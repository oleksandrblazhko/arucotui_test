
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
            print(f"Playing audio: {filename}")
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
        print(f"Stopped audio: {active_audio_file}")
    active_audio_file = None
    audio_channel = None

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
    global is_calibrating, calibration_start_time, calibration_data, table_zone, pixels_per_meter, active_audio_file, audio_channel, objects_data, control_marker_id, audio_base_dir, last_proximity_time
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
                            calibration_data[marker_id] = {'centers': [], 'widths': []}
                        calibration_data[marker_id]['centers'].append(markers[marker_id].get_center())
                        calibration_data[marker_id]['widths'].append(markers[marker_id].get_pixel_width())
            else:
                # Finish calibration
                is_calibrating = False
                print("Calibration finished. Calculating average positions...")
                
                temp_zone = []
                visible_marker_widths = []
                sorted_ids = sorted(list(BOUNDARY_IDS))

                for marker_id in sorted_ids:
                    if marker_id in calibration_data and len(calibration_data[marker_id]['centers']) > 0:
                        avg_point = np.mean(calibration_data[marker_id]['centers'], axis=0).astype(int)
                        temp_zone.append(avg_point)
                        visible_marker_widths.extend(calibration_data[marker_id]['widths'])
                    else:
                        print(f"Warning: No data collected for boundary marker {marker_id}.")
                
                if len(temp_zone) == 4:
                    table_zone = temp_zone
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

        # --- New Proximity-based Audio Playback ---
        control_marker_present = False
        control_marker = None
        if control_marker_id and control_marker_id in markers:
            control_marker_present = True
            control_marker = markers[control_marker_id]

        found_proximate_object_for_audio = False
        audio_to_play = None
        
        closest_dist_for_display = float('inf')
        actual_dist_for_display = 0.0

        if control_marker_present and control_marker:
            # Determine which audio to play (first object within proximity_threshold)
            for obj_def in objects_data.values():
                if obj_def.get("obj_type") != "control" and obj_def["marker_id"] in markers:
                    obj_marker = markers[obj_def["marker_id"]]
                    distance = np.linalg.norm(control_marker.get_pos_3d() - obj_marker.get_pos_3d())
                    
                    if distance < proximity_threshold:
                        found_proximate_object_for_audio = True
                        last_proximity_time = current_time
                        if obj_def["audio_name"]:
                            audio_to_play = obj_def["audio_name"]
                        break # Play audio for the first object found within threshold

            if audio_to_play:
                await asyncio.to_thread(play_audio_file, audio_to_play)
            elif current_time - last_proximity_time > AUDIO_GRACE_PERIOD:
                if active_audio_file:
                    await asyncio.to_thread(stop_audio_file)
            
            # Determine which distance to display (closest object within 2 * proximity_threshold)
            for obj_def in objects_data.values():
                if obj_def.get("obj_type") != "control" and obj_def["marker_id"] in markers:
                    obj_marker = markers[obj_def["marker_id"]]
                    distance = np.linalg.norm(control_marker.get_pos_3d() - obj_marker.get_pos_3d())
                    
                    if distance < (1.5 * proximity_threshold):
                        if distance < closest_dist_for_display:
                            closest_dist_for_display = distance
                            actual_dist_for_display = distance
        else: # No control marker present
            if current_time - last_proximity_time > AUDIO_GRACE_PERIOD:
                await asyncio.to_thread(stop_audio_file)
        
        frame_counter += 1 # Increment frame counter

        # --- Visualization ---
        if table_zone:
            # Draw the fixed calibrated zone
            pts = np.array(table_zone, dtype=np.int32)
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            # Draw the grid
            draw_table_grid(frame, table_zone, pixels_per_meter)
        else:
            # Draw live boundary
            boundary_markers = {mid: markers[mid] for mid in BOUNDARY_IDS if mid in markers}
            if len(boundary_markers) == 4:
                sorted_ids = sorted(list(boundary_markers.keys()))
                p0 = boundary_markers[sorted_ids[0]].get_center()
                p1 = boundary_markers[sorted_ids[1]].get_center()
                p2 = boundary_markers[sorted_ids[2]].get_center()
                p3 = boundary_markers[sorted_ids[3]].get_center()
                
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
        if control_marker_present and control_marker and closest_dist_for_display != float('inf'):
            display_text = f"dist={closest_dist_for_display*1000:.0f}mm"
            text_pos = control_marker.get_center()
            # Offset the text slightly to avoid overlapping with marker ID/coords
            cv2.putText(frame, display_text, (text_pos[0] + 20, text_pos[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1) # Red color

        # --- UI Text ---
        cv2.putText(frame, "0 - calibration", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

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
    stop_audio_file() # Ensure audio stops on exit

async def init_main(args):
    global objects_data, control_marker_id, audio_channel, audio_base_dir
    
    # Initialize Pygame Mixer
    pygame.mixer.init()
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
