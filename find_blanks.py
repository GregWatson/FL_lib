from fl_core import get_bbox_from_points, get_side_of_blank
import numpy as np

# def find_blank_lines(lines, bbox, center_pt, pct_tolerance=10.0):
#     """
#     Find lines that form part of the blanks inside a piece.
#     (A blank is the 'socket' in a piece that a tab slots into)
#     At least one line end point must be near the center of the piece to within given %age tolerance.
    
#     Args:
#         lines: A list of lines, where each line is specified as its endpoints, e.g. [((x1, y1), (x2, y2)), ...]
#         bbox: The bounding box specified as two points: (tl_corner, br_corner),
#               where tl_corner = (tl_x, tl_y) and br_corner = (br_x, br_y).
#         center_pt: (cx,cy) center of image
#         tolerance: The maximum distance to center to consider a line as being a tab.
        
#     Returns:
#         A list of lines that are likely to be part of piece tabs.
#     """
#     if not lines or bbox is None:
#         return []
        
#     tl, br = bbox
#     tl_x, tl_y = map(int, tl)
#     br_x, br_y = map(int, br)
    
#     def point_is_blank(pt, tl_x, tl_y, br_x, br_y):
#         w = abs(br_x - tl_x)
#         h = abs(br_y - tl_y)
#         x_mid = (br_x + tl_x)/2
#         y_mid = (br_y + tl_y)/2
#         min_dist_from_bb = 0.05 * max(w,h)
#         x_thresh = w * 0.3
#         y_thresh = h * 0.3
#         x,y = pt[0], pt[1]
#         if abs(x-tl_x)<min_dist_from_bb and (abs(y - y_mid)<y_thresh) : return False
#         if abs(x-br_x)<min_dist_from_bb and (abs(y - y_mid)<y_thresh) : return False
#         if abs(y-tl_y)<min_dist_from_bb and (abs(x - x_mid)<x_thresh) : return False
#         if abs(y-br_y)<min_dist_from_bb and (abs(x - x_mid)<x_thresh) : return False
#         return True
    
#     lines_might_be_blank = []
    
#     # list of line lengths
#     lls = [ get_distance_between_2_points(line[0], line[1]) for line in lines ]

#     # get distance of line ends from center
#     l_dist_from_center = [ min(get_distance_between_2_points(line[0], center_pt), get_distance_between_2_points(line[1], center_pt))  for line in lines]

#     min_dist = min(l_dist_from_center)

#     # find points that are likely to be part of a blank. A line is likely to be part of a blank if:
#     # - it is short (i.e. not a long edge of the piece)
#     # - it is close to the center of the piece (i.e. not on the edge of the piece)
#     # - at least one of its endpoints is not too close to the bounding box (i.e. not on the edge of the piece)

#     for i, line in enumerate(lines):
#         prev_i = (i - 1) % len(lls)
#         next_i = (i + 1) % len(lls)
#         # If the lines either side of this line are long then this is unlikely to be a blank
#         if max(lls[prev_i], lls[i], lls[next_i]) > 40:
#             continue
#         if l_dist_from_center[i] > 1.5 * min_dist:
#             continue
#         for pt in line:
#             if point_is_blank(pt, tl_x, tl_y, br_x, br_y):
#                 lines_might_be_blank.append(line)
#                 break

#     return lines_might_be_blank

def blank_points_are_valid(blank_points, tl_bbox, br_bbox):
    """
    Check if the points that define a blank area are valid.
    A blank area is valid if it has at least 5 points and some of the points
    meet the criteria for being a blank.
    
    Args:
        blank_points: List of points defining the blank area.
        tl_bbox: Top-left corner of the bounding box of the piece.
        br_bbox: Bottom-right corner of the bounding box of the piece.
    """
    if len(blank_points) < 7:
        return False

    tl_x, tl_y = map(int, tl_bbox)
    br_x, br_y = map(int, br_bbox)
    w = abs(br_x - tl_x)
    h = abs(br_y - tl_y)
    x_mid = (br_x + tl_x)/2
    y_mid = (br_y + tl_y)/2
    min_dist_from_bb = 0.1 * max(w,h) # A blank is at least 10% away from bbox
    x_thresh = w * 0.3  # A blank cannot be more than 30% away from the center of the piece
    y_thresh = h * 0.3  

    for pt in blank_points:
        x,y = pt[0], pt[1]
        if (abs(y - y_mid) < y_thresh) : # halfway down the piece
            if abs(x-tl_x) > min_dist_from_bb and abs(x-br_x) > min_dist_from_bb:
                return True
        elif (abs(x - x_mid) < x_thresh) : # halfway across the piece
            if abs(y-tl_y) > min_dist_from_bb and abs(y-br_y) > min_dist_from_bb:
                return True
    return False

def extend_keepout(keepout, side, tl_bbox, br_bbox, margin=10):
    """ 
    Extend the keep_out to the actual bbox of the piece
    Args:
        keepout: The keepout area to extend, specified as a bounding box (tl_corner, br_corner).
        side: The side of the piece to which the keepout area belongs. (L,R,T,B)
        tl_bbox: Top-left corner of the bounding box of the piece.
        br_bbox: Bottom-right corner of the bounding box of the piece.
        margin: The margin to extend the keepout area.
    """
    if keepout is None:
        return [(0,0,0,0)]

    (keepout_tl_x, keepout_tl_y), (keepout_br_x, keepout_br_y) = keepout
    tl_x, tl_y = map(int, tl_bbox)
    br_x, br_y = map(int, br_bbox)

    # if top of piece ...
    if side == 'T' :
        extended_tl_x = keepout_tl_x - margin
        extended_tl_y = tl_y
        extended_br_x = keepout_br_x + margin
        extended_br_y = keepout_br_y + margin
    # if bottom of piece ...
    elif side == 'B' :
        extended_tl_x = keepout_tl_x - margin
        extended_tl_y = keepout_tl_y - margin
        extended_br_x = keepout_br_x + margin
        extended_br_y = br_y
    # if left of piece ...
    elif side == 'L':
        extended_tl_x = tl_x
        extended_tl_y = keepout_tl_y - margin
        extended_br_x = keepout_br_x + margin
        extended_br_y = keepout_br_y + margin
    # if right of piece ...
    elif side == 'R':
        extended_tl_x = keepout_tl_x - margin
        extended_tl_y = keepout_tl_y - margin
        extended_br_x = br_x
        extended_br_y = keepout_br_y + margin
    else:
        # If the keepout area is not clearly on one side of the piece, return the original keepout area.
        extended_tl_x = keepout_tl_x
        extended_tl_y = keepout_tl_y
        extended_br_x = keepout_br_x
        extended_br_y = keepout_br_y    

    return (extended_tl_x, extended_tl_y), (extended_br_x, extended_br_y)

def find_blank_areas(poly_points, outer_angles, tl_bbox, br_bbox, debug=False):
    """
    Given a polygon and its outer angles, find areas that are likely to be blanks.
    A blank is the 'socket' in a piece that a tab slots into.
    A blank must have lines where the outer angle is less than 180 degrees (pi radians).
    (But an outer angle < 180 does not guarantee a blank, as it could be another feature)
    This function returns a list of bounding boxes for each blank area found.
    
    Args:
        poly_points: List of points defining the polygon.
        outer_angles: List of outer angles corresponding to each point in poly_points.
        tl_bbox: Top-left corner of the bounding box of the piece.
        br_bbox: Bottom-right corner of the bounding box of the piece.
        debug: If True, print debug information.
    """
    blank_areas = []
    n = len(poly_points)

    # Find the first point where the outer angle is > than 180 degrees so that we can start 
    # looking for blanks from there. This is to avoid starting in the middle of a blank area.
    p = 0
    while p < n and outer_angles[p] < 1.2 * np.pi:
        p += 1
    if p == n: return []

    blank_points = []
    for _ in range(n):
        # if we are in a concave section then allow for angle to slightly exceed 180
        # print(f"Point {p}  angle {outer_angles[p]:.3f}")
        angle_thresh = np.pi
        if len(blank_points): angle_thresh = 1.1*np.pi
        if outer_angles[p] >= angle_thresh:
            if len(blank_points) > 0:
                blank_points.append(poly_points[p]) # extend one more point to ensure that the keepout area is large enough to cover the blank area.
                if blank_points_are_valid(blank_points, tl_bbox, br_bbox):
                    #print(f"Checking blank bbox of {len(blank_points)} points. Indexes: {p-len(blank_points)+1} -> {p}")
                    keepout = get_bbox_from_points(blank_points)
                    side = get_side_of_blank(blank_points[0], blank_points[-1], tl_bbox, br_bbox) # L,R,T,B(ottom)
                    if side != "":
                        #print(f" Blank: Side is {side}.")
                        keepout = extend_keepout(keepout, side, tl_bbox, br_bbox)
                        blank_areas.append(keepout)
                    else:
                        if debug: print(f"Unable to get side")
                blank_points = []
            p = (p+1) % n
            continue

        if len(blank_points) == 0:
            # If this is the first point in a blank area, add the previous point as well to ensure that the keepout area is large enough to cover the blank area.
            prev_p = (p-1) % n
            blank_points.append(poly_points[prev_p])

        blank_points.append(poly_points[p])
        p = (p+1) % n

    # catch residual blank points if the last point was part of a blank area
    if len(blank_points) > 0:
        blank_points.append(poly_points[p])
        if blank_points_are_valid(blank_points, tl_bbox, br_bbox):
            keepout = get_bbox_from_points(blank_points)
            side = get_side_of_blank(blank_points[0], blank_points[-1], tl_bbox, br_bbox) # L,R,T,B(ottom)
            if side: 
                keepout = extend_keepout(keepout, side, tl_bbox, br_bbox)
                keepout = extend_keepout(keepout, side, tl_bbox, br_bbox)
                blank_areas.append(keepout)

    return blank_areas