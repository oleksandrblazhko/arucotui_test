
import argparse
import asyncio
import time
import functools
import itertools
import winsound # Import winsound for Windows-specific sound
import json
import os
import pygame.mixer

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
import numpy as np
import cv2

# --- Calibration Settings ---
is_calibrating = False
calibration_start_time = 0
calibration_duration = 3.0  # seconds
calibration_data = {}
table_zone = []
pixels_per_meter = 0

# --- Object Management ---
objects_data = {} # Dictionary to store object definitions from objects.json
control_marker_id = None
audio_base_dir = "audio" # Default audio directory
active_audio_file = None
audio_channel = None # To manage audio playback
last_proximity_time = 0 # For audio grace period
camera_prox_channels = {} # For camera proximity audio
camera_prox_last_seen = {} # For camera proximity grace period
calibrated_avg_boundary_z = 0.0 # To store the Z average from calibration
camera_distance_threshold = 0.0 # Global to store the calculated threshold
locked_object_state = None # To "lock" onto an object for proximity checks

# --- Global Constants ---
MARKER_TIMEOUT = 0.2  # seconds
AUDIO_GRACE_PERIOD = 0.5 # seconds

# --- Data Class for Markers ---
class Marker:
    def __init__(self, marker_id, tx, ty, tz, roll, pitch, yaw, corners):
        self.marker_id = marker_id
        self.update(tx, ty, tz, roll, pitch, yaw, corners)

    def update(self, tx, ty, tz, roll, pitch, yaw, corners):
        self.tx = tx
        self.ty = ty
        self.tz = tz
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.corners = np.array(corners, dtype=np.int32).reshape((4, 2))
        self.timestamp = time.time()

    def get_center(self):
        return np.mean(self.corners, axis=0).astype(int)

    def get_pos_3d(self):
        return np.array([self.tx, self.ty, self.tz])
    
    def get_pixel_width(self):
        """Calculates the average width of the marker in pixels."""
        d1 = np.linalg.norm(self.corners[0] - self.corners[1])
        d2 = np.linalg.norm(self.corners[2] - self.corners[3])
        return (d1 + d2) / 2

# --- Global Storage for Markers ---
markers = {}
BOUNDARY_IDS = {1, 2, 3, 5}

# --- Sound Functions ---
async def play_beep():
    # winsound.Beep is blocking, so run it in a separate thread
    # Frequency (Hz), Duration (ms)
    await asyncio.to_thread(winsound.Beep, 1000, 500)

async def play_calibration_beeps():
    """Plays three beeps for calibration feedback."""
    for _ in range(3):
        await asyncio.to_thread(winsound.Beep, 1500, 500)
        await asyncio.sleep(0.5)

def play_audio_file(filename):
    global active_audio_file, audio_channel
    if active_audio_file != filename:
        stop_audio_file() # Stop current sound if different
        try:
            # Assumes audio files are in a subdirectory like 'audio/'
            # Or adjust path as needed
            full_path = os.path.join(audio_base_dir, filename) 
            sound = pygame.mixer.Sound(full_path)
            audio_channel = sound.play(-1) # -1 means loop indefinitely
            active_audio_file = filename
        except pygame.error as e:
            print(f"Error playing audio file {full_path}: {e}")
            active_audio_file = None
        except FileNotFoundError:
            print(f"Error: Audio file not found at {full_path}")
            active_audio_file = None

def stop_audio_file():
    global active_audio_file, audio_channel
    if audio_channel and audio_channel.get_busy():
        audio_channel.stop()
    active_audio_file = None
    audio_channel = None

def stop_all_audio():
    global active_audio_file, audio_channel, camera_prox_channels
    # Stop the main audio channel
    if audio_channel and audio_channel.get_busy():
        audio_channel.stop()
    active_audio_file = None
    audio_channel = None

    # Stop all camera proximity channels
    for channel in camera_prox_channels.values():
        channel.stop()
    camera_prox_channels.clear()
    print("Stopped all audio channels.")

# --- OSC Message Handler (with scaling) ---
def marker_handler(address, *args, scale_x=1.0, scale_y=1.0):
    marker_id = args[0]
    tx, ty, tz = args[1:4]
    roll, pitch, yaw = args[4:7]
    raw_corners = np.array(args[7:], dtype=np.float32).reshape((4, 2))
    
    scaled_corners = (raw_corners * [scale_x, scale_y]).astype(np.int32)
    
    if marker_id in markers:
        markers[marker_id].update(tx, ty, tz, roll, pitch, yaw, scaled_corners)
    else:
        markers[marker_id] = Marker(marker_id, tx, ty, tz, roll, pitch, yaw, scaled_corners)

# --- Grid Drawing Function ---
def draw_table_grid(frame, table_zone, pixels_per_meter):
    if not table_zone or pixels_per_meter == 0:
        return

    inset_m = 0.005  # 5mm
    inset_px = inset_m * pixels_per_meter

    # 1. Get the perspective transform for the outer boundary
    src_pts = np.float32([[0, 0], [1, 0], [1, 1], [0, 1]])
    dst_pts = np.float32(table_zone)
    # M = cv2.getPerspectiveTransform(src_pts, dst_pts) # M is not used here

    # A simpler approximation for inset: shrink towards the centroid.
    centroid = np.mean(dst_pts, axis=0)
    inset_dst_pts = []
    for pt in dst_pts:
        vector = centroid - pt
        normalized_vector = vector / np.linalg.norm(vector)
        inset_dst_pts.append(pt + normalized_vector * inset_px)
    
    inset_dst_pts = np.array(inset_dst_pts, dtype=np.float32)

    # 2. Get the perspective transform for the inset grid
    grid_src_pts = np.float32([[0, 0], [8, 0], [8, 8], [0, 8]])
    grid_M = cv2.getPerspectiveTransform(grid_src_pts, inset_dst_pts)

    # 3. Draw the grid lines
    grid_color = (0, 255, 0)
    for i in range(1, 8):
        # Vertical lines
        line_src_v = np.float32([[[i, 0]], [[i, 8]]])
        line_dst_v = cv2.perspectiveTransform(line_src_v, grid_M)
        pt1_v = tuple(line_dst_v[0][0].astype(int))
        pt2_v = tuple(line_dst_v[1][0].astype(int))
        cv2.line(frame, pt1_v, pt2_v, grid_color, 1)

        # Horizontal lines
        line_src_h = np.float32([[[0, i]], [[8, i]]])
        line_dst_h = cv2.perspectiveTransform(line_src_h, grid_M)
        pt1_h = tuple(line_dst_h[0][0].astype(int))
        pt2_h = tuple(line_dst_h[1][0].astype(int))
        cv2.line(frame, pt1_h, pt2_h, grid_color, 1)


# --- Main Application Logic ---
async def main_loop(width, height, proximity_threshold, marker_size, no_text=False, no_proximity_check=False):
    global is_calibrating, calibration_start_time, calibration_data, table_zone, pixels_per_meter, active_audio_file, audio_channel, objects_data, control_marker_id, audio_base_dir, last_proximity_time, camera_prox_channels, camera_prox_last_seen, calibrated_avg_boundary_z, camera_distance_threshold, locked_object_state
    frame_counter = 0 # Initialize frame counter

    # Create the frame once, outside the loop
    frame = np.full((height, width, 3), 255, dtype=np.uint8)

    while True:
        # Clear the frame instead of reallocating
        frame[:] = 255
        current_time = time.time()

        # --- Prune old markers ---
        for marker_id, marker in list(markers.items()):
            if current_time - marker.timestamp > MARKER_TIMEOUT:
                del markers[marker_id]

        # --- Calibration Logic ---
        if is_calibrating:
            elapsed_time = current_time - calibration_start_time
            if elapsed_time <= calibration_duration:
                # Collect data for boundary markers
                for marker_id in BOUNDARY_IDS:
                    if marker_id in markers:
                        if marker_id not in calibration_data:
                            calibration_data[marker_id] = {'centers': [], 'widths': [], 'zs': []}
                        calibration_data[marker_id]['centers'].append(markers[marker_id].get_center())
                        calibration_data[marker_id]['widths'].append(markers[marker_id].get_pixel_width())
                        calibration_data[marker_id]['zs'].append(markers[marker_id].tz)
            else:
                # Finish calibration
                is_calibrating = False
                print("Calibration finished. Calculating average positions...")
                
                temp_zone = []
                visible_marker_widths = []
                visible_marker_zs = []
                sorted_ids = sorted(list(BOUNDARY_IDS))

                for marker_id in sorted_ids:
                    if marker_id in calibration_data and len(calibration_data[marker_id]['centers']) > 0:
                        avg_point = np.mean(calibration_data[marker_id]['centers'], axis=0).astype(int)
                        temp_zone.append(avg_point)
                        visible_marker_widths.extend(calibration_data[marker_id]['widths'])
                        visible_marker_zs.extend(calibration_data[marker_id]['zs'])
                    else:
                        print(f"Warning: No data collected for boundary marker {marker_id}.")
                
                if len(temp_zone) == 4:
                    table_zone = temp_zone
                    # Calculate and store calibrated average Z
                    if visible_marker_zs:
                        calibrated_avg_boundary_z = np.mean(visible_marker_zs)
                        print(f"Calibration successful. Calibrated Avg Boundary Z: {calibrated_avg_boundary_z:.4f}m")
                    else:
                        print("Warning: Could not calculate calibrated average boundary Z.")

                    # Calculate pixels_per_meter
                    if visible_marker_widths and marker_size > 0:
                        avg_pixel_width = np.mean(visible_marker_widths)
                        pixels_per_meter = avg_pixel_width / marker_size
                        print(f"Calibration successful. Pixels/meter: {pixels_per_meter:.2f}")
                    else:
                         print("Warning: Could not calculate pixels/meter ratio.")
                else:
                    print("Error: Could not define table zone. Not all boundary markers were visible.")
                
                calibration_data = {} # Clear data for next time
        
        # --- Camera Proximity Audio Logic (with Grace Period) ---
        if calibrated_avg_boundary_z > 0:
            camera_distance_threshold = calibrated_avg_boundary_z / 2.0

            # Step 1: Identify currently close markers and update their timestamps
            for marker_id, marker in markers.items():
                if marker_id in objects_data and objects_data[marker_id].get("obj_type") != "control":
                    if marker.tz < camera_distance_threshold:
                        # This marker is close, so update its "last seen close" time
                        camera_prox_last_seen[marker_id] = current_time
                        # If it's not already playing, start it
                        if marker_id not in camera_prox_channels:
                            obj_def = objects_data[marker_id]
                            if obj_def.get("audio_name"):
                                try:
                                    full_path = os.path.join(audio_base_dir, obj_def["audio_name"])
                                    sound = pygame.mixer.Sound(full_path)
                                    channel = pygame.mixer.find_channel(True)
                                    channel.play(sound, -1)
                                    camera_prox_channels[marker_id] = channel
                                except Exception as e:
                                    print(f"Error playing camera proximity sound for {marker_id}: {e}")
            
            # Step 2: Stop sounds for markers that haven't been close for a while
            for marker_id, channel in list(camera_prox_channels.items()):
                time_since_last_close = current_time - camera_prox_last_seen.get(marker_id, 0)
                if time_since_last_close > AUDIO_GRACE_PERIOD:
                    channel.stop()
                    del camera_prox_channels[marker_id]
                    if marker_id in camera_prox_last_seen:
                        del camera_prox_last_seen[marker_id]
        
        # --- Control Marker Proximity Audio (with Lock-on & Smoothing) ---
        control_marker = markers.get(control_marker_id)
        
        closest_dist_for_display = float('inf')
        
        # This block only runs if the control marker is VISIBLE in the current frame
        if not no_proximity_check and control_marker:
            # --- Step 1: Check and maintain the existing lock ---
            if locked_object_state:
                raw_distance = np.linalg.norm(control_marker.get_pos_3d() - locked_object_state["saved_pos"])
                closest_dist_for_display = raw_distance

                # --- Smoothing Logic ---
                if "recent_distances" not in locked_object_state:
                    locked_object_state["recent_distances"] = []
                
                distances = locked_object_state["recent_distances"]
                distances.append(raw_distance)
                if len(distances) > 5: # Keep last 5 frames
                    distances.pop(0)
                smoothed_distance = np.mean(distances)
                # --- End Smoothing ---

                break_threshold = proximity_threshold * 1.5 # Hysteresis: 50% larger threshold

                # If the smoothed distance is too far, break the lock
                if smoothed_distance >= break_threshold:
                    locked_object_state = None
                # Otherwise, maintain the lock and update the timer
                else:
                    play_audio_file(locked_object_state["audio_name"])
                    last_proximity_time = current_time
            
            # --- Step 2: If no lock, search for a new one ---
            else:
                for obj_def in objects_data.values():
                    obj_marker_id = obj_def["marker_id"]
                    if obj_def.get("obj_type") != "control" and obj_marker_id in markers:
                        obj_marker = markers[obj_marker_id]
                        distance = np.linalg.norm(control_marker.get_pos_3d() - obj_marker.get_pos_3d())

                        # If we find a new close object, lock it
                        if distance < proximity_threshold:
                            locked_object_state = {
                                "marker_id": obj_marker_id,
                                "saved_pos": obj_marker.get_pos_3d(),
                                "audio_name": obj_def["audio_name"],
                                "recent_distances": [distance] # Initialize with the first distance
                            }
                            play_audio_file(locked_object_state["audio_name"])
                            last_proximity_time = current_time
                            closest_dist_for_display = distance
                            break 
            
            # --- Step 3: Update distance display for any nearby object (visual only) ---
            if not locked_object_state:
                for obj_def in objects_data.values():
                    if obj_def.get("obj_type") != "control" and obj_def["marker_id"] in markers:
                        obj_marker = markers[obj_def["marker_id"]]
                        distance = np.linalg.norm(control_marker.get_pos_3d() - obj_marker.get_pos_3d())
                        if distance < (1.5 * proximity_threshold):
                            if distance < closest_dist_for_display:
                                closest_dist_for_display = distance
        
        # --- Handle audio stop grace period ---
        time_since_last_event = current_time - last_proximity_time
        if active_audio_file and time_since_last_event > AUDIO_GRACE_PERIOD:
            # This handles both breaking a lock and the control marker disappearing.
            if locked_object_state:
                locked_object_state = None
            stop_audio_file()

        # --- Visualization ---
        if table_zone:
            # Draw the fixed calibrated zone
            pts = np.array(table_zone, dtype=np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            # Draw the grid
            draw_table_grid(frame, table_zone, pixels_per_meter)
        else:
            # Draw live boundary
            boundary_markers_viz = {mid: markers[mid] for mid in BOUNDARY_IDS if mid in markers}
            if len(boundary_markers_viz) == 4:
                sorted_ids = sorted(list(boundary_markers_viz.keys()))
                p0 = boundary_markers_viz[sorted_ids[0]].get_center()
                p1 = boundary_markers_viz[sorted_ids[1]].get_center()
                p2 = boundary_markers_viz[sorted_ids[2]].get_center()
                p3 = boundary_markers_viz[sorted_ids[3]].get_center()
                
                cv2.line(frame, tuple(p0), tuple(p1), (0, 255, 0), 2)
                cv2.line(frame, tuple(p1), tuple(p2), (0, 255, 0), 2)
                cv2.line(frame, tuple(p2), tuple(p3), (0, 255, 0), 2)
                cv2.line(frame, tuple(p3), tuple(p0), (0, 255, 0), 2)

        for marker_id, marker in list(markers.items()):
            cv2.polylines(frame, [marker.corners], isClosed=True, color=(255, 0, 0), thickness=2)
            
            if not no_text:
                text_id = f"id={marker_id}"
                text_coords = f"({marker.tx*1000:.0f},{marker.ty*1000:.0f},{marker.tz*1000:.0f})"
                
                text_pos = marker.corners[0]
                cv2.putText(frame, text_id, (text_pos[0], text_pos[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 0), 1)
                cv2.putText(frame, text_coords, (text_pos[0], text_pos[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 0), 1)

        # --- Display Proximity Distance for Control Marker (Task 19) ---
        if control_marker and closest_dist_for_display != float('inf'):
            display_text = f"dist={closest_dist_for_display*1000:.0f}mm"
            text_pos = control_marker.get_center()
            # Offset the text slightly to avoid overlapping with marker ID/coords
            cv2.putText(frame, display_text, (text_pos[0] + 20, text_pos[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # --- UI Text ---
        cv2.putText(frame, "0 - calibration", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        if calibrated_avg_boundary_z > 0:
             cv2.putText(frame, f"Cam Thresh: {camera_distance_threshold*1000:.0f}mm", (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        cv2.imshow("Client", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('0'):
            if not is_calibrating:
                print("Starting calibration...")
                is_calibrating = True
                calibration_start_time = time.time()
                calibration_data = {}
                asyncio.create_task(play_calibration_beeps())
            
        await asyncio.sleep(1/60)

    cv2.destroyAllWindows()
    stop_all_audio() # Ensure audio stops on exit

async def init_main(args):
    global objects_data, control_marker_id, audio_channel, audio_base_dir
    
    # Initialize Pygame Mixer
    pygame.mixer.init()
    pygame.mixer.set_num_channels(32) # Increase channels for multiple proximity sounds
    audio_channel = pygame.mixer.Channel(0) # Use channel 0 for our audio

    # Load objects data from JSON
    try:
        script_dir = os.path.dirname(__file__)
        objects_json_path = os.path.join(script_dir, "objects.json")
        with open(objects_json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        audio_base_dir = config.get("audio_directory", "audio") # Get audio directory, default to "audio"
        
        raw_objects = config.get("objects", []) # Get the list of objects
        for obj in raw_objects:
            objects_data[obj["marker_id"]] = obj
            if obj.get("obj_type") == "control":
                control_marker_id = obj["marker_id"]
        print(f"Loaded {len(objects_data)} objects from objects.json. Control marker ID: {control_marker_id}. Audio directory: {audio_base_dir}")

    except FileNotFoundError:
        print("Error: objects.json not found in the client directory.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode objects.json. Check for valid JSON format.")
        return
    
    scale_x = args.width / args.source_width
    scale_y = args.height / args.source_height
    
    proximity_threshold = args.marker_size + args.proximity_gap

    handler_with_scaling = functools.partial(marker_handler, scale_x=scale_x, scale_y=scale_y)
    dispatcher = Dispatcher()
    dispatcher.map("/marker", handler_with_scaling)
    server = AsyncIOOSCUDPServer((args.ip, args.port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()
    try:
        await main_loop(args.width, args.height, proximity_threshold, args.marker_size, args.no_text, args.no_proximity_check)
    finally:
        transport.close()
        pygame.mixer.quit() # Quit mixer on exit

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=9000, help="The port to listen on")
    parser.add_argument("--width", type=int, default=1280, help="Client window width")
    parser.add_argument("--height", type=int, default=720, help="Client window height")
    parser.add_argument("--source-width", type=int, default=640, help="Source (server) camera width")
    parser.add_argument("--source-height", type=int, default=480, help="Source (server) camera height")
    parser.add_argument("--marker-size", type=float, default=0.012, help="Physical size of the markers in meters")
    parser.add_argument("--proximity-gap", type=float, default=0.015, help="Desired visual gap between markers for proximity alert (in meters)")
    parser.add_argument("--no-text", action="store_true", help="Disable drawing text for each marker to improve performance")
    parser.add_argument("--no-proximity-check", action="store_true", help="Disable proximity check to improve performance")
    args = parser.parse_args()

    try:
        asyncio.run(init_main(args))
    except KeyboardInterrupt:
        pass
