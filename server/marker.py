
import cv2
import numpy as np
import time
import argparse
import json
import os
from pythonosc import udp_client

# -------------------------
# OSC (same as old system)
# -------------------------
client = udp_client.SimpleUDPClient("127.0.0.1", 9000)

# -------------------------
# CLI
# -------------------------
parser = argparse.ArgumentParser()

parser.add_argument("--cam", type=int, default=0)
parser.add_argument("--width", type=int, default=640)
parser.add_argument("--height", type=int, default=480)
parser.add_argument("--pattern", type=int, default=0, help="0 - DICT_ARUCO_ORIGINAL(5x5), 1 - DICT_4X4_1000")
parser.add_argument("--size", type=float, default=0.015, help="ArUco marker size in meters (default: 0.015 for 15mm)")
parser.add_argument("--flip", action="store_true", help="Flip the camera feed both horizontally and vertically")
parser.add_argument("--win", action="store_true", default=True, help="Use Windows-specific camera backend (DSHOW)")

args = parser.parse_args()

# -------------------------
# Camera Calibration
# -------------------------
if os.path.exists('camera_ext.json'):
    with open('camera_ext.json', 'r') as json_file:
        camera_data = json.load(json_file)
    camera_matrix = np.array(camera_data["mtx"])
    dist_coeffs = np.array(camera_data["dist"])
    print("INFO: Camera calibration loaded from camera_ext.json")
else:
    print("WARNING: camera_ext.json not found. Using default identity matrix for camera. Z-depth will be incorrect.")
    camera_matrix = np.eye(3)
    dist_coeffs = np.zeros(5)

# -------------------------
# Camera Setup
# -------------------------
backend = cv2.CAP_DSHOW if args.win else cv2.CAP_ANY
cap = cv2.VideoCapture(args.cam, backend)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

if not cap.isOpened():
    raise RuntimeError("Camera not opened")

# -------------------------
# ArUco Dictionary
# -------------------------
ARUCO_DICTS = {
    0: cv2.aruco.DICT_ARUCO_ORIGINAL,
    1: cv2.aruco.DICT_4X4_1000,
    2: cv2.aruco.DICT_APRILTAG_36h11,
}
aruco_dict = cv2.aruco.getPredefinedDictionary(
    ARUCO_DICTS.get(args.pattern, cv2.aruco.DICT_ARUCO_ORIGINAL)
)
params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, params)

# -------------------------
# Helper: rotation matrix → euler
# -------------------------
def rmat_to_euler(R):
    sy = np.sqrt(R[0,0]**2 + R[1,0]**2)
    singular = sy < 1e-6
    if not singular:
        roll  = np.arctan2(R[2,1], R[2,2])
        pitch = np.arctan2(-R[2,0], sy)
        yaw   = np.arctan2(R[1,0], R[0,0])
    else:
        roll = np.arctan2(-R[1,2], R[1,1])
        pitch = np.arctan2(-R[2,0], sy)
        yaw = 0
    return roll, pitch, yaw

# -------------------------
# MAIN LOOP
# -------------------------
prev = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Apply flip if requested
    if args.flip:
        frame = cv2.flip(frame, -1)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    now = time.time()
    fps = 1.0 / (now - prev + 1e-6)
    prev = now

    if ids is not None:
        # Use the loaded calibration data for pose estimation
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            corners, args.size, camera_matrix, dist_coeffs
        )

        for i in range(len(ids)):
            c = corners[i][0]
            rvec = rvecs[i]
            tvec = tvecs[i]

            R, _ = cv2.Rodrigues(rvec)
            roll, pitch, yaw = rmat_to_euler(R)
            tx, ty, tz = tvec[0]

            # -------------------------
            # OSC FORMAT
            # -------------------------
            msg = [
                int(ids[i][0]),
                float(tx), float(ty), float(tz),
                float(roll), float(pitch), float(yaw),
                int(c[0][0]), int(c[0][1]),
                int(c[1][0]), int(c[1][1]),
                int(c[2][0]), int(c[2][1]),
                int(c[3][0]), int(c[3][1]),
            ]
            client.send_message("/marker", msg)

        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        # Draw axes for each marker
        for i in range(len(ids)):
            cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], args.size * 0.5)

    cv2.putText(frame, f"FPS {fps:.1f}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.imshow("server", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()