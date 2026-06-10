# Відображення.

import cv2

def draw_markers(
    frame,
    corners,
    ids
):

    if ids is not None:

        cv2.aruco.drawDetectedMarkers(
            frame,
            corners,
            ids
        )

def draw_axes(frame, camera_matrix, dist_coeffs, rvecs, tvecs, marker_size):
    if rvecs is not None:
        for i in range(len(rvecs)):
            cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvecs[i], tvecs[i], marker_size * 0.5)


def draw_fps(frame, fps):

    cv2.putText(
        frame,
        f"FPS {fps:.1f}",
        (20,40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0,255,0),
        2
    )
    