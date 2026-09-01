import numpy as np
import math
import cv2
from fl_types import J_Piece, SideType
from fl_core import show_image

def show_matching_pair(p1: J_Piece, p1_s_idx: int, p2: J_Piece, p2_s_idx: int, wait_for_key=True, debug=False):
    """
    Create a side-by-side image of two puzzle pieces that match. 
    The matching sides are aligned.
    If wait_for_key is True, the function waits for user to press a key
    """
    img1 = p1.orig['user_image']
    img2 = p2.orig['user_image']
    
    if img1 is None or img2 is None:
        if debug:
            print("Error: one or both pieces do not have user_image loaded.")
        return

    # Convert to BGR if grayscale to ensure compatibility
    if len(img1.shape) == 2:
        img1_color = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
    else:
        img1_color = img1

    if len(img2.shape) == 2:
        img2_color = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)
    else:
        img2_color = img2

    # Get centers of rotation
    cx1, cy1 = p1.orig['rot_center']
    cx2, cy2 = p2.orig['rot_center']
    
    if cx1 is None or cy1 is None:
        cx1, cy1 = img1_color.shape[1] // 2, img1_color.shape[0] // 2
    if cx2 is None or cy2 is None:
        cx2, cy2 = img2_color.shape[1] // 2, img2_color.shape[0] // 2

    # Get straightening rotation angles
    rot_angle_rad1 = p1.rot['rotation_angle_rad']
    rot_angle_rad2 = p2.rot['rotation_angle_rad']
    
    angle_deg1 = np.degrees(rot_angle_rad1) if rot_angle_rad1 is not None else 0.0
    angle_deg2 = np.degrees(rot_angle_rad2) if rot_angle_rad2 is not None else 0.0

    # Calculate total rotation:
    # For p1, matching side p1_s_idx should face East (Right, index 1).
    # For p2, matching side p2_s_idx should face West (Left, index 3).
    total_angle_1 = angle_deg1 + (p1_s_idx - 1) * 90
    total_angle_2 = angle_deg2 + (p2_s_idx - 3) * 90

    # Rotate the images
    h1, w1 = img1_color.shape[:2]
    rot_mat1 = cv2.getRotationMatrix2D((cx1, cy1), total_angle_1, 1.0)
    rotated_p1 = cv2.warpAffine(img1_color, rot_mat1, (w1, h1))
    
    h2, w2 = img2_color.shape[:2]
    rot_mat2 = cv2.getRotationMatrix2D((cx2, cy2), total_angle_2, 1.0)
    rotated_p2 = cv2.warpAffine(img2_color, rot_mat2, (w2, h2))

    # Create the canvas (main_image)
    H = max(h1, h2)
    W = w1 + w2
    main_image = np.zeros((H, W, 3), dtype=np.uint8)

    # Insert the rotated images vertically centered
    y_offset1 = (H - h1) // 2
    y_offset2 = (H - h2) // 2
    
    main_image[y_offset1 : y_offset1 + h1, 0 : w1] = rotated_p1
    main_image[y_offset2 : y_offset2 + h2, w1 : w1 + w2] = rotated_p2

    # Display the final side-by-side image
    show_image(main_image, str="Matching Pair", wait_for_key=wait_for_key)
