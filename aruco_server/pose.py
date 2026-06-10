# Оцінка поз паркерів та кутів Ейлера.

import cv2
import numpy as np

def rmat_to_euler(R):

    sy = np.sqrt(
        R[0,0]**2 +
        R[1,0]**2
    )

    singular = sy < 1e-6

    if not singular:

        roll = np.arctan2(
            R[2,1],
            R[2,2]
        )

        pitch = np.arctan2(
            -R[2,0],
            sy
        )

        yaw = np.arctan2(
            R[1,0],
            R[0,0]
        )

    else:

        roll = np.arctan2(
            -R[1,2],
            R[1,1]
        )

        pitch = np.arctan2(
            -R[2,0],
            sy
        )

        yaw = 0

    return roll, pitch, yaw


def estimate_pose(
    corners,
    marker_size,
    camera_matrix,
    dist_coeffs
):

    return cv2.aruco.estimatePoseSingleMarkers(
        corners,
        marker_size,
        camera_matrix,
        dist_coeffs
    )
