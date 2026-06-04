import cv2
import numpy as np
import time
import argparse
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
parser.add_argument("--pattern", type=int, default=0)

# IMPORTANT: Windows default ON (as old system expected)
parser.add_argument("--win", action="store_true", default=True)

args = parser.parse_args()

backend = cv2.CAP_DSHOW if args.win else cv2.CAP_ANY
cap = cv2.VideoCapture(args.cam, backend)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

if not cap.isOpened():
    raise RuntimeError("Camera not opened")

# -------------------------
# Dictionary (same as old system)
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
# helper: rotation matrix → euler
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

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    corners, ids, _ = detector.detectMarkers(gray)

    now = time.time()
    fps = 1.0 / (now - prev + 1e-6)
    prev = now

    if ids is not None:

        for i in range(len(ids)):

            c = corners[i][0]

            # -------------------------
            # POSE estimation (OLD STYLE)
            # -------------------------
            rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners[i], 0.05,
                np.eye(3), np.zeros(5)
            )

            R, _ = cv2.Rodrigues(rvec)

            roll, pitch, yaw = rmat_to_euler(R)

            tx, ty, tz = tvec[0][0]

            # -------------------------
            # OSC FORMAT (CRITICAL FIX)
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

    cv2.putText(frame, f"FPS {fps:.1f}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    cv2.imshow("server", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()