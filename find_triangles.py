from fl_core import point_to_infinite_line_distance, show_image, get_adjacent_points, draw_triangle

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

    # (side_name, corner1, corner2, side_midpoint, side_normal)
    sides = [ ('top', corners[0][0][1], corners[0][1][1], (img_w//2, 0), (0,1)),
              ('right', corners[0][1][1], corners[1][1][1], (img_w-1, img_h//2), (-1,0)),
              ('bottom', corners[1][0][1], corners[1][1][1], (img_w//2, img_h-1), (0,-1)),
              ('left', corners[0][0][1], corners[1][0][1], (0, img_h//2), (1,0)) ]

    # num_to_check: number of points to check starting from the midpoint of the side and moving outwards.
    def find_furthest_point_for_side(img, side, thresh=20,num_to_check=100):
        side_name, corner1, corner2, side_midpoint, side_normal = side
        img_w, img_h = img.shape[1], img.shape[0]

        # Note: could optimize performance by precomputing coefficients A, B, and C in the line 
        # equation Ax + By + C = 0 for the line defined by corner1 and corner2, and then use those 
        # coefficients to compute the distance from each point to the line. But for now, we'll just 
        # use the point_to_infinite_line_distance function.

        # First start at midpoint and head in the direction of the normal to the side, and then expand 
        # outwards in a spiral pattern to find the furthest point from the line defined by corner1 and corner2.
        # This is a brute force approach, but it should be fast enough for our purposes since the image 
        # is small and we only have 4 sides to check. 
        sx,sy = side_midpoint
        while sx >= 0 and sx < img_w and sy >= 0 and sy < img_h and img[sy][sx] == 0:
            sx += side_normal[0]
            sy += side_normal[1]
        max_dist = point_to_infinite_line_distance((sx, sy), corner1, corner2)
        furthest_point = (sx, sy)
        img[sy][sx] = 0 # mark as checked

        # Now expand out from the point we found to find other points and find the furthest.
        unchecked_points = get_adjacent_points(img, (sx, sy), thresh=thresh)

        while (len(unchecked_points) > 0 and num_to_check > 0):
            px, py = unchecked_points.pop(0)
            if img[py][px] >= thresh:
                img[py][px] = 0 # mark as checked
                dist = point_to_infinite_line_distance((px, py), corner1, corner2)
                if dist > max_dist:
                    max_dist = dist
                    furthest_point = (px, py)
                num_to_check -= 1
                unchecked_points.extend(get_adjacent_points(img, (px, py), thresh=thresh))

        return furthest_point


    work_img = img.copy()
    triangles = []
    for side in sides:
        furthest_point = find_furthest_point_for_side(work_img, side, thresh=20, num_to_check=min(img_w, img_h)//2)
        triangles.append((side[1], side[2], furthest_point))

    for triangle in triangles:
        draw_triangle(work_img, triangle[0], triangle[1], triangle[2], color=(200, 200, 200), thickness=2)

    show_image(work_img, str="Find triangles", max=1000, wait_for_key=True)

    return triangles
