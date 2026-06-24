import cv2
import numpy as np
from fl_core import get_bounding_box_from_lines, get_distance_between_2_points

# Do the following changes to create a new image:
# 1. create a new image from the bounding box of just the piece itself.
# 2. pad the image so that it can be rotated around cx,cy without being cropped.
# 3. scale it to the desired size.
# Return the new image, the new b-box, and the new center of rotation.

# Inputs:
# image - a cv2 image that is monochrome
# lines : list of line, where line = [start, end], where start and end are points (x,y)
# rot_point: point (x,y)
# new_image_size: the desired size of the largest dimension (height or width) after scaling.

def fl_pad_and_scale(image, lines, rot_point, new_img_size = 500, debug=False):

    # create a new image that is just the piece, by cropping the pre_processed_image using the 
    # bounding box of the piece.
    bb = get_bounding_box_from_lines(lines) # top left, bottom right points
    x, y, w, h = bb[0][0], bb[0][1], bb[1][0]-bb[0][0], bb[1][1]-bb[0][1]
    cx, cy = rot_point
    piece_image = image[y:y+h, x:x+w]
    cx -= x
    cy -= y
    bb = [(0,0), (w-1, h-1)]

    # compute the radius of the surrounding circle.
    # We can use this to increase the canvas size to ensure that we can rotate the piece without 
    # cutting off any parts of it. 
    diameter = get_distance_between_2_points((x,y), (x+w, y+h))

    add_height = max(0, int(diameter - h)) // 2 + 5
    add_width = max(0, int(diameter - w)) // 2 + 5

    # Add black padding around the piece so that the rotation wont cut off any parts of it.
    piece_image = cv2.copyMakeBorder(piece_image, add_height, add_height, add_width, add_width, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    cx += add_width
    cy += add_height
    bb = [(bb[0][0]+add_width, bb[0][1]+add_height), (bb[1][0]+add_width, bb[1][1]+add_height)]

    # scale the image to new_img_size on longest side for better processing. 
    # We can use cv2.resize for this, and we can use interpolation to maintain quality.
    scale_factor = new_img_size / max(w + 2*add_width, h + 2*add_height)
    piece_image = cv2.resize(piece_image, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    cx = int(cx * scale_factor)
    cy = int(cy * scale_factor)
    bb = [(bb[0][0]*scale_factor, bb[0][1]*scale_factor), (bb[1][0]*scale_factor, bb[1][1]*scale_factor)]

    def inverse_transform(pt):
        pt_x, pt_y = pt
        # Undo scale
        x_padded = pt_x / scale_factor
        y_padded = pt_y / scale_factor
        # Undo padding
        x_cropped = x_padded - add_width
        y_cropped = y_padded - add_height
        # Undo crop
        x_orig = x_cropped + x
        y_orig = y_cropped + y
        return (x_orig, y_orig)

    return piece_image, bb, (cx, cy), inverse_transform