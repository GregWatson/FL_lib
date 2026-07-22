# Types used by Jigsaw solver
import numpy as np
from enum import Enum
from math import sqrt
from fl_core import get_angle_between_3_points

def line_len(pt1, pt2):
    return sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

class SideType(Enum):
    EDGE = 0 # Edge of the puzzle
    TAB = 1 # Outward calibration
    BLANK = 2 # Inward calibration
    CURVE = 3 # Irregular but not a distinct tab or socket. Kind of "Other"

class P_Triangle:
    """ Info about a triangle on a side.
    NOTE: if there are 3 points then they are always ordered as corner1, corner2, mid-point
    """
    points: list [ tuple ] | None # Either 2 (edge) or 3 (Tab, blank) points
    lengths: list | None  # of sides. Side is opposite point in list order.
    angles: list [ float ] | None # angles associated with each point (radians)

    def __init__(self, points=None):
        self.points = points
        self.lengths = None
        self.angles = None
        if points != None:
            if len(points) == 2: # Edge
                self.lengths = [line_len(points[0], points[1])]
                self.angles = [0]
            elif len(points) == 3: # triangle
                self.lengths = [line_len(points[1], points[2]), # type: ignore
                                line_len(points[2], points[0]), # type: ignore
                                line_len(points[0], points[1]) ] # type: ignore
                self.angles = [ get_angle_between_3_points(points[1], points[0], points[2]), # corner 1
                                get_angle_between_3_points(points[0], points[1], points[2]), # corner 2
                                get_angle_between_3_points(points[0], points[2], points[1]) ] # mid-point / apex
            else:
                print(f"Error: Wrong number of points in edge endpoints - expected 2 (edge) or 3 (tab/blank). Got {len(points)}")
                exit(1)

# class P_Side:
#     """ Info about a single side of a piece """
#     side_type: SideType | None = None # Type
#     triangle: P_Triangle | None = None # Info about triangle on side

#     def __init__(self, side_type = None, triangle = None):
#         self.side_type = side_type
#         self.triangle = triangle

class P_Info:
    """ Info about a single piece"""
    id: int | None = None # A unique numeric ID for the piece.
    box: tuple | None = None # Bounding box for the piece in ORIGINAL image.
    contour: np.ndarray | None = None # Numpy array of points that form the contour
    sides: list [SideType] | None = []
    area: int | None = None # Area of the piece in pixels in original image.
    centroid: tuple | None = None # Centroid in original image

    # Private class attribute tracking the count
    __instance_count = 0

    @classmethod
    def get_count(cls):
        # Safe public reader method
        return cls.__instance_count
    
    def __init__(self):
        self.id = P_Info.__instance_count
        self.box = None
        self.contour = None
        self.sides = []
        self.area = None
        self.centroid = None

        P_Info.__instance_count += 1

class J_Piece:
    """ Info about a single piece.
    Info can be pre-rotation (before we were able to rate the image to a 'straight' rotation)
    or post-rotation.
    """
    info: P_Info | None
    orig: dict 
    rot: dict

    def __init__(self, info=None):
        self.info = info
        self.orig = {
            'user_image': None # Image or None. Orig for *only* this piece.
        }
        self.rot = {
            'edges_image_grey': None, # Rotated edges only (grey)
            'img_w': None, # Width of the image
            'img_h': None,  # Height of image
            'triangles': []
        }
        pass



class Jigsaw:
    images: dict
    pieces: list[ J_Piece ]

    def __init__(self):
        # Initialize any necessary properties here
        self.images = {'originals': []} # All images used
        self.unplaced = [] # Unplaced pieces
        pass

