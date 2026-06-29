from fl_core import get_distance_between_2_points

def find_blank_lines(lines, bbox, center_pt, pct_tolerance=10.0):
    """
    Find lines that form part of the blanks inside a piece.
    (A blank is the 'socket' in a piece that a tab slots into)
    At least one line end point must be near the center of the piece to within given %age tolerance.
    
    Args:
        lines: A list of lines, where each line is specified as its endpoints, e.g. [((x1, y1), (x2, y2)), ...]
        bbox: The bounding box specified as two points: (tl_corner, br_corner),
              where tl_corner = (tl_x, tl_y) and br_corner = (br_x, br_y).
        center_pt: (cx,cy) center of image
        tolerance: The maximum distance to center to consider a line as being a tab.
        
    Returns:
        A list of lines that are likely to be part of piece tabs.
    """
    if not lines or bbox is None:
        return []
        
    tl, br = bbox
    tl_x, tl_y = map(int, tl)
    br_x, br_y = map(int, br)
    cx, cy = center_pt
    
    def point_is_blank(pt, tl_x, tl_y, br_x, br_y):
        w = abs(br_x - tl_x)
        h = abs(br_y - tl_y)
        x_mid = (br_x + tl_x)/2
        y_mid = (br_y + tl_y)/2
        min_dist_from_bb = 0.05 * max(w,h)
        x_thresh = w * 0.3
        y_thresh = h * 0.3
        x,y = pt[0], pt[1]
        if abs(x-tl_x)<min_dist_from_bb and (abs(y - y_mid)<y_thresh) : return False
        if abs(x-br_x)<min_dist_from_bb and (abs(y - y_mid)<y_thresh) : return False
        if abs(y-tl_y)<min_dist_from_bb and (abs(x - x_mid)<x_thresh) : return False
        if abs(y-br_y)<min_dist_from_bb and (abs(x - x_mid)<x_thresh) : return False
        return True
    
    lines_might_be_blank = []
    
    # list of line lengths
    lls = [ get_distance_between_2_points(line[0], line[1]) for line in lines ]

    # get distance of line ends from center
    l_dist_from_center = [ min(get_distance_between_2_points(line[0], center_pt), get_distance_between_2_points(line[1], center_pt))  for line in lines]

    min_dist = min(l_dist_from_center)

    for i, line in enumerate(lines):
        prev_i = (i - 1) % len(lls)
        next_i = (i + 1) % len(lls)
        # If the lines either side of this line are long then this is unlikely to be a blank
        if max(lls[prev_i], lls[i], lls[next_i]) > 40:
            continue
        if l_dist_from_center[i] > 1.5 * min_dist:
            continue
        for pt in line:
            if point_is_blank(pt, tl_x, tl_y, br_x, br_y):
                lines_might_be_blank.append(line)
                break

    return lines_might_be_blank

