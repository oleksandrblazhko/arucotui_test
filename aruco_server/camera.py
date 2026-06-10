# Робота з камерою.

import cv2

def create_camera(cam_id, width, height, use_windows_backend):

    backend = (
        cv2.CAP_DSHOW
        if use_windows_backend
        else cv2.CAP_ANY
    )

    cap = cv2.VideoCapture(cam_id, backend)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        raise RuntimeError("Camera not opened")

    return cap
