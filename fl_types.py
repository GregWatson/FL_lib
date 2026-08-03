# Types used by Jigsaw solver
import numpy as np
from enum import Enum
from math import sqrt
from fl_core import get_angle_between_3_points

def line_len(pt1, pt2):
    return sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

class PieceType(Enum):
    CORNER = 0
    EDGE = 1
    MIDDLE = 2

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
    side_types: list [SideType] = []
    area: int | None = None # Area of the piece in pixels in original image.
    centroid: tuple | None = None # Centroid in original image
    piece_type: PieceType | None = None # Type of the piece
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
        self.side_types = []
        self.area = None
        self.centroid = None
        self.piece_type = None # CORNER, EDGE, MIDDLE

        P_Info.__instance_count += 1

class J_Piece:
    """ Info about a single piece.
    Info can be pre-rotation (before we were able to rate the image to a 'straight' rotation)
    or post-rotation.
    """
    info: P_Info 
    orig: dict 
    rot: dict

    def __init__(self, info=None):
        if info is None:
            self.info = P_Info()
        else: self.info = info
        self.orig = {
            'user_image': None, # Image or None. Orig for *only* this piece. Pre-rotation
            'inverse_transform_fn': None, # Inverse transform matrix to place point back in full original image
            'rot_center': None, # Center of rotation for user_image
        }
        self.rot = { # Info of post-rotation image
            'rotation_angle_rad': None, # Rotation angle in radians
            'edges_image_grey': None, # Rotated edges only (grey)
            'img_w': None, # Width of the image
            'img_h': None,  # Height of image
            'corners': None, # List of 2 lists of 2 corners: [[TL, TR], [BL, BR]]. Each is (corner-ness, point(x,y), outer angle in radians)
            'blank_keep_outs': None, # List of areas where blanks occur. Each is (top left point, bottom right point)
            'tab_keep_outs': None, # List of areas where tabs occur. Each is (top left point, bottom right point)
            'triangles': [] # List of triangles. (P_Triangle)
        }
        pass

    def has_an_edge(self):
        return self.info.side_types and len(self.info.side_types) == 4 and SideType.EDGE in self.info.side_types

    def side_index_opposite(self, side_index):
        return (side_index + 2) % 4

    def side_type_opposite(self, side_index):
        return self.info.side_types[self.side_index_opposite(side_index)]



class Jigsaw:
    images: dict
    pieces: list[ J_Piece ]

    def __init__(self):
        # Initialize any necessary properties here
        self.images = {'originals': []} # All images used
        self.unplaced = [] # Unplaced pieces
        pass

