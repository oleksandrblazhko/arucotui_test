# Завантаження результатів калібрування камери.

import json
import os
import numpy as np

def load_camera_calibration(filename="camera_ext.json"):

    if os.path.exists(filename):

        with open(filename, "r") as f:
            data = json.load(f)

        return (
            np.array(data["mtx"]),
            np.array(data["dist"])
        )

    print("WARNING: calibration not found")

    return np.eye(3), np.zeros(5)
