import numpy as np
from fl_core import get_distance_between_2_points
from polygon_angles import get_polygon_outer_angles
from find_blanks import find_blank_areas
from find_tabs import find_tab_areas
import cv2

# Given a list of lines that form the edges of a piece, try to find
# the corners of a piece.
# This is a simplified approach that assumes the corners are where lines meet
# at a "significant" angle (e.g. 90 degrees).
# Params:
# - lines_found: list of lines, where each line is represented as a tuple of start and end points.
#   The lines form the outline of the piece in clockwise order. The end point of a line might not 
#   be the same as the start point of the next line. If they are close then we treat them as the same, 
#   but if they are more than a threshold distance apart then we ignore the gap and don't consider
#   them as connected (cannot be a corner).
#   NOTE: The lines should have been extracted from an image that has already been rotated
#         such that straight lines tend to be horizontal or vertical.
# - corner_thresh: minimum angle difference in degrees to consider a corner (e.g. 50 degrees)
# - tl_bbox: top left corner of the bounding box of the piece (x,y)
# - br_bbox: bottom right corner of the bounding box of the piece (x,y)
# - end_to_end_dist_thresh: maximum distance between the end of one line and the 
#   start of the next line to consider them connected (e.g. 20 pixels)
# 
# Returns a list of 4 corners in [row][column] format, where each corner is represented as a tuple of (corner_x, point, angle_diff).
#   The order of the corners should be [top-left, top-right,bottom-left,bottom-right].
# - corner_x is a value that represents how "corner-like" this corner is, which is a function of the 
#   angle difference and the lengths of the lines. We can use this to sort the corners and only keep the most "corner-like" corners.
# - point is the (int(x), int(y)) point of the corner (e.g. the end of line1 or the start of line2, or we could compute an intersection point 
#   if we want to be more precise)
# - angle_diff is the EXTERNAL angle in radians between the two lines that form this corner, which can be useful for 
#   debugging and for further filtering of corners if needed.

# Compute a corner-ish function to evaluate how "corner-like" each potential corner is
# This function will be used to sort the corners and select the most "corner-like" ones.
# The angle is the EXTERNAL angle (of a polygon) between the two lines that form the corner.
def cornerness_function(pt0, pt1, pt2, angle, rel_d_to_c, keep_outs, debug=False):

    # return 1 if point falls in the corner keep-out zones, otherwise return 0. 
    def get_keep_out_effect(pt, keep_outs):
        x,y = pt
        for (xmin, ymin), (xmax, ymax) in keep_outs:
            if x > xmin and x <= xmax and y > ymin and y <= ymax: return 1
        return 0

    l1 = get_distance_between_2_points(pt0, pt1)
    l2 = get_distance_between_2_points(pt1, pt2)
    if abs(angle) < np.pi: # if the angle is very small, it's not a corner
        corner_ness = 0
    else:
        # angle_effect = 10.0/(abs(np.pi*1.5 - abs(angle))) # the less the angle deviates from 270 degrees, the more corner-like it is
        angle_effect = 20-20**(abs(np.pi*1.5 - abs(angle))) # the less the angle deviates from 270 degrees, the more corner-like it is
        length_effect = (l1 + l2)/2 # longer lines should contribute to more corner-ness, but we can take the average to avoid giving too much weight to one long line and one short line
        #dist_to_corner_effect = 5.0 * (30 - 30**rel_d_to_c) # the closer to the corner of the image, the more likely it is to be a real corner of the piece rather than noise in the middle
        dist_to_corner_effect = 100 * (5 ** (-rel_d_to_c)) # the closer to the corner of the image, the more likely it is to be a real corner of the piece rather than noise in the middle
        keep_out_effect = 0
        if keep_outs:
            keep_out_effect = 100 * get_keep_out_effect(pt1, keep_outs) 

        corner_ness = angle_effect + length_effect + dist_to_corner_effect - keep_out_effect

        if debug:
            print(f"At {int(pt1[0])},{int(pt1[1])}: angle={int(np.degrees(angle))}, lens={int(l1)}, {int(l2)}. d2c= {rel_d_to_c:.2f} ", end=' ')
            print(f"angle_effect = {angle_effect:.3f}, length_effect = {length_effect:.3f}, ", end='')
            print(f"dist_to_corner_effect = {dist_to_corner_effect:.3f}, keep_out_effect={keep_out_effect:.3f}", end=' ')
            print(f" ===> Corner_ness = {corner_ness:.2f}", end=' ')
    return corner_ness

def get_rel_shortest_distance_to_corner (pt, w,h, half_diag):
    corners = [(0,0), (w,0), (w,h), (0,h)]
    m = min([get_distance_between_2_points(pt, corner) for corner in corners])
    return m/half_diag

# Given an ordered set of lines that form the outline of a piece, return a polygon
# that represents the entire piece. If the end of one line is close to the start of 
# the next line, we consider them connected and we change the points to be the average 
# of the two points.
def get_polygon_from_lines(lines, end_to_end_dist_thresh=20):
    polygon = []
    for i in range(len(lines)):
        line1 = lines[i]
        line2 = lines[(i + 1) % len(lines)]
        end1 = line1[1]
        start2 = line2[0]
        distance = get_distance_between_2_points(end1, start2)
        if distance <= end_to_end_dist_thresh:
            avg_x = int((end1[0] + start2[0]) / 2)
            avg_y = int((end1[1] + start2[1]) / 2)
            polygon.append([avg_x, avg_y])
        else:
            polygon.append([int(end1[0]), int(end1[1])])
            polygon.append([int(start2[0]), int(start2[1])])
    return polygon

# Compute keep-out zones where corners are unlikely to be found due to the presence of tabs or blanks.
# Return xmin, xmax, ymin, ymax for each keep-out zone.
def get_keep_outs(poly_points, outer_angles, tl_bbox, br_bbox, debug=False):
    blank_keep_outs = find_blank_areas(poly_points, outer_angles, tl_bbox, br_bbox, debug=debug)
    tab_keep_outs = find_tab_areas(poly_points, outer_angles, tl_bbox, br_bbox, blank_keep_outs, debug=debug)
    return blank_keep_outs, tab_keep_outs

def find_approx_corners(lines_found, tl_bbox=None, br_bbox=None, end_to_end_dist_thresh=20, debug=False):
    corners = []
    if not len(lines_found):
        return corners

    # First, create a fully closed polygon from the lines. If the end of one line is close to the start of 
    # the next line, we consider them connected and we change the points to be the average of the two points.
    # If they are too far apart then we introduce a fake line to just close the polygon but will 
    # not be used in the corner detection.

    if tl_bbox is None or br_bbox is None:
        # compute the bounding box of the lines to get the top left and bottom right corners of the piece.
        tl_bbox = (min([min(line[0][0], line[1][0]) for line in lines_found]), min([min(line[0][1], line[1][1]) for line in lines_found]))
        br_bbox = (max([max(line[0][0], line[1][0]) for line in lines_found]), max([max(line[0][1], line[1][1]) for line in lines_found]))

    polygon = get_polygon_from_lines(lines_found, end_to_end_dist_thresh)

    poly_points = np.array(polygon, dtype=np.int32)
    outer_angles = get_polygon_outer_angles(poly_points)

    if debug:
        for i, outer_angle in enumerate(outer_angles):
            print(f"Vertex {i}: point={int(poly_points[i][0])},{int(poly_points[i][1])}, inner angle={int(np.degrees(2*np.pi - outer_angle))}, outer angle={int(np.degrees(outer_angle))}")
    
    bb_w = br_bbox[0] - tl_bbox[0]
    bb_h = br_bbox[1] - tl_bbox[1]
    half_diag = np.sqrt(bb_w**2 + bb_h**2) / 2


    # Compute keep-out areas that cannot be corners due to them being blanks or tabs.
    # We will use this to reduce the corner-ness of corners that are near these areas.
    blank_keep_outs, tab_keep_outs = get_keep_outs(poly_points, outer_angles, tl_bbox, br_bbox, debug=debug)
    keep_outs = blank_keep_outs + tab_keep_outs

    # debug by displaying an image with points joined by arrows in order
    if debug and len(polygon) > 2:
        SIZE = 500
        img = np.zeros((SIZE, SIZE,3), dtype=np.uint8)
        for i, point in enumerate(polygon):
            cv2.arrowedLine(img, (point[0], point[1]), (polygon[(i + 1) % len(polygon)][0], polygon[(i + 1) % len(polygon)][1]), (0, 150, 0), 1)
            cv2.putText(img, f"{i}", (point[0], point[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        # add keepouts
        for (xmin, ymin), (xmax, ymax) in blank_keep_outs:
            cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
        for (xmin, ymin), (xmax, ymax) in tab_keep_outs:
            cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)
        cv2.imshow(f"Polygon ordering", img)
        # cv2.waitKey(0)


    for i, outer_angle in enumerate(outer_angles):
        pt0 = poly_points[(i - 1) % len(poly_points)]
        pt1 = poly_points[i]
        pt2 = poly_points[(i + 1) % len(poly_points)]
        if debug: print(f"Corner {i}:", end='')
        rel_d_to_c = get_rel_shortest_distance_to_corner((pt1[0]-tl_bbox[0], pt1[1]-tl_bbox[1]), bb_w, bb_h, half_diag) 
        #print(f"Distance to closest image corner: {int(d_to_c)}")
        cornerness_value = cornerness_function(pt0, pt1, pt2, outer_angle, rel_d_to_c, keep_outs=keep_outs, debug=debug) # outer angle
        # Store the corner information
        corners.append((cornerness_value, pt1, outer_angle)) # store the corner-ness value, the point, and the angle difference
        if debug:
            print("")
    # Sort the corners by their "corner-ness" (cornerness_value) in descending order
    corners.sort(key=lambda x: x[0], reverse=True)

    # Only have one corner per quadrant, and only keep corners that are above a certain threshold of "corner-ness" (e.g. corner_x > 0.5)
    final_corners = [[False, False],[False,False]] # by row then column
    # compute the quadrant of each corner relative to the center of the piece, and only keep the most "corner-like" corner in each quadrant.
    quandrant_used= [[False, False],[False,False]]
    # get center
    center_x = np.mean([point[0] for _, point, _ in corners])
    center_y = np.mean([point[1] for _, point, _ in corners])
    for corner in corners:
        ness,point,rotation_angle = corner
        # print(f"Evaluating corner with point={point}")
        quad_x = 0 if point[0] < center_x else 1
        quad_y = 0 if point[1] < center_y else 1
        if not quandrant_used[quad_y][quad_x] :
            final_corners[quad_y][quad_x] = corner
            quandrant_used[quad_y][quad_x] = True
            if debug:
                print(f"Adding corner at point {point}. Corner-ness: {ness:.2f} and angle difference {np.degrees(rotation_angle):.2f} degrees to final corners.")

    return final_corners, blank_keep_outs, tab_keep_outs

# Helper function
# Calculate all the pixel positions that form the edge of a box centered 
# at pointXY with edge length box_len, and that lie within a bounding box
# 0 <= x < maxX, 0 <= y < maxY
def get_box_pixel_list(pointXY, box_len, maxX, maxY):
    half_len = box_len // 2
    x_min = pointXY[0] - half_len
    x_max = pointXY[0] + half_len 
    y_min = pointXY[1] - half_len
    y_max = pointXY[1] + half_len
    pixels = []
    if y_min >= 0:
        for x in range(x_min, x_max + 1):
            if x >=0 and x < maxX:  pixels.append((x, y_min))
    if y_max < maxY:
        for x in range(x_min, x_max + 1):
            if x >=0 and x < maxX:  pixels.append((x, y_max))
    if x_min >= 0:
        for y in range(y_min + 1, y_max):
            if y >= 0 and y < maxY:  pixels.append((x_min, y))
    if x_max < maxX:
        for y in range(y_min + 1, y_max):
            if y >= 0 and y < maxY:  pixels.append((x_max, y))
    #print(f"Box len {box_len}: ",end='')
    #for p in pixels: print(f"({p[0]},{p[1]}) ", end='')
    # print("")
    return pixels

# Helper function for find_better_corners.
# Given an initial pixel location pointXY, search the image by scanning
# pixels starting at pointXY and moving outwards.
# Two phases:
# 1: Find a pixel close to pointXY that is set (not black). Call this startXY
# 2: Expand outwards from startXY until we have an expansion that doesnt find 
#    any pixels set. Then return pixel that was set and closest to img_corner.
def find_better_corner(image, pointXY, img_corner):
    min_white = 128 # pixel value to be a set pixel
    #print(f"find_better_corner: Initial Pixel at ({pointXY[0]},{pointXY[1]}) is {image[pointXY[1], pointXY[0]]}. img_corner is ({img_corner[0]},{img_corner[1]})")
    startXY = (pointXY[0], pointXY[1])
    if image[startXY[1],startXY[0]] < min_white:
        # Phase 1 is needed
        # Look at each pixel that forms the edge of a box centered at pointXY and 
        # with length box_len. box_len goes up in increments of 2.
        box_len = 3
        max_box_len = 15 # If we dont find a set pixel within this size box then something's wrong.
        done = False
        while not done:
            poss_pixels = get_box_pixel_list(pointXY, box_len, image.shape[1], image.shape[0])
            for p in poss_pixels:
                if image[p[1], p[0]] >= min_white:
                    startXY = p
                    done = True
                    break
            if not done:
                box_len += 2
                if box_len > max_box_len:
                    done = True
        assert box_len <= max_box_len, "Failed to find a set pixel within the maximum box size"
    #print(f"Actual startXY is ({startXY[0]},{startXY[1]})")

    # Phase 2
    best_corner = startXY
    best_distance = (startXY[0] - img_corner[0]) ** 2 + (startXY[1] - img_corner[1]) ** 2
    box_len = 3
    max_box_len = max(abs(startXY[0] - img_corner[0]), 3)
    
    while True:
        poss_pixels = get_box_pixel_list(startXY, box_len, image.shape[1], image.shape[0])
        found = False
        for p in poss_pixels:
            if image[p[1], p[0]] >= min_white:
                distance = (p[0] - img_corner[0]) ** 2 + (p[1] - img_corner[1]) ** 2
                if distance < best_distance:
                    found = True
                    best_distance = distance
                    best_corner = p
                    #print(f"  New best corner: ({best_corner[0]},{best_corner[1]}) with distance {best_distance}")
        if not found:
            break
        box_len += 2
    assert box_len <= max_box_len, "Failed to find a set pixel within the maximum box size of {}".format(max_box_len)
    # print(f"Better corner: Start ({startXY[0]},{startXY[1]}) -> ({best_corner[0]},{best_corner[1]})")
    return best_corner

# Given a pixel location close to the real corner, try to find the real corner
# by looking at the actual edge image to find the pixel closest to the image corner.
# Param corners is [[TL, TR], [BL, BR]].
def find_better_corners(image, corners):
    new_corners = []
    width = image.shape[1]
    height = image.shape[0]
    for ix, corner_point in enumerate([ col for row in corners for col in row if col]):
            cornerness, pointXY, angle = corner_point
            img_corner = ((ix % 2) * width, (ix >> 1) * height)
            better_corner = find_better_corner(image, pointXY, img_corner)
            new_corners.append((cornerness, better_corner, angle))
    
    return [new_corners[0:2], new_corners[2:4]]