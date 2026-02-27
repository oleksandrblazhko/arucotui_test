########################################
# ArUCoTUI server ver.25.2
# Rong-Hao Liang (TU Eindhoven)
# email r.liang@tue.nl
# Tested with opencv-python ver. 4.6.0.66
########################################
# CONTROLS:
# q: Stop the program
# 0-3: Change ArUco/AprilTag dictionary
# +/-: Increase/Decrease marker size
# p: Toggle Pose Estimation
# v: Toggle Camera View
# f: Toggle Camera Flip
# c: Roll Camera Index
# q: Quit Program
########################################

# Import necessary libraries
from pythonosc import udp_client  # Import UDP client for OSC communication
import cv2  # Import OpenCV library
import numpy as np  # Import numpy library for numerical operations
import json  # Import json library for reading camera calibration data from a JSON file
import time  # Import time library for measuring FPS
import argparse  # Import argparse for command line argument parsing
# Removed Thread import

def find_connected_cameras(max_check=10):
    """
    Checks camera indices 0 through max_check-1.
    Returns the number of valid (openable) camera indices.
    """
    count = 0
    for i in range(max_check):
        # Try to open the camera
        cap_test = cv2.VideoCapture(i)
        
        # Check if it was successfully opened
        if cap_test.isOpened():
            count += 1
            # MUST release it so the main stream can use it later
            cap_test.release()
        else:
            # If this index fails, we assume no more cameras are available
            break
            
    return count

# Create a UDP client to send OSC messages
client = udp_client.SimpleUDPClient("127.0.0.1", 9000)  # Define the IP address and port of the receiver

# Create an argument parser
parser = argparse.ArgumentParser(description='ArUco Marker Detection with Camera Selection')

# Add command line arguments
parser.add_argument('--cam', type=int, default=0, help='Camera index (default is 0)')
parser.add_argument('--width', type=int, default=1280, help='Frame width (default is 1280)')
parser.add_argument('--height', type=int, default=720, help='Frame height (default is 720)')
parser.add_argument('--profile', type=str, default='camera_ext.json', help='Camera profile JSON file')
parser.add_argument('--pattern', type=int, default=0, help='0: ArUco5x5, 1: April36h11')
parser.add_argument('--size', type=float, default=0.05, help='ArUco marker size in meters')
parser.add_argument('--flip', type=int, default=0, help='Camera flip (default is 0)')
parser.add_argument('--win', action='store_true', help='Set Windows camera mode')

# Parse the command line arguments
args = parser.parse_args()

if args.win:
    initCamMode = True
else:
    initCamMode = False

# Detect how many cameras are connected
num_cameras = find_connected_cameras()

if num_cameras == 0:
    print("Error: No cameras found! Exiting.")
    exit()

print(f"INFO: Found {num_cameras} connected cameras.")

# Check if the user's --cam argument is valid
if args.cam >= num_cameras:
    print(f"Warning: Camera index {args.cam} not found. Defaulting to index 0.")
    args.cam = 0

# MODIFIED: Initialize the standard (single-threaded) camera capture
if initCamMode:
    cap = cv2.VideoCapture(args.cam, cv2.CAP_DSHOW)
else: 
    cap = cv2.VideoCapture(args.cam)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

# Initialize variables for measuring FPS (Frames Per Second)
fps = 0
prev_time = time.time()  # Get the current time as the previous time

# Print the OpenCV library version
print(cv2.__version__)

# Define dictionary names and their corresponding OpenCV enums for dynamic switching
# Pre-load the dictionary objects for efficiency
ARUCO_PATTERNS = {
    0: (cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL), "ARUCO_ORIGINAL (5x5)"),
    1: (cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000), "4X4_1000"),
    2: (cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11), "APRILTAG_36h11"),
    3: (cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h10), "APRILTAG_36h10")
}

parameters = cv2.aruco.DetectorParameters_create()
parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
# We now use args.size directly, but update it in the loop
marker_size = args.size  # Define the size of the ArUco marker in meters



# Load camera calibration data from a JSON file
with open(args.profile, 'r') as json_file:
    camera_data = json.load(json_file)
distCoeffs = np.array(camera_data["dist"])
cameraMatrix = np.array(camera_data["mtx"])

# Pre-calculate the undistortion mapping for efficiency
newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, (args.width, args.height), 1, (args.width, args.height))
mapx, mapy = cv2.initUndistortRectifyMap(cameraMatrix, distCoeffs, None, newCameraMatrix, (args.width, args.height), 5)

isCalibed = True
# Add state for toggling pose estimation
pose_estimation_enabled = True
# Add state for toggling camera view
camera_view_enabled = True

# Define a function to convert a rotation matrix to Euler angles (yaw, pitch, roll)
def rotation_matrix_to_euler_angles(rotation_matrix):
    # Extract the rotation components from the rotation matrix
    sy = np.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] + rotation_matrix[1, 0] * rotation_matrix[1, 0])
    singular = sy < 1e-6  # Check if the rotation matrix is singular (close to zero)

    if not singular:
        # Compute yaw, pitch, and roll from the rotation matrix
        roll = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
        pitch = np.arctan2(-rotation_matrix[2, 0], sy)
        yaw = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
    else:
        # Handle the case when the rotation matrix is singular
        roll = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
        pitch = np.arctan2(-rotation_matrix[2, 0], sy)
        yaw = 0

    return roll, pitch, yaw

# Define a step for changing marker size
MARKER_SIZE_STEP = 0.001  # 1mm

# Main loop for video capture and ArUco marker detection
while True:
    ret, frame = cap.read()  # Read from camera (blocking call)

    if not ret or frame is None:
        print("Waiting for frame...")
        time.sleep(0.1) # Avoid busy-waiting if stream starts slow
        continue  # Break the loop if no frame is captured

    # Capture key press first
    key = cv2.waitKey(1) & 0xFF

    # Exit the program when the 'q' key is pressed
    if key == ord('q'):
        break
    # Check for pattern change keys
    elif key == ord('0'):
        args.pattern = 0
    elif key == ord('1'):
        args.pattern = 1
    elif key == ord('2'):
        args.pattern = 2
    elif key == ord('3'):
        args.pattern = 3
    # Check for marker size change keys
    elif key == ord('+') or key == ord('='):
        args.size += MARKER_SIZE_STEP
    elif key == ord('-'):
        args.size -= MARKER_SIZE_STEP
        # Add a check to prevent size from going to zero or negative
        if args.size < MARKER_SIZE_STEP:
            args.size = MARKER_SIZE_STEP
    # Check for pose estimation toggle
    elif key == ord('p'):
        pose_estimation_enabled = not pose_estimation_enabled
    # Check for camera view toggle
    elif key == ord('v'):
        camera_view_enabled = not camera_view_enabled
        if not camera_view_enabled:
            pass # We will just stop drawing, not destroy window
    # Check for camera flip toggle
    elif key == ord('f'):
        args.flip = 1 - args.flip  # Toggle between 0 and 1
        if not camera_view_enabled:
            pass
    # Check for rolling camera index
    elif key == ord('c'):
        print(f"Stopping camera index {args.cam}...")
        cap.release() # Release the current camera

        # Use the detected num_cameras variable for wrapping
        args.cam = (args.cam + 1) % num_cameras 
        
        print(f"Starting new camera index {args.cam}...")
        
        # Create a new capture object for the new camera index
        if initCamMode:
            cap = cv2.VideoCapture(args.cam, cv2.CAP_DSHOW)
        else: 
            cap = cv2.VideoCapture(args.cam)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)


    # Update marker_size variable from the (potentially changed) args.size
    marker_size = args.size

    # Calculate FPS (Frames Per Second)
    current_time = time.time()
    elapsed_time = current_time - prev_time
    if elapsed_time > 0:
        fps = 1 / elapsed_time
    prev_time = current_time
    
    # Use cv2.remap() for faster undistortion
    frame = cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)
    
    # Crop the image based on the Region of Interest (ROI) from getOptimalNewCameraMatrix
    x, y, w, h = roi
    frame = frame[y:y+h, x:x+w]
    
    # Get current pattern name and dictionary object based on args.pattern
    # Select the pre-loaded dictionary and name
    aruco_dict, pattern_name = ARUCO_PATTERNS.get(args.pattern, ARUCO_PATTERNS[3]) # Default to pattern 3

    # All drawing operations are now conditional on camera_view_enabled
    if camera_view_enabled:
        # Display FPS on the frame
        cv2.putText(frame, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display the current pattern name
        cv2.putText(frame, f'Pattern: {pattern_name} (Press [0-3])', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display the current marker size
        cv2.putText(frame, f'Marker Size: {marker_size:.3f} m (Press +/-)', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Display the pose estimation status
        pose_status_text = f'Pose: {"ON" if pose_estimation_enabled else "OFF"} (Press P)'
        pose_status_color = (0, 255, 0) if pose_estimation_enabled else (0, 0, 255) # Green for ON, Red for OFF
        cv2.putText(frame, pose_status_text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, pose_status_color, 2)

        # Display the view status
        cv2.putText(frame, "View: ON (Press V)", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Display the flip status
        flip_status_text = f'Flip: {"ON" if args.flip == 1 else "OFF"} (Press F)'
        flip_status_color = (0, 255, 0) if args.flip == 0 else (0, 0, 255) # Green for ON, Red for OFF
        cv2.putText(frame, flip_status_text, (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 1, flip_status_color, 2)

        # Display the current camera index
        cv2.putText(frame, f'Camera: {args.cam} (Press C)', (10, 270), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Display the current camera index
        cv2.putText(frame, f'Quit Program (Press Q)', (10, 310), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Convert the frame to grayscale (optional)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect ArUco markers in the grayscale frame
    corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        # Only draw markers if view is enabled
        if camera_view_enabled:
            # Draw detected markers and their pose axes
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # Check if pose estimation is enabled
        if pose_estimation_enabled:
            for i in range(len(ids)):
                # marker_size is now dynamic
                rvec, tvec, markerPoints = cv2.aruco.estimatePoseSingleMarkers(corners[i], marker_size, newCameraMatrix, distCoeffs)

                # Convert the rotation matrix to Euler angles
                rotation_matrix, _ = cv2.Rodrigues(rvec)
                roll, pitch, yaw = rotation_matrix_to_euler_angles(rotation_matrix)

                # Flatten the translation vector to a 1D array
                translation_vector = tvec.flatten()
                tx, ty, tz = translation_vector
                
                # Create an OSC message with marker ID and pose information
                message = [int(ids[i].item()), float(tx), float(ty), float(tz), float(roll), float(pitch), float(yaw),
                   int(corners[i][0][0][0].item()), int(corners[i][0][0][1].item()),
                   int(corners[i][0][1][0].item()), int(corners[i][0][1][1].item()),
                   int(corners[i][0][2][0].item()), int(corners[i][0][2][1].item()),
                   int(corners[i][0][3][0].item()), int(corners[i][0][3][1].item())]

                # Only draw axes if view is enabled
                if camera_view_enabled:
                    # marker_size is now dynamic
                    cv2.drawFrameAxes(frame, newCameraMatrix, distCoeffs, rvec, tvec, marker_size * 0.5)
                else:
                    # Print marker information to the console on a single line
                    print(f"ID: {int(ids[i].item()):<3} | Pose: ON | T: ({tx:6.3f}, {ty:6.3f}, {tz:6.3f}) | R: ({roll:6.3f}, {pitch:6.3f}, {yaw:6.3f})")

                # Send the OSC message to the specified address ("/message")
                client.send_message("/marker", message)
        
        else: # If pose estimation is off, just print the IDs
            if ids is not None:
            # Draw detected markers and their pose axes
                for corner in corners:
                    int_corners = np.int32(corner)  # Convert to integer array
                    cv2.fillPoly(frame, [int_corners], color=(255, 255, 255))  # white fill
                    cv2.polylines(frame, [int_corners], isClosed=True, color=(255,255,255), thickness=3)
                
                cv2.aruco.drawDetectedMarkers(frame, corners, ids, borderColor=(0,0,100))
                
                for i in range(len(ids)):
                    # Create an OSC message with marker ID and pose information
                    message = [int(ids[i].item()), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                    int(corners[i][0][0][0].item()), int(corners[i][0][0][1].item()),
                    int(corners[i][0][1][0].item()), int(corners[i][0][1][1].item()),
                    int(corners[i][0][2][0].item()), int(corners[i][0][2][1].item()),
                    int(corners[i][0][3][0].item()), int(corners[i][0][3][1].item())]
                    # Send the OSC message to the specified address ("/message")
                    client.send_message("/marker", message)
            
            if camera_view_enabled is False:
                print(f"IDs: {ids.flatten()} | Pose: OFF")


    # Only update the window display if camera view is enabled
    if camera_view_enabled:
        # Display the frame with detected markers and axes
        if(args.flip == 1): frame = cv2.flip(frame, 1)  # 1 indicates horizontal flip
        
        cv2.imshow('ArUco Marker Detection', frame)
    else:
        # Print the current FPS to the console
        print(f'FPS: {int(fps)}')

# Release the camera and close all OpenCV windows
cap.release() # Use .release() for VideoCapture
cv2.destroyAllWindows()