from fl_core import point_to_infinite_line_distance, get_adjacent_points, get_distance_between_2_points
from fl_types import SideType, P_Triangle, PieceType    

# Returns the triangles for each edge.
# A triangle is [ 3 points] - formed from the two corners of the side and the point furthest away from the line 
# formed between the two corners.
# If it's a straight line (Edge) then it just returns [ 2 points ] (the corners)
# For each triangle it also returns the edge type (EDGE, TAB, or BLANK)

# Params:
# img: a cv2 image that has only the edges of the piece.
# 
# corners: a list of 4 corners in [row][column] format, where each corner is represented as a tuple of (corner_x, point, angle_diff) where:
# - corner_x is a value that represents how "corner-like" this corner is, which is a function of the 
#   angle difference and the lengths of the lines. We can use this to sort the corners and only keep the most "corner-like" corners.
# - point is the (int(x), int(y)) point of the corner (e.g. the end of line1 or the start of line2, or we could compute an intersection point 
#   if we want to be more precise)
# - angle_diff is the EXTERNAL angle in radians between the two lines that form this corner, which can be useful for 
#   debugging and for further filtering of corners if needed.
#
# NOTE: corners might not be part of a line.

def find_triangles_from_corners(img, corners, debug=False):

    img_w, img_h = img.shape[1], img.shape[0]
    cx = img_w // 2 # center
    cy = img_h // 2

    # (side_name, corner1, corner2, side_midpoint, side_normal)
    sides = [ ('N', corners[0][0][1], corners[0][1][1], (cx, 0), (0,1)),
              ('E', corners[0][1][1], corners[1][1][1], (img_w-1, cy), (-1,0)),
              ('S', corners[1][0][1], corners[1][1][1], (cx, img_h-1), (0,-1)),
              ('W', corners[0][0][1], corners[1][0][1], (0, cy), (1,0)) ]

    # num_to_check: number of points to check starting from the midpoint of the side and moving outwards.
    def find_furthest_point_for_side(img, side, thresh=20, num_to_check=100, min_distance=20):
        # Thresh is grey level. If a pixel is darker than this value, it is ignored.
        side_name, corner1, corner2, side_midpoint, side_normal = side
        img_w, img_h = img.shape[1], img.shape[0]
        min_dist_from_corner = min(img_h, img_w)//10
        tab_min_dist_from_edge = min(img_h, img_w)//20

        # print(f"Process side {side_name} with midpoint {side_midpoint} ")
        # Note: could optimize performance by precomputing coefficients A, B, and C in the line 
        # equation Ax + By + C = 0 for the line defined by corner1 and corner2, and then use those 
        # coefficients to compute the distance from each point to the line. But for now, we'll just 
        # use the point_to_infinite_line_distance function.

        # First start at the line midpoint and head in the direction of the normal to the side, until we find 
        # a pixel that is on (piece contour). Then follow the contour in both directions to find maxima and minima.
        
        sx,sy = side_midpoint
        while sx >= 0 and sx < img_w and sy >= 0 and sy < img_h and img[sy][sx] < thresh:
            sx += side_normal[0]
            sy += side_normal[1]
        max_dist = point_to_infinite_line_distance((sx, sy), corner1, corner2)
        furthest_point = (sx, sy)
        img[sy][sx] = 0 # mark as checked

        # Now expand out from the point we found to find other points and find the furthest.
        unchecked_points = get_adjacent_points(img, (sx, sy), thresh=thresh)
        # print(f"Side {side_name} starts at {sx},{sy}  dist={max_dist:.2f}  unchecked = {len(unchecked_points)}")


        while (len(unchecked_points) > 0 and num_to_check > 0):
            px, py = unchecked_points.pop(0)
            #if side_name == 'W': 
            #    print(f"{side_name} {num_to_check}: Checking at point {px},{py}. val = {img[py][px]}")
            if img[py][px] >= thresh:
                num_to_check -= 1
                # Check not too close too corner
                skip = False
                for c in [corner1, corner2]:
                    dist_from_corner = get_distance_between_2_points((px, py), c)
                    if dist_from_corner < min_dist_from_corner:
                        skip  = True
                if skip: continue
                dist = point_to_infinite_line_distance((px, py), corner1, corner2)
                #if side_name == 'W': 
                #    print(f"{side_name} {num_to_check}: Checking at point {px},{py}. D={dist}  (max = {max_dist} )  dist_to_C = {dist_from_corner} (min={min_dist_from_corner})")
                if dist > max_dist:
                    max_dist = dist
                    furthest_point = (px, py)
                unchecked_points.extend(get_adjacent_points(img, (px, py), thresh=thresh))
            img[py][px] = 0 # mark as checked

        # See if tab or blank
        dist_center_to_corner_line = point_to_infinite_line_distance((cx,cy), corner1, corner2)
        dist_center_to_point = get_distance_between_2_points((cx,cy), furthest_point)
        if dist_center_to_corner_line < dist_center_to_point:
            st = SideType.TAB
        else:
            st = SideType.BLANK

        return (furthest_point, st) if max_dist > min_distance else (0,SideType.EDGE)

    work_img = img.copy()
    triangles = []
    side_types = []
    for side in sides:
        (furthest_point, side_type) = find_furthest_point_for_side(work_img, side, thresh=20, num_to_check=max(img_w, img_h))
        if furthest_point: # Tab or Blank
            triangles.append(P_Triangle([side[1], side[2], furthest_point]))
            side_types.append(side_type)
        else: # Edge
            triangles.append(P_Triangle([side[1], side[2]]))
            side_types.append(SideType.EDGE)

    # cannot have edges on opposite sides
    if side_types[0] == SideType.EDGE and side_types[2] == SideType.EDGE:
        return None, None, None
    if side_types[1] == SideType.EDGE and side_types[3] == SideType.EDGE:
        return None, None, None

    piece_type = PieceType.MIDDLE
    num_edges = sum ([1 for st in side_types if st == SideType.EDGE ])
    print(f"Number of edges = {num_edges}")
    if num_edges == 2:
        piece_type = PieceType.CORNER
    elif num_edges == 1:
        piece_type = PieceType.EDGE

    return triangles, side_types, piece_type
