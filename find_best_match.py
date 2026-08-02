import numpy as np
from fl_types import J_Piece

def find_best_match(piece: J_Piece, pieces: list[J_Piece]) -> J_Piece | None:

    # Find another piece (other than self) that has an edge that best matches an edge of piece.

    for side_type, triangle in zip(piece.info.side_types, piece.rot['triangles']):
        print(f"Type = {side_type:s}   triangle = {triangle.points}")

    return None