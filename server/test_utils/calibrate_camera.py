import cv2
import numpy as np
import json
import argparse
import time
from math import sqrt

# ---------- Configuration ----------
CHESSBOARD_SIZE = (9, 6)
SQUARE_SIZE = 0.025
SAMPLES_NEEDED = 20
CALIBRATION_FILE = "camera_ext.json"

CAPTURE_DELAY = 2.0
MIN_CENTER_SHIFT = 40.0  # pixels


def distance(p1, p2):
    return sqrt((p1[0] - p2[0]) ** 2 +
                (p1[1] - p2[1]) ** 2)


def main():

    parser = argparse.ArgumentParser(
        description="Camera Calibration using Chessboard"
    )

    parser.add_argument(
        "--cam",
        type=int,
        default=0,
        help="Camera index"
    )

    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Capture width"
    )

    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Capture height"
    )

    parser.add_argument(
        "--file",
        type=str,
        default=CALIBRATION_FILE,
        help="Output calibration file"
    )

    args = parser.parse_args()

    cap = cv2.VideoCapture(args.cam, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"Cannot open camera {args.cam}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    # ---------- Object points ----------

    objp = np.zeros(
        (CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3),
        np.float32
    )

    objp[:, :2] = np.mgrid[
        0:CHESSBOARD_SIZE[0],
        0:CHESSBOARD_SIZE[1]
    ].T.reshape(-1, 2)

    objp *= SQUARE_SIZE

    objpoints = []
    imgpoints = []

    samples_collected = 0
    last_capture_time = 0

    last_center = None

    criteria = (
        cv2.TERM_CRITERIA_EPS +
        cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001
    )

    print("\n=== Camera Calibration ===")
    print(f"Chessboard: {CHESSBOARD_SIZE[0]}x{CHESSBOARD_SIZE[1]}")
    print(f"Need {SAMPLES_NEEDED} samples")
    print("Move chessboard around the image")
    print("Press q to quit\n")

    image_size = None

    while samples_collected < SAMPLES_NEEDED:

        ok, frame = cap.read()

        if not ok:
            print("Frame capture error")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        image_size = gray.shape[::-1]

        found = False
        status_text = "No chessboard"

        # ---------- New detector ----------
        try:
            corners = cv2.findChessboardCornersSB(
                gray,
                CHESSBOARD_SIZE
            )

            if isinstance(corners, tuple):
                found, corners = corners
            else:
                found = corners is not None

        except Exception:
            found, corners = cv2.findChessboardCorners(
                gray,
                CHESSBOARD_SIZE
            )

        if found:

            cv2.drawChessboardCorners(
                frame,
                CHESSBOARD_SIZE,
                corners,
                found
            )

            center_x = np.mean(corners[:, 0, 0])
            center_y = np.mean(corners[:, 0, 1])

            current_center = (center_x, center_y)

            current_time = time.time()

            allow_capture = True

            if last_center is not None:

                shift = distance(
                    current_center,
                    last_center
                )

                if shift < MIN_CENTER_SHIFT:
                    allow_capture = False
                    status_text = (
                        f"Move board more ({shift:.1f}px)"
                    )

            if current_time - last_capture_time < CAPTURE_DELAY:
                allow_capture = False
                status_text = "Waiting..."

            if allow_capture:

                corners2 = cv2.cornerSubPix(
                    gray,
                    corners,
                    (11, 11),
                    (-1, -1),
                    criteria
                )

                objpoints.append(objp.copy())
                imgpoints.append(corners2)

                samples_collected += 1
                last_capture_time = current_time
                last_center = current_center

                status_text = (
                    f"Captured {samples_collected}/"
                    f"{SAMPLES_NEEDED}"
                )

                print(status_text)

        # ---------- UI ----------

        cv2.putText(
            frame,
            f"Samples: {samples_collected}/{SAMPLES_NEEDED}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            status_text,
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        cv2.imshow("Calibration", frame)

        key = cv2.waitKey(1)

        if key & 0xFF == ord("q"):
            print("Cancelled")
            cap.release()
            cv2.destroyAllWindows()
            return

    cap.release()
    cv2.destroyAllWindows()

    if len(objpoints) < 10:
        print("Too few samples")
        return

    # ---------- Calibration ----------

    print("\nPerforming calibration...")

    try:

        rms, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints,
            imgpoints,
            image_size,
            None,
            None
        )

        print(f"\nRMS Error = {rms:.6f}")

        data = {
            "mtx": mtx.tolist(),
            "dist": dist.tolist()
        }

        with open(args.file, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Saved: {args.file}")

        # ---------- Reprojection Error ----------

        total_error = 0

        for i in range(len(objpoints)):

            projected, _ = cv2.projectPoints(
                objpoints[i],
                rvecs[i],
                tvecs[i],
                mtx,
                dist
            )

            error = (
                cv2.norm(
                    imgpoints[i],
                    projected,
                    cv2.NORM_L2
                )
                / len(projected)
            )

            total_error += error

        reprojection_error = (
            total_error / len(objpoints)
        )

        print(
            f"Mean reprojection error = "
            f"{reprojection_error:.6f}"
        )

        if reprojection_error < 0.3:
            print("Excellent calibration")
        elif reprojection_error < 0.7:
            print("Good calibration")
        elif reprojection_error < 1.0:
            print("Acceptable calibration")
        else:
            print("Poor calibration, repeat capture")

        print("\nCamera matrix:")
        print(mtx)

        print("\nDistortion coefficients:")
        print(dist)

    except Exception as e:
        print("Calibration error:")
        print(e)


if __name__ == "__main__":
    main()
