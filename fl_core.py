# core routines used for line finding
import sys

import numpy as np
import math
import cv2

# return height, width, channels = img.shape
def get_image_info(image):
    return image.shape

def rotate_point(point, center, angle_rad):
    # Rotate a point around a center by a given angle in radians.
    # Returns the new coordinates of the point after rotation.
    x, y = point
    cx, cy = center
    cos_a = np.cos(-angle_rad)
    sin_a = np.sin(-angle_rad)
    new_x = cos_a * (x - cx) - sin_a * (y - cy) + cx
    new_y = sin_a * (x - cx) + cos_a * (y - cy) + cy
    return (new_x, new_y)

def rotate_line(line, center, angle_rad):
    # Rotate a line (defined by two points) around a center by a given angle in radians.
    # Returns the new coordinates of the line after rotation.
    (x1, y1), (x2, y2) = line
    new_start = rotate_point((x1, y1), center, angle_rad)
    new_end = rotate_point((x2, y2), center, angle_rad)
    return (new_start, new_end)

def get_distance_between_2_points(pt1, pt2):
    return math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

# shortest distance from point p1 to the infinite line segment defined by points p2 and p3
def point_to_infinite_line_distance(p1, p2, p3):
    x1, y1 = p1; x2, y2 = p2; x3, y3 = p3
    
    # Line equation coefficients: Ax + By + C = 0
    A = y3 - y2 ; B = x2 - x3; C = x3 * y2 - y3 * x2
    
    # Perpendicular distance formula
    numerator = abs(A * x1 + B * y1 + C)
    denominator = math.sqrt(A**2 + B**2)
    
    return numerator / denominator

def points_are_close(pt1, pt2, thresh=10):
    return get_distance_between_2_points(pt1, pt2) < thresh

# compute angular tolerance based on line length, and use it to check if the angle of a new point 
# is consistent with the average angle of the line so far.
def get_angle_tol(line_length):
    return abs(np.arctan2(1.9, line_length)) if line_length > 0 else np.pi/2
    
def get_side_of_tab(start_pt, end_pt, tl_bbox, br_bbox):
    """ Determine which side of the bounding box a tab neck is on. """
    cx = (tl_bbox[0] + br_bbox[0]) / 2
    cy = (tl_bbox[1] + br_bbox[1]) / 2
    diff_x = abs(start_pt[0] - end_pt[0])
    diff_y = abs(start_pt[1] - end_pt[1])
    min_from_bb_x = 0.1 * abs(br_bbox[0] - tl_bbox[0])
    min_from_bb_y = 0.1 * abs(br_bbox[1] - tl_bbox[1])
    # print(f"SIDE: {start_pt} -> {end_pt} : diffx = {diff_x}   diffy= {diff_y}  min_from_bbx = {min_from_bb_x:.1f} min_from_bby={min_from_bb_y:.1f} ", end='')
    # print(f"tl={tl_bbox} br={br_bbox}")

    if diff_x > diff_y: # top or bottom
        if start_pt[1] < cy and end_pt[1] < cy:
            if abs(min(start_pt[1], end_pt[1]) - tl_bbox[1]) < min_from_bb_y: return "" # neck of tab/blank is too close to bbox
            return 'T'  # Top
        elif start_pt[1] > cy and end_pt[1] > cy:
            if abs(min(start_pt[1], end_pt[1]) - br_bbox[1]) < min_from_bb_y: return "" # neck of tab/blank is too close to bbox
            return 'B'  # Bottom
        else:
            print(f"\nfl_core: get_side: ERROR: Cannot determine bbox top or bottom side for line segment from {start_pt} to {end_pt}.\n") # left or right
    else: # left or right
        if start_pt[0] < cx and end_pt[0] < cx:
            if abs(min(start_pt[0], end_pt[0]) - tl_bbox[0]) < min_from_bb_x: return "" # neck of tab/blank is too close to bbox
            return 'L'  # Left
        elif start_pt[0] > cx and end_pt[0] > cx:
            if abs(min(start_pt[0], end_pt[0]) - br_bbox[0]) < min_from_bb_x: return "" # neck of tab/blank is too close to bbox
            return 'R'  # Right
        else:
            print(f"\nfl_core: get_side: ERROR: Cannot determine bbox left or right side for line segment from {start_pt} to {end_pt}.\n") # top or bottom
            sys.exit(1)
    return ""

def get_side_of_blank(start_pt, end_pt, tl_bbox, br_bbox):
    """ Determine which side of the bounding box a blank neck is on. """
    cx = (tl_bbox[0] + br_bbox[0]) / 2
    cy = (tl_bbox[1] + br_bbox[1]) / 2
    diff_x = abs(start_pt[0] - end_pt[0])
    diff_y = abs(start_pt[1] - end_pt[1])
    max_from_bb_x = 0.2 * abs(br_bbox[0] - tl_bbox[0])
    max_from_bb_y = 0.2 * abs(br_bbox[1] - tl_bbox[1])
    #print(f"SIDE: {start_pt} -> {end_pt} : diffx = {diff_x}   diffy= {diff_y}  max_from_bbx = {max_from_bb_x:.1f} max_from_bby={max_from_bb_y:.1f} ", end='')
    #print(f"tl={tl_bbox} br={br_bbox}")
    if diff_x > diff_y: # top or bottom
        # both x cords must be away from left/right edge
        for x in [start_pt[0], end_pt[0]]:
            if abs(x-tl_bbox[0]) < max_from_bb_x or abs(x-br_bbox[0]) < max_from_bb_x:
                return ""
        if start_pt[1] < cy and end_pt[1] < cy:
            if abs(min(start_pt[1], end_pt[1]) - tl_bbox[1]) > max_from_bb_y: return "" # neck of tab/blank is too far from bbox
            return 'T'  # Top
        elif start_pt[1] > cy and end_pt[1] > cy:
            if abs(min(start_pt[1], end_pt[1]) - br_bbox[1]) > max_from_bb_y: return "" # neck of tab/blank is too far from bbox
            return 'B'  # Bottom
        else:
            print(f"\nfl_core: get_side: ERROR: Cannot determine bbox top or bottom side for line segment from {start_pt} to {end_pt}.\n") # left or right
    else: # left or right
        # both y coords must be away from top/bottom edge
        for y in [start_pt[1], end_pt[1]]:
            if abs(y-tl_bbox[1]) < max_from_bb_y or abs(y-br_bbox[1]) < max_from_bb_y:
                return ""
        if start_pt[0] < cx and end_pt[0] < cx:
            if abs(min(start_pt[0], end_pt[0]) - tl_bbox[0]) > max_from_bb_x: return "" # neck of tab/blank is too far from bbox
            return 'L'  # Left
        elif start_pt[0] > cx and end_pt[0] > cx:
            if abs(min(start_pt[0], end_pt[0]) - br_bbox[0]) > max_from_bb_x: return "" # neck of tab/blank is too far from bbox
            return 'R'  # Right
        else:
            print(f"\nfl_core: get_side: ERROR: Cannot determine bbox left or right side for line segment from {start_pt} to {end_pt}.\n") # top or bottom
            sys.exit(1)
    return ""

# Calculate angle in radians between the line from start_point to pt and the horizontal axis.
# Always returns a positive angle between 0 and 2*pi.
def get_angle(pt, start_point):
    a = np.arctan2(pt[1] - start_point[1], pt[0] - start_point[0])
    while a < 0.0:
        a += 2*np.pi
    return a

# Calculate the smallest difference between two angles in radians, accounting for wraparound at 2*pi.
def get_angle_diff(angle1, angle2):
    diff = abs(angle1 - angle2)
    if diff > np.pi:
        diff = abs(2*np.pi - diff)
    return diff

# Get the bounding box from a list of lines. The bounding box is defined by the top-left and bottom-right corners.
# the argument lines is a list of (start_pt, end_pt) where each point is (x,y)
# Returns two values tl_pt and br_pt which are both (x,y) points
def get_bounding_box_from_lines(lines):
    if not lines:
        return None, None

    min_x = min(min(line[0][0], line[1][0]) for line in lines)
    max_x = max(max(line[0][0], line[1][0]) for line in lines)
    min_y = min(min(line[0][1], line[1][1]) for line in lines)
    max_y = max(max(line[0][1], line[1][1]) for line in lines)

    return (min_x, min_y), (max_x, max_y)


def get_bbox_from_points(points):
    """
    Given a list of points, return the bounding box that contains all the points.
    The bounding box is defined by the top-left and bottom-right corners."""
    if not points:
        return None, None

    min_x = min(pt[0] for pt in points)
    max_x = max(pt[0] for pt in points)
    min_y = min(pt[1] for pt in points)
    max_y = max(pt[1] for pt in points)

    return (min_x, min_y), (max_x, max_y)


def find_piece_center(img):
    # Find the coordinates of all white pixels
    white_pixels = np.argwhere(img == 255)
    
    # Calculate the center of mass
    center_x = np.mean(white_pixels[:, 1])
    center_y = np.mean(white_pixels[:, 0])
    
    return int(center_x), int(center_y)

def find_initial_start_point(gray):
    for y in range(gray.shape[0]):
        for x in range(gray.shape[1]):
            if gray[y, x] >= 127:
                return (x, y)
    return None

# Search an ever-expanding circle around the last point, looking for a set pixel.
def find_local_start_point(gray, last_point, size_thresh=100, color_thresh=255):
    # print(f"Searching for local start point around {last_point} with size_thresh {size_thresh} and color_thresh {color_thresh}.")
    x, y = last_point
    for dist in range(1, size_thresh + 1):
        for new_y in range(y - dist, y + dist + 1):
            if new_y in [y - dist, y + dist]:
                for new_x in range(x-dist, x+dist+1):
                    if 0 <= new_x < gray.shape[1] and 0 <= new_y < gray.shape[0]:
                        if gray[new_y, new_x] >= color_thresh:
                            return (new_x, new_y)
            else:
                for new_x in [x - dist, x + dist]:
                    if 0 <= new_x < gray.shape[1] and 0 <= new_y < gray.shape[0]:
                        if gray[new_y, new_x] >= color_thresh:
                            return (new_x, new_y)

    return None


def get_adjacent_points(gray, point, thresh=255):
    x, y = point
    adjacent_points = []
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            new_x = x + dx
            new_y = y + dy
            if new_x >= 0 and new_x < gray.shape[1] and new_y >= 0 and new_y < gray.shape[0]:
                #print(f"Checking adjacent point ({new_x}, {new_y}) with value {gray[new_y][new_x]} against threshold {thresh}.")
                if gray[new_y][new_x] >= thresh:
                    adjacent_points.append((new_x, new_y))
                    # print(f"Added adjacent point ({new_x}, {new_y}) to list.")
    return adjacent_points

# returns 6 color palette and names. Colors are (B:G:R) tuples.
def get_palette(palette_size=6):
    palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    names = ["Blue", "Green", "Red", "Cyan", "Magenta", "Yellow"]
    return (palette[:palette_size], names[:palette_size])

def draw_lines_on_color_image(image, lines, palette, dx=3, thickness=1):
    color_index = 0
    for line in lines:
        (x1, y1), (x2, y2) = line
        cv2.line(image, (int(x1+dx), int(y1)), (int(x2+dx), int(y2)), palette[color_index % len(palette)], thickness=thickness)
        color_index = (color_index + 1) % len(palette)

def draw_poly(image, pts, color=(0,0,255), thickness=4):
        for i,pt in enumerate(pts):
            print(f"{i}  {pt}")
            next_pt = pts[(i+1)%(len(pts))]
            cv2.line(image, (int(pt[0]), int(pt[1])), (int(next_pt[0]),int(next_pt[1])), color, thickness=thickness)

def draw_triangle(image, pt0, pt1, pt2, color=(0, 255, 0), thickness=1):
    cv2.polylines(image, [np.array([[pt0[0], pt0[1]], [pt1[0], pt1[1]], [pt2[0], pt2[1]]], dtype=np.int32)], isClosed=True, color=color, thickness=thickness)   

def show_image(img, str="Image", max=1000, wait_for_key=True):
    x_scale_factor = 1000.0 / img.shape[1]
    y_scale_factor = 1000.0 / img.shape[0]
    scale_factor = min(x_scale_factor, y_scale_factor, 1.0)
    resized_image = cv2.resize(img, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    cv2.imshow(str, resized_image)
    if wait_for_key:
        k = cv2.waitKey(0)
        if k == 27:  # ESC key
            cv2.destroyAllWindows()
            sys.exit(1)

def print_histogram(values, bin_labels):
    scale = max(values)/60
    for i, v in enumerate(values):
        print(f"{bin_labels[i]} {int(values[i] / scale) * '#'}")
