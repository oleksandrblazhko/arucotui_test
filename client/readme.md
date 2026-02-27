# **ArUco-TUI Client v25.3**

**Author:** Rong-Hao Liang (TU Eindhoven)
**Email:** r.liang@tue.nl

This Processing sketch acts as a client for a Tangible User Interface (TUI) system based on ArUco marker tracking. It receives data from an external marker-detection script (e.g., Python with OpenCV) via OSC messages.

The system tracks individual ArUco tags, groups them into "Tagged Objects" (TOs), and maps their positions and orientations from 3D camera space to the 2D screen space. Users can interact with on-screen "Data Objects" (DOs) by moving and rotating the physical Tagged Objects over them.

## **Features**

* **OSC Client:** Listens on port 9000 for /marker messages containing tag ID, 3D position (tx, ty, tz), 3D rotation (rx, ry, rz), and corner points.  
* **Homography Calibration:** Uses a set of corner markers (IDs {1, 3, 2, 0} by default) from a calibration image (ArUco\_Grid15.png) to calculate a homography matrix. This maps the 3D tracking data to the 2D screen.  
* **Tag Management:** Manages the state (present, absent, updated) of all detected tags with a Time-To-Live (TTL) system.  
* **Tagged Object (TO) System:** Defines tangible objects as groups of one or more tags with specific offsets.  
* **Data Object (DO) Interaction:** Allows tangible objects (TOs) to "hit" and control on-screen Data Objects.  
* **Multiple Gesture Modes:** Supports different interaction modes, selectable via keyboard.  
* **Debug Views:** Provides multiple debug overlays to visualize tags, gestures, and data object states.

## **Setup**

1. **Run External Detection:** Start your external ArUco detection script (e.g., Python, OpenCV) that sends OSC messages to this client's IP address on port 9000\.  
2. **Configure Sketch:** Open ArUcoTUI\_Client.pde and configure the following:  
   * TO\_IDs: Define the tag IDs that make up each tangible object.  
   * TO\_Offsets: Define the 3D offsets (in meters) for each tag within its tangible object.  
   * paperWidthOnScreen: Measure the real-world width (in mm) of your calibration sheet and update this value.  
   * markerWidth: The width (in mm) of your markers.  
   * touchThreshold: The distance (in meters) from the plane to consider a TO as "touching".  
3. **Run Processing Sketch:** Run the ArUcoTUI\_Client.pde file.  
4. **Calibrate:**  
   * The sketch will start in calibration mode, showing the calibration image.  
   * Place the calibration sheet (with corner markers 1, 3, 2\) on the surface so it's visible to the camera.  
   * Once all corner markers are detected, the sketch will automatically calculate the homography and switch to interaction mode.  
   * Press the SPACE bar at any time to re-enter calibration mode.

## **Usage & Key Controls**

* **Interaction:** Move a defined Tagged Object over an on-screen Data Object. Depending on the gestureMode, you can change the DO's value, position, and rotation.  
* **Keyboard Shortcuts:**  
  * SPACE: Reset calibration and recalculate homography.  
  * r: Reset Data Objects to their initial positions and values.  
  * 1: Set Gesture Mode 1 (e.g., rotation controls value).  
  * 2: Set Gesture Mode 2 (e.g., rotation controls value, TO controls location).  
  * 3: Set Gesture Mode 3 (e.g., TO controls location and orientation).  
  * g: Toggle Gesture debug view.  
  * t: Toggle Tag debug view (shows all active tags).  
  * d: Toggle Data Object debug view.  
  * s: Toggle Serial (console) debug messages for tag and TO events.

## **File Overview**

* ArUcoTUI\_Client.pde: Main sketch, setup(), draw() loop, UI rendering.  
* oscEvent.pde: Handles incoming OSC messages from the detection script.  
* tools.pde: Contains calibration logic, homography calculation, and coordinate transformation functions.  
* keyEvent.pde: Defines all keyboard shortcuts.  
* Tag.pde: Class defining an individual ArUco tag.  
* TaggedObject.pde: Class defining a tangible object (a collection of one or more tags).  
* TagManager.pde: Manages all Tag and TaggedObject instances, including state updates and grouping.  
* DataObject.pde: Class for the on-screen interactive elements.  
* API.pde: Event listeners (Present, Absent, Update) that link TOs to DOs (e.g., checking for "hits").  
* ContinuousGestures.pde: Implements the logic for the different interaction modes (Mode 1, 2, 3).