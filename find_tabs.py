from fl_core import get_distance_between_2_points

def find_tabs(lines, bbox, pct_tolerance=10.0):
    """
    Find lines that touch the bounding box within the given tolerance.
    At least one line end point must be in the center of a bbox side 
    to within given %age tolerance.
    
    Args:
        lines: A list of lines, where each line is specified as its endpoints, e.g. [((x1, y1), (x2, y2)), ...]
        bbox: The bounding box specified as two points: (tl_corner, br_corner),
              where tl_corner = (tl_x, tl_y) and br_corner = (br_x, br_y).
        tolerance: The maximum distance to center to consider a line as being a tab.
        
    Returns:
        A list of lines that are likely to be part of piece tabs.
    """
    if not lines or bbox is None:
        return []
        
    tl, br = bbox
    tl_x, tl_y = map(int, tl)
    br_x, br_y = map(int, br)
    
    def point_is_tab(pt, tl_x, tl_y, br_x, br_y, mid_thresh_pct = pct_tolerance):
        w = abs(br_x - tl_x)
        h = abs(br_y - tl_y)
        x_mid = (br_x + tl_x)/2
        y_mid = (br_y + tl_y)/2
        thresh = mid_thresh_pct/100.0 * max(w,h)
        x,y = pt[0], pt[1]
        if abs(x-tl_x)<1.0001 and (abs(y - y_mid)<thresh) : return True
        if abs(x-br_x)<1.0001 and (abs(y - y_mid)<thresh) : return True
        if abs(y-tl_y)<1.0001 and (abs(x - x_mid)<thresh) : return True
        if abs(y-br_y)<1.0001 and (abs(x - x_mid)<thresh) : return True
        return False
    
    lines_touch_bb = []
    
    # list of lene lengths
    lls = [ get_distance_between_2_points(line[0], line[1]) for line in lines ]

    for i, line in enumerate(lines):
        prev_i = (i - 1) % len(lls)
        next_i = (i + 1) % len(lls)
        # If the lines either side of this line are long then this is unlikely to be a tab
        if max(lls[prev_i], lls[i], lls[next_i]) > 40:
            continue
        for pt in line:
            if point_is_tab(pt, tl_x, tl_y, br_x, br_y):
                lines_touch_bb.append(line)
                print(f"Line is tab. Len is {lls[i]}")
                break

    return lines_touch_bb

