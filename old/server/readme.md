# **ArUco-TUI Server v25.1**

**Author:** Rong-Hao Liang (TU Eindhoven)
**Email:** r.liang@tue.nl

This is a high-performance Python server for detecting ArUco and AprilTag markers using a webcam. It captures video using a multithreaded approach, performs camera undistortion, detects markers, estimates their 6D pose (position and rotation), and sends this data over OSC (Open Sound Control).

It features a user interface in the OpenCV window, allowing for real-time control over detection parameters and settings.

## Features

* **Multithreaded Camera Reading**: Uses a separate thread for camera capture to ensure high FPS and non-blocking reads.
* **Real-time Detection**: Detects and identifies ArUco and AprilTag markers in real-time.
* **6D Pose Estimation**: Calculates the translation ($tx, ty, tz$) and rotation ($roll, pitch, yaw$) of each marker relative to the camera.
* **OSC Output**: Broadcasts marker data over OSC for easy integration with software like TouchDesigner, Unity, Processing, etc..
* **Camera Calibration**: Uses camera calibration data from a JSON file for accurate undistortion and pose estimation.
* **Dynamic Controls**: Allows runtime switching of marker dictionaries, marker size, and toggling of key features.

## Installation

1.  Clone this repository.
2.  Install the required Python libraries. 

    ```bash
    pip install -r requirements.txt
    ```
    * opencv-contrib-python==4.6.0.66 # Specific OpenCV Computer Vision library that includes ArUco marker detection
    * python-osc # OSC (open-sound-communication) protocol for data exchange between Python software and other software
    * numpy==1.23 # Specific NumPy library for ArUco markers
3.  **Camera Calibration**: You MUST calibrate your camera to ensure accurate marker detection. A script is provided to automate this process.

    *   **Prerequisites**: You need a printed chessboard pattern. The script is configured to find a pattern with **9 horizontal and 6 vertical internal corners**.
        *   When using an online generator (like `https://calib.io/pages/camera-calibration-pattern-generator`), you must specify the **number of squares**, which should be **10 squares wide by 7 squares high**.
        *   Example settings for a generator:
            *   **Target Type:** `Checkerboard`
            *   **Columns (width):** `10`
            *   **Rows (height):** `7`
            *   **Checker Width:** A size that is easy for your camera to see (e.g., `15mm` or `20mm`).
        *   Print the pattern on a flat, non-reflective surface for the best results.

    *   **Run the calibration script**:
        ```bash
        python calibrate_camera.py
        ```
    *   **Follow the instructions**:
        1.  A window will appear showing your camera feed.
        2.  Show the printed chessboard to the camera. Hold it at different angles and distances.
        3.  The script will automatically collect samples when it clearly sees the chessboard.
        4.  Once it has enough samples, it will calculate the calibration data and save it to `camera_ext.json`.

    This will generate the `camera_ext.json` file required by the main `marker.py` script. The file contains the camera's intrinsic matrix (`mtx`) and distortion coefficients (`dist`). If you want to use a different camera, you can re-run the script and specify the camera index:
    ```bash
    python calibrate_camera.py --cam 1
    ```

## Usage

Run the script from your terminal.

```bash
python marker.py [ARGUMENTS]
```

### **Command-line Arguments**

| Argument | Description | Default |
| :---- | :---- | :---- |
| \--cam | The index of the camera to use. | 0 |
| \--width | The desired capture width for the camera. | 1280 |
| \--height | The desired capture height for the camera. | 720 |
| \--profile | Path to the camera calibration JSON file. | camera\_ext.json |
| \--pattern | The initial marker dictionary to use (see controls). | 0 |
| \--size | The size of the markers in meters. | 0.015 |
| \--flip | Set to 1 to flip the camera view horizontally. | 0 |
| \--win' | Set Windows camera mode | non |
## **Runtime Controls**

While the OpenCV window is active, you can use the following keys:

| Key | Action |
| :---- | :---- |
| **q** | Quit the program. |
| **0** | Use ARUCO\_ORIGINAL (5x5) dictionary. |
| **1** | Use DICT\_4X4\_1000 dictionary. |
| **2** | Use APRILTAG\_36h11 dictionary. |
| **3** | Use APRILTAG\_36h10 dictionary. |
| **\+ / \=** | Increase the marker size (in meters) by 0.005. |
| **\-** | Decrease the marker size (in meters) by 0.005. |
| **p** | Toggle Pose Estimation On/Off. |
| **v** | Toggle the Camera View On/Off (OSC still runs). |
| **f** | Toggle horizontal camera flip On/Off. |

---

## **OSC Output**

The script sends OSC messages for each detected marker.

* **Client IP**: 127.0.0.1 (localhost)  
* **Client Port**: 9000  
* **Address**: /marker

### **Message Payload**

The message is a list of 15 values:

| Index | Value | Type | Description |
| :---- | :---- | :---- | :---- |
| 0 | Marker ID | int | The ID of the detected marker. |
| 1 | tx | float | Translation X (meters). |
| 2 | ty | float | Translation Y (meters). |
| 3 | tz | float | Translation Z (meters). |
| 4 | roll | float | Rotation Roll (radians). |
| 5 | pitch | float | Rotation Pitch (radians). |
| 6 | yaw | float | Rotation Yaw (radians). |
| 7 | c0x | int | Corner 0 X (pixels). |
| 8 | c0y | int | Corner 0 Y (pixels). |
| 9 | c1x | int | Corner 1 X (pixels). |
| 10 | c1y | int | Corner 1 Y (pixels). |
| 11 | c2x | int | Corner 2 X (pixels). |
| 12 | c2y | int | Corner 2 Y (pixels). |
| 13 | c3x | int | Corner 3 X (pixels). |
| 14 | c3y | int | Corner 3 Y (pixels). |

**Note**: If Pose Estimation is toggled **off** (via the p key), values for tx, ty, tz, roll, pitch, and yaw will all be sent as 0.0.

