
import argparse
import asyncio
import time
import functools
import itertools
import winsound # Import winsound for Windows-specific sound

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
import numpy as np
import cv2

# --- Proximity Alert Settings ---
SOUND_COOLDOWN = 1.0  # seconds
last_beep_time = 0

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

# --- Global Storage for Markers ---
markers = {}
BOUNDARY_IDS = {1, 2, 3, 5}
MARKER_TIMEOUT = 0.2  # seconds

# --- Sound Function ---
async def play_beep():
    # winsound.Beep is blocking, so run it in a separate thread
    # Frequency (Hz), Duration (ms)
    await asyncio.to_thread(winsound.Beep, 1000, 500) 

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

# --- Main Application Logic ---
async def main_loop(width, height, proximity_threshold, no_text=False, no_proximity_check=False):
    global last_beep_time
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

        # --- Proximity Check for Internal Markers (optimized) ---
        if not no_proximity_check:
            if frame_counter % 10 == 0: # Only check every 10th frame
                internal_markers = [m for m in markers.values() if m.marker_id not in BOUNDARY_IDS]
                if len(internal_markers) >= 2:
                    for marker1, marker2 in itertools.combinations(internal_markers, 2):
                        distance = np.linalg.norm(marker1.get_pos_3d() - marker2.get_pos_3d())
                        if distance < proximity_threshold:
                            if current_time - last_beep_time > SOUND_COOLDOWN:
                                last_beep_time = current_time
                                asyncio.create_task(play_beep())
                            break # Only beep once per frame
        
        frame_counter += 1 # Increment frame counter

        # --- Visualization ---
        boundary_markers = {mid: markers[mid] for mid in BOUNDARY_IDS if mid in markers}
        if len(boundary_markers) == 4:
            # Sort the boundary IDs to ensure consistent drawing order
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
                text_id = f"id: {marker_id}"
                text_coords = f"{marker.tx*1000:.0f}, {marker.ty*1000:.0f}, {marker.tz*1000:.0f})"
                
                text_pos = marker.corners[0]
                cv2.putText(frame, text_id, (text_pos[0], text_pos[1] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 2)
                cv2.putText(frame, text_coords, (text_pos[0], text_pos[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 2)

        cv2.imshow("Client", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        await asyncio.sleep(1/60)

    cv2.destroyAllWindows()

async def init_main(args):
    scale_x = args.width / args.source_width
    scale_y = args.height / args.source_height
    
    proximity_threshold = args.marker_size + args.proximity_gap

    handler_with_scaling = functools.partial(marker_handler, scale_x=scale_x, scale_y=scale_y)
    dispatcher = Dispatcher()
    dispatcher.map("/marker", handler_with_scaling)
    server = AsyncIOOSCUDPServer((args.ip, args.port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()
    try:
        await main_loop(args.width, args.height, proximity_threshold, args.no_text, args.no_proximity_check)
    finally:
        transport.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=9000, help="The port to listen on")
    parser.add_argument("--width", type=int, default=1280, help="Client window width")
    parser.add_argument("--height", type=int, default=720, help="Client window height")
    parser.add_argument("--source-width", type=int, default=640, help="Source (server) camera width")
    parser.add_argument("--source-height", type=int, default=480, help="Source (server) camera height")
    parser.add_argument("--marker-size", type=float, default=0.012, help="Physical size of the markers in meters")
    parser.add_argument("--proximity-gap", type=float, default=0.007, help="Desired visual gap between markers for proximity alert (in meters)")
    parser.add_argument("--no-text", action="store_true", help="Disable drawing text for each marker to improve performance")
    parser.add_argument("--no-proximity-check", action="store_true", help="Disable proximity check to improve performance")
    args = parser.parse_args()

    try:
        asyncio.run(init_main(args))
    except KeyboardInterrupt:
        pass
