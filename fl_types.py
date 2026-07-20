# Types used by Jigsaw solver
import numpy as np

class J_Piece:
    """ Info about a single piece.
    Info can be pre-rotation (before we were able to rate the image to a 'stright' rotation)
    or post-rotation.
    """
    info: dict | None
    orig: dict
    rot: dict

    def __init__(self, info=None):
        self.info = info
        self.orig = {
            'user_image': None
        }
        self.rot = {}
        pass



class Jigsaw:
    images: dict
    pieces: list[ J_Piece ]

    def __init__(self):
        # Initialize any necessary properties here
        self.images = {'originals': []} # All images used
        self.unplaced = [] # Unplaced pieces
        pass

