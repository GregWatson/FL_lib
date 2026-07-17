# Types used by Jigsaw solver
import numpy as np

class J_Piece:
    """ Info about a single piece.
    Info can be pre-rotation (before we were able to rate the image to a 'stright' rotation)
    or post-rotation.
    """
    pre: dict
    post: dict

    def __init__(self):
        self.pre = {
            'user_image': None
        }
        self.post = {}
        pass
class Jigsaw:
    images: dict
    pieces: list[ J_Piece ]

    def __init__(self):
        # Initialize any necessary properties here
        self.images = {'originals': []} # All images used
        self.unplaced = [] # Unplaced pieces
        pass

