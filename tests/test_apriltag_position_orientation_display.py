import cv2
import numpy as np
import pyrealsense2 as rs
from pupil_apriltags import Detector

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
profile = pipeline.start(config)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()  # Get the depth sensor's depth scale
intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
fx, fy, cx, cy = intrinsics.fx, intrinsics.fy, intrinsics.ppx, intrinsics.ppy

camera_matrix = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
tag_size = 0.08  # Size of the AprilTag side in meters

# Initialize AprilTag detector with camera parameters for pose estimation
detector = Detector(families='tag36h11',
                    nthreads=4,
                    quad_decimate=1.0,
                    quad_sigma=0.0,
                    refine_edges=1,
                    decode_sharpening=0.25,
                    debug=0)

def euler_from_rotation_matrix(R):
    ''' Calculate Euler angles (roll, pitch, yaw) from a rotation matrix. '''
    sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    singular = sy < 1e-6
    if not singular:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])
    else:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0
    return np.rad2deg(x), np.rad2deg(y), np.rad2deg(z)  # Convert to degrees

try:
    while True:
        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Convert color_image to grayscale
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        tags = detector.detect(gray, estimate_tag_pose=True, camera_params=[fx, fy, cx, cy], tag_size=tag_size)

        for tag in tags:
            # Extract tag position, orientation, and draw bounding box
            (ptA, ptB, ptC, ptD) = tag.corners
            cv2.polylines(color_image, [np.array(tag.corners, np.int32).reshape((-1,1,2))], True, (0,255,0), 2, cv2.LINE_AA)

            ptA, ptB, ptC, ptD = np.array(ptA, dtype=int), np.array(ptB, dtype=int), np.array(ptC, dtype=int), np.array(ptD, dtype=int)
            cv2.line(color_image, tuple(ptA), tuple(ptB), (0, 255, 0), 2)
            cv2.line(color_image, tuple(ptB), tuple(ptC), (0, 255, 0), 2)
            cv2.line(color_image, tuple(ptC), tuple(ptD), (0, 255, 0), 2)
            cv2.line(color_image, tuple(ptD), tuple(ptA), (0, 255, 0), 2)

            # Calculate tag orientation (Euler angles)
            tvec = tag.pose_t  # Translation vector
            R = tag.pose_R  # Rotation matrix
            pitch, yaw, roll = euler_from_rotation_matrix(R)

            # Display tag ID and orientation on the frame
            tag_center = np.mean(tag.corners, axis=0).astype(int)
            # Line 1: Tag ID
            cv2.putText(color_image, f"ID: {tag.tag_id}", 
                        (tag_center[0]-150, tag_center[1] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            # Line 2: X, Y, Z positions
            cv2.putText(color_image, f"X: {tvec[0][0]*100:.2f}cm, Y: {tvec[1][0]*100:.2f}cm, Z: {tvec[2][0]*100:.2f}cm", 
                        (tag_center[0]-150, tag_center[1] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            # Line 3: Roll, Pitch, Yaw orientations
            cv2.putText(color_image, f"Roll: {roll:.2f}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f}", 
                        (tag_center[0]-150, tag_center[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
 
        # Display the resulting frame
        cv2.imshow('Frame', color_image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming
    pipeline.stop()
