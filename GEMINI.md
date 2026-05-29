# ArUcoTUI Project

## Project Overview

This project, **ArUcoTUI**, is a software toolkit for rapid Tangible User Interface (TUI) prototyping. It uses a client-server architecture to track physical objects with ArUco markers and translate their movements into on-screen interactions.

*   **Server (`server/`):** A Python application that uses OpenCV to perform real-time ArUco marker detection via a standard camera. It calculates the 6D pose (translation and rotation) of each marker and broadcasts this data over the network using Open Sound Control (OSC).

*   **Client (`client/`):** A Processing application that listens for OSC data from the server. It includes a calibration process to map the camera's 3D space to the 2D screen coordinates. The client defines "Tagged Objects" (physical controllers) and "Data Objects" (interactive on-screen elements) and manages the interaction logic between them.

**Key Technologies:**
*   **Server:** Python, OpenCV, python-osc, NumPy
*   **Client:** Processing

## Building and Running

The project requires running the server and client components separately.

### Running the Server (Python)

The server is responsible for camera capture and marker detection.

1.  **Prerequisites:**
    *   Python 3.x
    *   A connected webcam

2.  **Install Dependencies:**
    Navigate to the `server` directory and install the required packages from `requirements.txt`.
    ```bash
    cd server
    pip install -r requirements.txt
    ```

3.  **Camera Calibration:**
    The server requires a camera calibration file to accurately estimate marker poses.
    *   You must generate a `camera_ext.json` file containing your camera's intrinsic matrix (`mtx`) and distortion coefficients (`dist`).
    *   Place this file in the `server` directory. A template is available in `server/readme.md`.

4.  **Run the Server:**
    From the `server` directory, run the `marker.py` script. You can specify the camera index and resolution.
    ```bash
    # Example: Use camera 0 with 1280x720 resolution
    python marker.py --cam 0 --width 1280 --height 720
    ```
    The server will start sending OSC data to `127.0.0.1:9000`.

### Running the Client (Processing)

The client receives OSC data and runs the interactive application.

1.  **Prerequisites:**
    *   Processing IDE (4.x or later).
    *   The required Processing libraries (the `oscP5` library is likely needed, and the `ejml` jars are included in the `code/` folder).

2.  **Open the Sketch:**
    Open the `ArUcoTUI_Client.pde` sketch located in `client/ArUcoTUI_Client/` using the Processing IDE.

3.  **Configure (First Time):**
    Before running, you may need to configure object and marker properties in `ArUcoTUI_Client.pde`, such as `TO_IDs` (which marker IDs belong to which object) and `TO_Offsets`.

4.  **Run the Sketch:**
    Press the "Run" button in the Processing IDE.

5.  **Calibrate the Surface:**
    *   The application starts in calibration mode.
    *   Place the `ArUco_Grid15.png` calibration pattern (found in `client/data/`) on your interactive surface, visible to the camera.
    *   The sketch will automatically detect the corner markers, calculate the homography matrix to map the 3D space to your 2D screen, and switch to interaction mode.
    *   You can press the `SPACE` bar to re-run the calibration at any time.

## Development Conventions

*   **Separation of Concerns:** The core logic is split between the server (perception) and the client (interaction). The server's only job is to detect markers and send data. The client's job is to interpret that data and manage application-specific logic.
*   **Communication Protocol:** All communication happens via OSC messages sent from server to client over UDP. The message format is documented in `server/readme.md`.
*   **Configuration:**
    *   Server configuration (camera, resolution, marker size) is handled via command-line arguments.
    *   Client configuration (tangible object definitions, interaction logic) is handled within the Processing sketch files, primarily `ArUcoTUI_Client.pde`.
*   **Coordinate Systems:** Be mindful of the different coordinate systems: the camera's 3D space, the marker's local 3D space, and the client's 2D screen space. The `tools.pde` file in the client contains the transformation logic.
