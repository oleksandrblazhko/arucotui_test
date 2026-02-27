# ArUco-TUI (v.25.1)

**ArUcoTUI** is a software toolkit for rapid TUI (Tangible User Interface) prototyping on portable screens. It uses standard cameras, OpenCV, and ArUco markers for real-time object tracking.

ArUcoTUI uses ArUco fiducial markers to detect physical inputs. The toolkit offers streamlined calibration, a signal processing pipeline, and a client application that translates tangible input into structured events for use in HCI applications.

---

## Server Software for Image Processing

The server designed for real-time ArUco fiducial marker detection and pose estimation is based on **Python OpenCV**. It utilizes the OpenCV library for CV tasks and the `python-osc` library to send detected marker data to the client software via Open Sound Control (OSC) over UDP to a local address.

### Key Features:

* **Initialization:** The script initializes a camera using command-line arguments for its index, resolution, and optional flipping.
* **Calibration:** It loads intrinsic parameters from a JSON file to correct for lens distortion—a crucial step for accurate 3D pose estimation.
* **Processing Loop:** * Captured frames are corrected for distortion and converted to grayscale.
* The system estimates a 3D pose consisting of a translation vector ($t$) and a rotation vector ($r$).
* The rotation vector is converted to a rotation matrix and then into **Euler angles** (roll, pitch, yaw).


* **Data Transmission:** Pose data is sent as a single OSC message containing:
* Marker ID
* Translation vector ($t_x, t_y, t_z$)
* Euler angles ($r_x, r_y, r_z$)
* Pixel coordinates of the four marker corners.

---

## Client Software for Application Development

The client software is based on **Processing**. It defines interactive data representations and physical controllers:

* **DataObject (DO):** Instances representing interactive data.
* **TaggedObject (TO):** Instances representing physical controllers (rigid bodies with ArUco markers).
* **TO_IDs:** Arrays that group markers for each specific object.
* **TagOffsets:** Specifies each marker’s 3D position relative to the object’s center.

### Workflow:

1. **Unpacking:** The software continuously processes incoming OSC data ($t_x, t_y, t_z$ and $r_x, r_y, r_z$).
2. **Calibration Phase:** Users use a calibration pattern to map the camera’s 3D space to the 2D screen coordinates.
3. **Homography:** The software computes a homography matrix to map 3D world coordinates to the 2D interactive surface, saving this matrix to streamline future use.
4. **TagManager:** This component calculates the averaged position/orientation for each `TaggedObject`.
5. **Event Triggering:** If a TO's distance to the surface is within the `touchThreshold`, it triggers event listeners like `TO_Present2D()`, allowing developers to link physical gestures to `DataObjects`.

---

## 3.3 Hardware Implementation and Performance

The implementation was tested using the following hardware stack:

| Component | Specification |
| --- | --- |
| **Camera** | Logitech StreamCam (45-60 fps @ 1280x720) |
| **Display** | 13-inch 2K AMOLED (2560x1440) |
| **Processor** | MacBook Pro (M1 Pro) |
| **Alternate Hardware** | Microsoft Surface Pro 7, Sony toio™ robots |
| **Marker Dictionaries** | `ARUCO_ORIGINAL` (5×5) & `ARUCO_4X4_1000` |
| **Marker Size** | 15 mm to 24 mm width |

**Performance Note:** This setup supports reliable pose detection of a 15mm-width marker within a distance of 25 cm, sufficiently covering the 13-inch display area.

---

## Reference:

> Rong-Hao Liang, Steven Houben, Krithik Ranjan, S. Sandra Bae, Peter Gyory, Ellen Yi-Luen Do, and Clement Zheng. 2026. **ArUcoTUI: Software Toolkit for Prototyping Tangible Interactions on Portable Flat-Panel Displays with OpenCV.** In *Twentieth International Conference on Tangible, Embedded, and Embodied Interaction (TEI ’26)*, March 08–11, 2026, Chicago, IL, USA. ACM, New York, NY, USA, 8 pages. [https://doi.org/10.1145/3731459.3779317](https://doi.org/10.1145/3731459.3779317)