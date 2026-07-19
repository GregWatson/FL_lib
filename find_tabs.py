from fl_core import get_bbox_from_points, get_side_of_tab

import numpy as np

# def find_tabs(lines, bbox, pct_tolerance=10.0):
#     """
#     Tabs are the bits that poke out and interlock with tabs. 
#     They are usually short lines that are close to the bounding box of the piece.
#     Find lines that touch the bounding box within the given tolerance.
#     At least one line end point must be in the center of a bbox side 
#     to within given %age tolerance.
    
#     Args:
#         lines: A list of lines, where each line is specified as its endpoints, e.g. [((x1, y1), (x2, y2)), ...]
#         bbox: The bounding box specified as two points: (tl_corner, br_corner),
#               where tl_corner = (tl_x, tl_y) and br_corner = (br_x, br_y).
#         tolerance: The maximum distance to center to consider a line as being a tab.
        
#     Returns:
#         A list of lines that are likely to be part of piece tabs.
#     """
#     if not lines or bbox is None:
#         return []
        
#     tl, br = bbox
#     tl_x, tl_y = map(int, tl)
#     br_x, br_y = map(int, br)
    
#     def point_is_tab(pt, tl_x, tl_y, br_x, br_y, mid_thresh_pct = pct_tolerance):
#         w = abs(br_x - tl_x)
#         h = abs(br_y - tl_y)
#         x_mid = (br_x + tl_x)/2
#         y_mid = (br_y + tl_y)/2
#         thresh = mid_thresh_pct/100.0 * max(w,h)
#         x,y = pt[0], pt[1]
#         if abs(x-tl_x)<1.0001 and (abs(y - y_mid)<thresh) : return True
#         if abs(x-br_x)<1.0001 and (abs(y - y_mid)<thresh) : return True
#         if abs(y-tl_y)<1.0001 and (abs(x - x_mid)<thresh) : return True
#         if abs(y-br_y)<1.0001 and (abs(x - x_mid)<thresh) : return True
#         return False
    
#     lines_touch_bb = []
    
#     # list of line lengths
#     lls = [ get_distance_between_2_points(line[0], line[1]) for line in lines ]

#     for i, line in enumerate(lines):
#         prev_i = (i - 1) % len(lls)
#         next_i = (i + 1) % len(lls)
#         # If the lines either side of this line are long then this is unlikely to be a tab
#         if max(lls[prev_i], lls[i], lls[next_i]) > 40:
#             continue
#         for pt in line:
#             if point_is_tab(pt, tl_x, tl_y, br_x, br_y):
#                 lines_touch_bb.append(line)
#                 # print(f"Line is tab. Len is {lls[i]}")
#                 break

#     return lines_touch_bb


def tab_points_are_valid(tab_points, tl_bbox, br_bbox):
    """
    Check if the points that define a tab area are valid.
    A tab area is valid if it has at least 5 points and some of the points
    meet the criteria for being a tab.
    
    Args:
        tab_points: List of points defining the tab area.
        tl_bbox: Top-left corner of the bounding box of the piece.
        br_bbox: Bottom-right corner of the bounding box of the piece.
    """
    if len(tab_points) < 7:
        return False

    tl_x, tl_y = map(int, tl_bbox)
    br_x, br_y = map(int, br_bbox)
    w = abs(br_x - tl_x)
    h = abs(br_y - tl_y)
    x_mid = (br_x + tl_x)/2
    y_mid = (br_y + tl_y)/2
    min_dist_from_bb_x = 0.10 * w # A tab is at least 10% away from bbox
    min_dist_from_bb_y = 0.10 * h # A tab is at least 10% away from bbox
    max_dist_from_bb = 0.05 * max(w,h) # The tip of the tab should be no more than 5% away from bbox
    x_thresh = w * 0.3  # A tab cannot be more than 30% away from the center of the piece
    y_thresh = h * 0.3  

    # For a tab, the first and last points should be a reasonable distance away from the bbox.
    for pt in [tab_points[0], tab_points[-1]]:
        x,y = pt[0], pt[1]
        if (abs(y - y_mid) < y_thresh) : # left and right side tabs 
            # print(f"Check ({x},{y}) left and right: tlx:{tl_x}  brx:{br_x}  thresh {min_dist_from_bb_x} )")
            if abs(x-tl_x) < min_dist_from_bb_x or abs(x-br_x) < min_dist_from_bb_x:
                return False
        elif (abs(x - x_mid) < x_thresh) : # top and bottom side tabs
            # print(f"Check ({x},{y}) top and bottom: tly:{tl_y}  bry:{br_y}  thresh {min_dist_from_bb_y} )")
            if abs(y-tl_y) < min_dist_from_bb_y or abs(y-br_y) < min_dist_from_bb_y:
                return False

    # For a tab, at least one of the points should be close to the bbox.
    for pt in tab_points:
        x,y = pt[0], pt[1]
        if (abs(y - y_mid) < y_thresh) : # left and right side tabs 
            if abs(x-tl_x) < max_dist_from_bb or abs(x-br_x) < max_dist_from_bb:
                return True
        elif (abs(x - x_mid) < x_thresh) : # top and bottom side tabs
            if abs(y-tl_y) < max_dist_from_bb or abs(y-br_y) < max_dist_from_bb:
                return True
    return False


def extend_keepout(keepout, side, tl_bbox, br_bbox, margin=10):
    """ 
    Extend the keep_out to the actual bbox of the piece, as well as a margin. 
    This is to ensure that the keepout area is large enough to cover the tab area.
    Args:
        keepout: The keepout area to extend, specified as a bounding box (tl_corner, br_corner).
        side: The side of the piece where the keepout area is located (L, R, T, B).
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
    if side == 'T':
        extended_tl_x = keepout_tl_x - margin
        extended_tl_y = tl_y
        extended_br_x = keepout_br_x + margin
        extended_br_y = keepout_br_y + margin
    # if bottom of piece ...
    elif side == 'B':
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

def no_hit_with_blank_keepouts(keepout, blank_keep_outs):
    """
    Check if the given keepout area overlaps with any of the blank keepouts.
    Args:
        keepout: The keepout area to check, specified as a bounding box (tl_corner, br_corner).
        blank_keep_outs: List of bounding boxes for blank areas.
    Returns:
        True if there is no overlap with any blank keepout, False otherwise.
    """
    if keepout is None:
        return True

    (keepout_tl_x, keepout_tl_y), (keepout_br_x, keepout_br_y) = keepout

    for (blank_tl, blank_br) in blank_keep_outs:
        blank_tl_x, blank_tl_y = map(int, blank_tl)
        blank_br_x, blank_br_y = map(int, blank_br)

        # Check for overlap
        if not (keepout_br_x < blank_tl_x or keepout_tl_x > blank_br_x or
                keepout_br_y < blank_tl_y or keepout_tl_y > blank_br_y):
            return False  # There is an overlap

    return True  # No overlaps found


def find_tab_areas(poly_points, outer_angles, tl_bbox, br_bbox, blank_keep_outs, debug=False):
    """
    Given a polygon and its outer angles, find areas that are likely to be tabs.
    A tab is the 'socket' in a piece that a tab slots into.
    A tab must have lines where the outer angle is greater than 180 degrees (pi radians).
    (But an outer angle > 180 does not guarantee a tab, as it could be another feature)
    This function returns a list of bounding boxes for each tab area found.

    Also, a tab area cannot overlap with a blank area, so the blank areas are passed in as an argument.
    (Blanks are easier to reliably detect than tabs)
    
    Args:
        poly_points: List of points defining the polygon.
        outer_angles: List of outer angles corresponding to each point in poly_points.
        tl_bbox: Top-left corner of the bounding box of the piece.
        br_bbox: Bottom-right corner of the bounding box of the piece.
        blank_keep_outs: List of bounding boxes for blank areas.
        debug: If True, print debug information.
    """
    tab_areas = []
    n = len(poly_points)

    # Find the first point where the outer angle is < than 180 degrees so that we can start 
    # looking for tabs from there. This is to avoid starting in the middle of a tab area.
    p = 0
    while p < n and outer_angles[p] > np.pi:
        p += 1
    if p == n: return []

    tab_points = []
    for _ in range(n):
        # print(f"{p} has outer angle {outer_angles[p]}")
        angle_thresh = np.pi
        if len(tab_points): angle_thresh = 0.9*np.pi
        if outer_angles[p] < angle_thresh:
            if len(tab_points) > 0:
                tab_points.append(poly_points[p]) # extend one more point to ensure that the keepout area is large enough to cover the tab area.
                # print(f"**** Checking {len(tab_points)} Tab points ending at index {p}")
                if tab_points_are_valid(tab_points, tl_bbox, br_bbox):
                    print(f"Checking Tab bbox of {len(tab_points)} points. Indexes: {p-len(tab_points)+1} -> {p}")

                    keepout = get_bbox_from_points(tab_points)
                    side = get_side_of_tab(tab_points[0], tab_points[-1], tl_bbox, br_bbox) # L,R,T,B(ottom)
                    if side != "":
                        keepout = extend_keepout(keepout, side, tl_bbox, br_bbox)
                        if no_hit_with_blank_keepouts(keepout, blank_keep_outs):
                            tab_areas.append(keepout)

                tab_points = []
            p = (p+1) % n
            continue

        # add one extra point either side of the tab area to ensure that the keepout area is large enough to cover the tab area.
        if len(tab_points) == 0:
            prev_p = (p - 1) % n
            tab_points.append(poly_points[prev_p])
        tab_points.append(poly_points[p])
        p = (p+1) % n

    # catch residual tab points if the last point was part of a tab area
    if len(tab_points) > 0:
        tab_points.append(poly_points[p])
        start_index = p-len(tab_points)+1
        if start_index < 0: start_index += n
        # print(f"Residual Checking Tab bbox of {len(tab_points)} points. Indexes: {start_index} -> {p}")
        if tab_points_are_valid(tab_points, tl_bbox, br_bbox):
            keepout = get_bbox_from_points(tab_points)
            side = get_side_of_tab(tab_points[0], tab_points[-1], tl_bbox, br_bbox) # L,R,T,B(ottom)
            if side != "":
                keepout = extend_keepout(keepout, side, tl_bbox, br_bbox)
                if no_hit_with_blank_keepouts(keepout, blank_keep_outs):
                    tab_areas.append(keepout)
    # print(f"Returning {len(tab_areas)} tab areas.")
    return tab_areas
