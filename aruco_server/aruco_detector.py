# Створення детектора маркерів.

import cv2

ARUCO_DICTS = {
    0: cv2.aruco.DICT_ARUCO_ORIGINAL,
    1: cv2.aruco.DICT_4X4_1000,
    2: cv2.aruco.DICT_APRILTAG_36h11,
}

def create_detector(pattern):

    dictionary = cv2.aruco.getPredefinedDictionary(
        ARUCO_DICTS.get(
            pattern,
            cv2.aruco.DICT_ARUCO_ORIGINAL
        )
    )

    params = cv2.aruco.DetectorParameters()

    return cv2.aruco.ArucoDetector(
        dictionary,
        params
    )

def detect_markers(detector, frame):

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    return detector.detectMarkers(gray)
