# Types used by Jigsaw solver
import numpy as np
from enum import Enum

class SideType(Enum):
    FLAT = 0 # Edge of the puzzle
    TAB = 1 # Outward calibration
    BLANK = 2 # Inward calibration
    CURVE = 3 # Irregular but not a distinct tab or socket. Kind of "Other"

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
        self.sides = None
        self.area = None
        self.centroid = None

        P_Info.__instance_count += 1

class J_Piece:
    """ Info about a single piece.
    Info can be pre-rotation (before we were able to rate the image to a 'stright' rotation)
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
            'img_h': None  # Height of image
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

