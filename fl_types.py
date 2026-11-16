# Types used by Jigsaw solver
import numpy as np
from enum import Enum
from math import sqrt
from fl_core import get_angle_between_3_points, scale_and_place_foreground_with_background, rotate_image

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

    def get_connecting_type(self):
        """ Return the side type that connects to the given side type. """
        if self == SideType.EDGE or self == SideType.CURVE:
            return None
        return SideType.TAB if self == SideType.BLANK else SideType.BLANK 

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
    dir: dict  # Map of compass points NSEW to int index used in side_types and rot['triangles']

    @classmethod
    def connecting_sidetype(cls, side_type: SideType):
        if side_type == SideType.EDGE or side_type == SideType.CURVE:
            return None
        return SideType.TAB if side_type == SideType.BLANK else SideType.BLANK

    @classmethod
    def side_index_opposite(cls, side_index):
        return (side_index + 2) % 4


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
        self.dir = {} # Dict. maps 'NESW' to index(integer 0-3). Index used for triangle and side_types.
                      # Will get set to NESW -> 0 1 2 3 when piece is processed, but then 
                      # may change once the piece is placed in the jigsaw.

    def set_orientation(self, dir):
        self.dir = dir

    def has_an_edge(self):
        return self.info.side_types and len(self.info.side_types) == 4 and SideType.EDGE in self.info.side_types

    def side_type_opposite(self, side_index):
        return self.info.side_types[self.side_index_opposite(side_index)]

    def get_sidetype_by_dir(self, dir:str): # dir in NESW
        index = self.dir[dir]
        return self.info.side_types[index]
    
    # Check that current piece direction satisfies the constraints.
    def piece_side_constraints_ok(self, constraints: dict, use_given_dir = False, given_dir = None):
        if use_given_dir: assert given_dir is not None
        for dir, st in constraints.items():
            if dir=='P': continue
            index = given_dir[dir] if use_given_dir else self.dir[dir]
            if self.info.side_types[index] != st:
                return False
        return True

    # Get all (0 to 4) dirs dicts that satisfy the given side constraints.
    # returns list of dirs, or None.
    def get_dirs_by_constraints(self, constraints: dict):
        assert len(self.dir) == 4
        result = []
        temp_dir = self.dir.copy()
        for _ in  range(4):
            if self.piece_side_constraints_ok(constraints, use_given_dir = True, given_dir = temp_dir):
                result.append(temp_dir)
            # Rotate the piece by one direction and try again
            temp_dir = temp_dir.copy()
            for d in 'NESW': temp_dir[d] = (temp_dir[d] + 1) % 4
        if len(result): return result 
        else: return None

    # return the number of radians that the piece has been rotated using the dir list
    def get_macro_rotate_rads(self):
        if self.dir['N'] == 0: return 0
        elif self.dir['E'] == 0: return 3*np.pi/2
        elif self.dir['S'] == 0: return np.pi
        elif self.dir['W'] == 0: return np.pi/2
    
class Jigsaw:
    images: dict
    unplaced: list [ J_Piece ] # Unplaced pieces
    placed: list[ list [J_Piece | None] ] # list of rows. Each row is a list of pieces. 0,0 = top left.
    dim: list[int] # Dimensions of the puzzle. 0 = width, 1 = height
    num_pieces: int # Total number of pieces in the puzzle

    def __init__(self):
        # Initialize any necessary properties here
        self.images = {'originals': []} # All images used
        self.unplaced = [] # Unplaced pieces
        self.placed = [] # gird. Index as [y][x]
        self.dim = []
        self.num_pieces = 0
        pass

    def set_dim(self, height:int, width:int):
        self.dim = [width, height]
        self.placed = [[None for _ in range(width)] for _ in range(height)]
        self.num_pieces = height * width

    def get_placed_constraints(self, x:int, y:int) -> dict :
        constraints = {}
        if x==0: constraints['W'] = SideType.EDGE
        else: 
            if self.placed[y][x-1] is not None: constraints['W'] = self.placed[y][x-1].get_sidetype_by_dir('E').get_connecting_type()

        if x==(self.dim[0]-1): constraints['E'] = SideType.EDGE
        else: 
            if self.placed[y][x+1] is not None: constraints['E'] = self.placed[y][x+1].get_sidetype_by_dir('W').get_connecting_type()

        if y==0: constraints['N'] = SideType.EDGE
        else: 
            if self.placed[y-1][x] is not None: constraints['N'] = self.placed[y-1][x].get_sidetype_by_dir('S').get_connecting_type()

        if y==(self.dim[1]-1): constraints['S'] = SideType.EDGE
        else: 
            if self.placed[y+1][x] is not None: constraints['S'] = self.placed[y+1][x].get_sidetype_by_dir('N').get_connecting_type()


        # Set piece type constraint
        constraints['P'] = [PieceType.MIDDLE]

        # Check for corner
        for xx in (0, self.dim[0]-1):
            for yy in (0, self.dim[1]-1):
                if x==xx and y==yy:
                    constraints['P'] = [PieceType.CORNER]
                    return constraints

        # Check for edge
        for xx in (0, self.dim[0]-1):
            for yy in (0, self.dim[1]-1):
                if x==xx or y==yy:
                    constraints['P'] = [PieceType.EDGE]
                    return constraints

        return constraints


    def place_top_edge(self, top_edge):
        """ We constructed param top_edge assuming that it might be the top edge,
        but it could be the left (or right) edge."""
        if self.dim[0] != self.dim[1]:
            raise ValueError("Only square jigsaw puzzles are currently supported")
        for i,p in enumerate(top_edge):
            self.placed[0][i] = p
        print("The first edge has now been moved to be the top edge.")
        return

    def get_surrounding_pieces(self,x:int, y:int):
        """ Return dict of surrounding pieces."""
        surrounding_pieces = { 'W':None, 'N':None, 'E':None, 'S':None}
        if y > 0: 
            if self.placed[y-1][x] is not None: surrounding_pieces['N'] = self.placed[y-1][x]
        if y < self.dim[1] - 1:
            if self.placed[y+1][x] is not None: surrounding_pieces['S'] = self.placed[y+1][x]
        if x > 0: 
            if self.placed[y][x-1] is not None: surrounding_pieces['W'] = self.placed[y][x-1]
        if x < self.dim[0] - 1:
            if self.placed[y][x+1] is not None: surrounding_pieces['E'] = self.placed[y][x+1]
        return surrounding_pieces

    def create_image_of_jigsaw(self):
        """ Create an image representation of the current jigsaw state. """
        import cv2
        import numpy as np
        main_img = np.zeros((self.dim[1]*100, self.dim[0]*100, 4), dtype=np.uint8)
        for y in range(self.dim[1]):
            for x in range(self.dim[0]):
                piece = self.placed[y][x]
                if piece is not None:
                    macro_rotate_rads = piece.get_macro_rotate_rads()
                    print(f"Macro rotate for {x},{y} is {np.degrees(macro_rotate_rads)}")
                    # Rotate the piece's edges image by the macro rotation
                    rot_img = rotate_image(self.placed[y][x].rot["edges_image_grey"], macro_rotate_rads)
                    main_img = scale_and_place_foreground_with_background(rot_img, main_img, (100, 100), (x*100, y*100))
        return main_img