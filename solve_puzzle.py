import cv2
import numpy as np
from fl_types import J_Piece, PieceType, Jigsaw, SideType
from find_best_match import find_best_match_given_surrounding_pieces

def build_edges(jigsaw: Jigsaw):
    """ Build the edges for the jigsaw """

    pieces = jigsaw.unplaced

    # Build an edge

    # First get a corner piece; then orient it so that the top and left are edges.
    topleft_piece = next((p for p in pieces if p.info.piece_type == PieceType.CORNER), None)
    if topleft_piece is None:
        raise ValueError("No corner piece found.")
    # Rotate the corner to be top left.
    new_dirs = topleft_piece.get_dirs_by_constraints({'W':SideType.EDGE, 'N':SideType.EDGE})
    if new_dirs is None:
        raise ValueError("Corner piece does not satisy two adjacent sides being edges.")
    else:
        topleft_piece.dir = new_dirs[0] # can only be one valid rotation

    edge_pieces = [topleft_piece]

    # Now try to add edge pieces along the top edge. 
    # We should come to a corner piece after placing dim[0] or dim[1] pieces.
    max_side = max(jigsaw.dim)   # dont know if we have top/bottom or left/right, so take max.
    while len(edge_pieces) < max_side:

        # There is only one placed piece adjacent and that is to the west of the piece we are looking for.
        last_piece = edge_pieces[-1]

        surrounding_pieces = { 'W':last_piece, 'N':None, 'E':None, 'S':None}
        side_constraints = {'N': SideType.EDGE,
                            'W': J_Piece.connecting_sidetype(last_piece.get_sidetype_by_dir('E'))}

        piece_dir_score = find_best_match_given_surrounding_pieces(surrounding_pieces, side_constraints, jigsaw.unplaced)

        # # Add a piece.

        # if (len(edge_pieces) != (jigsaw.dim[0]-1)) and (len(edge_pieces) != (jigsaw.dim[1]-1)):
        #     possibles = [ p for p in jigsaw.unplaced if p.info.piece_type == PieceType.EDGE ]
        # else:
        #     possibles = [ p for p in jigsaw.unplaced if (p.info.piece_type == PieceType.EDGE or p.info.piece_type == PieceType.CORNER) ]

        # # limit the possibles to those that match tab/blank as well.
        # possibles = Jigsaw.get_pieces_that_satisfy_constraints(constraints, possibles)

        # poss_ids = ", ".join([str(p.info.id) for p in possibles])
        # print(f"  Found {len(possibles)} possible edge pieces: {poss_ids}.")
        # if not len(possibles):
        #     raise ValueError("Unable to find a piece that satisfies the given constraints.")

        # # Find the best match from list of possibles, given the surrounding (NESW) pieces.
        # best_match = find_best_match_given_surrounding_pieces( last_piece, possibles)


        # best_matching_piece = find_best_match(piece, pieces)


def solve_puzzle(jigsaw: Jigsaw, debug=False) -> bool:

    print(f"Solving puzzle")

    build_edges(jigsaw)

    return True

