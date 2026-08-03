import cv2
import numpy as np
from fl_types import J_Piece, PieceType
from find_best_match import find_best_match

def solve_puzzle(pieces: list[J_Piece], debug=False) -> bool:

    print(f"Solving puzzle")

    for p in pieces:
        if p.info.piece_type == PieceType.CORNER:
            piece = p
            break
    else:
        print(f"No corner piece found")
        return False
    
    best_matching_piece = find_best_match(piece, pieces)

    if best_matching_piece is None:
        print("No matching piece found")
        return False
    else:
        print(f"Best matching piece has ID: {best_matching_piece.info.id}")
        return True



