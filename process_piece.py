import cv2
import numpy as np

from fl_types import J_Piece
from find_rotation import find_rotation
from fl_core import rotate_line, show_image, get_bounding_box_from_lines, convert_img_to_bgr
from find_corners import find_approx_corners, find_better_corners
from fl_pad_and_scale import fl_pad_and_scale
from find_triangles import find_triangles_from_corners

def process_piece(piece: J_Piece, pre_processed_image: np.ndarray, debug:bool=False) -> bool:

    """ Process a single Jigsaw piece:
    Piece of type J_Piece must have basic info already determined via a function such as get_piece_info().

    Then:
    1. Expand image if needed so no info is lost if we rotate it.
    2. Find the lines that make up the edges.
    3. Use these lines to determine how to rotate the piece in order to 'straighten it up'.
    4. Rotate the piece.
    5. Find the corners as well as tab and blank areas.
    6. Find triangles from corners.

    As we go, add the computed information to the piece object.
    """
    info = piece.info
    assert info is not None, "Piece must have basic info."
    assert info.box is not None, "Piece must have bounding box info."
    assert info.centroid is not None, "Piece must have centroid defined."

    # create a new image that is just the piece, by cropping the pre_processed_image using the 
    # bounding box of the piece, and scale it up to something more useable. Also add padding around 
    # the piece so it can be rotated around centroid without losing any pixels.

    orig_x, orig_y, w, h = info.box
    cx, cy = info.centroid
    piece_image, _, rot_center, inverse_transform_fn, scale_factor = fl_pad_and_scale(pre_processed_image, 
                                                                        [[(orig_x,orig_y), (orig_x+w, orig_y+h)]],
                                                                        info.centroid,
                                                                        new_img_size = None, 
                                                                        debug=debug)
    piece.orig['user_image'] = piece_image
    piece.orig['scale_factor'] = scale_factor
    piece.orig['inverse_transform_fn'] = inverse_transform_fn
    piece.orig['rot_center'] = rot_center

    cx,cy = rot_center

    # Extract edges using Canny edge detection. This will give us a binary image where the edges
    # are white and the rest is black. We can then use this to find lines and estimate rotation.
    orig_edges = cv2.Canny(piece_image, 50, 150, apertureSize=3)

    # Analyse the image to see if it can be 'straightened up' and if so by how much.
    rotation_angle_rad, lines = find_rotation(orig_edges, cx, cy, debug=debug)
    rotation_angle = np.degrees(rotation_angle_rad)
    piece.rot['rotation_angle_rad'] = rotation_angle_rad


    # rotate the image around the point cx, cy by the rotation angle
    rotation_matrix = cv2.getRotationMatrix2D((cx, cy), rotation_angle, 1.0)
    rotated_image_grey = cv2.warpAffine(piece_image, rotation_matrix, (500, 500))
    rotated_image = cv2.cvtColor(rotated_image_grey, cv2.COLOR_GRAY2BGR)
    piece.rot['edges_image_grey'] = rotated_image_grey
    piece.rot['img_w'], piece.rot['img_h'] = rotated_image_grey.shape[1], rotated_image_grey.shape[0]
    rotated_edges = cv2.warpAffine(orig_edges.copy(), rotation_matrix, (piece.rot['img_w'], piece.rot['img_h']))

    # Rotate the lines we found as well for debugging purposes , and draw them on the rotated image. 
    # This will help us see if the rotation is correct and if the lines are aligned with the edges 
    # of the piece after rotation. We can also use this to find the corners of the piece after rotation, 
    # which will be useful for further processing steps like matching pieces together.

    rotated_lines = [ rotate_line(line, (cx, cy), rotation_angle_rad) for line in lines ]
    # get top_left and bottom right bounding box of rotated lines.
    tl, br = get_bounding_box_from_lines(rotated_lines)
    if tl is not None and br is not None:
        (tl_x, tl_y), (br_x, br_y) = (tl, br)
    else:
        return False

    # Find the corners of the piece
    approx_corners, blank_keep_outs, tab_keep_outs = find_approx_corners(rotated_lines, (tl_x, tl_y), (br_x, br_y), end_to_end_dist_thresh=20, debug=debug)
    # print(f"Approx corners are: {approx_corners}")

    # Refine the corner pixel selection
    corners = find_better_corners(rotated_edges, approx_corners)

    if len(corners) == 2: # [[TL, TR], [BL, BR]].
        piece.rot['corners'] = corners
        piece.rot['blank_keep_outs'] = blank_keep_outs
        piece.rot['tab_keep_outs'] = tab_keep_outs
    else:
        return False

    if debug:
        # Display rotated edge image with corners.
        rotated_edges_bgr = convert_img_to_bgr(rotated_edges)
        # Add approx corners to rot_edges image.
        for corner_point in [ col for row in corners for col in row if col]:
            _, point, _ = corner_point
            cv2.circle(rotated_edges_bgr, (int(point[0]), int(point[1])), 4, (0, 0, 200), 2)
        show_image(rotated_edges_bgr, str=f"Rot edges and better corners {info.id}", max_side=None, wait_for_key=False)


    
    # Get triangles formed by corners and the point furthest from the line between 2 corners.
    # Operate on rotated edge image.
    triangles, side_types, piece_type, dir = find_triangles_from_corners(rotated_edges, corners, debug=debug)
    if not triangles or not side_types or not dir: return False
    print(f"Side Types are : {side_types}")
    if len(triangles) == 4:
        piece.dir = dir
        for tri, et in zip(triangles, side_types):
            piece.rot['triangles'].append(tri)
            piece.info.side_types.append(et)
            piece.info.piece_type = piece_type
    else:
        return False


    if debug:
        # draw bbox of lines on rotated image for debugging purposes
        cv2.rectangle(rotated_image, (int(tl_x), int(tl_y)), (int(br_x), int(br_y)), (255, 0, 0), 1)

        # Show UN-rotated lines
        for (x1, y1), (x2, y2) in lines:
            cv2.line(rotated_image, (x1, y1), (x2, y2), (25, 155, 145), 1)

        # Show rotated lines
        for (x1,y1), (x2,y2) in rotated_lines:
            cv2.line(rotated_image, (int(x1), int(y1)), (int(x2), int(y2)), (80, 255, 80), 3)

        # Corners is list of lists [rows][cols]. 4 elements
        for corner_point in [ col for row in corners for col in row if col]:
            _, point, angle_rad = corner_point
            cv2.circle(rotated_image, (int(point[0]), int(point[1])), 10, (0, 0, int(255*angle_rad/(2*np.pi))), -1)
        show_image(rotated_image, str=f"Corners {info.id}", max_side=1000, wait_for_key=True)

    return True