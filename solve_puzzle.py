import cv2
import numpy as np
from fl_types import J_Piece, PieceType, Jigsaw, SideType
from find_best_match import find_best_match_given_surrounding_pieces
from fl_core import show_image

def build_top_edge(jigsaw: Jigsaw):
    """ Build the first edge for the jigsaw """

    # First get any corner piece; then orientate it so that the top and left are edges.
    topleft_piece = next((p for p in jigsaw.unplaced if p.info.piece_type == PieceType.CORNER), None)
    if topleft_piece is None:
        raise ValueError("No corner piece found.")
    # Rotate the corner to be top left.
    new_dirs = topleft_piece.get_dirs_by_constraints({'W':SideType.EDGE, 'N':SideType.EDGE})
    if new_dirs is None:
        raise ValueError("Corner piece does not satisy two adjacent sides being edges.")
    else:
        topleft_piece.dir = new_dirs[0] # can only be one valid rotation

    # We cannot use jigsaw.placed yet as we don't know which side we are dealing with.
    # Instead, use a list that we can place once we know where we are.
    top_edge = [topleft_piece]
    jigsaw.unplaced.remove(topleft_piece)

    # Now try to add edge pieces along the top edge. 
    # We should come to a corner piece after placing dim[0] or dim[1] pieces.
    max_side = max(jigsaw.dim)   # dont know if we have top/bottom or left/right, so take max.
    min_side = min(jigsaw.dim)

    while len(top_edge) != max_side or top_edge[-1].info.piece_type != PieceType.CORNER:

        # There is only one placed piece adjacent and that is to the west of the piece we are looking for.
        last_piece = top_edge[-1]

        surrounding_pieces = { 'W':last_piece, 'N':None, 'E':None, 'S':None}
        constraints = {'N': SideType.EDGE,
                            'W': J_Piece.connecting_sidetype(last_piece.get_sidetype_by_dir('E'))}
        if len(top_edge) == max_side-1:
            constraints['P'] = [PieceType.CORNER ] # only
        elif len(top_edge) == min_side-1:
            constraints['P'] = [PieceType.CORNER, PieceType.EDGE ] 
        else:
            constraints['P'] = [PieceType.EDGE ] # only

        (piece, dir, score) = find_best_match_given_surrounding_pieces(surrounding_pieces, constraints, jigsaw.unplaced)
        if piece is None:
            raise ValueError("No suitable piece was found.")
        piece.set_orientation(dir)
        top_edge.append(piece)
        print(f"Adding {str(piece.info.piece_type)} piece {piece.info.id} to initial edge.")
        jigsaw.unplaced.remove(piece)

    return top_edge

def find_and_place_best_piece_at_XY(jigsaw, x, y):
        if jigsaw.placed[y][x] != None: return
        print(f"Find and place best piece at ({x},{y})")
        constraints = jigsaw.get_placed_constraints(x=x, y=y)
        surrounding_pieces = jigsaw.get_surrounding_pieces(x=x,y=y)
        if (x==5 and y==5): print(f"    Constraints at ({x},{y}) are {constraints}")
        (piece, dir, score) = find_best_match_given_surrounding_pieces(surrounding_pieces, constraints, jigsaw.unplaced)
        if piece is None:
            raise ValueError(f"No suitable piece was found for ({x},{y}).")
        piece.set_orientation(dir)
        jigsaw.placed[y][x] = piece
        print(f"Adding {str(piece.info.piece_type)} piece {piece.info.id} to grid at ({x},{y}): {piece.print_edges()}")
        jigsaw.unplaced.remove(piece)

def build_edges(jigsaw):
    """ Build all edges for the jigsaw. One edge (top or left) is already constructed.
    """
    # print("Placing top edge")
    # y = 0 # top edge
    # for x in range(jigsaw.dim[0]):
    #     find_and_place_best_piece_at_XY(jigsaw, x, y)
    for x in (0, jigsaw.dim[0]-1): # left edge, right edge
        print("Placing {} edge.".format("left" if x == 0 else "right"))
        for y in range(jigsaw.dim[1]):
            find_and_place_best_piece_at_XY(jigsaw, x, y)
            new_image = jigsaw.create_image_of_jigsaw()
            show_image(new_image, str="Jigsaw", max_side=1000, wait_for_key=True)

    print("Placing bottom edge")
    y = jigsaw.dim[1]-1 # bottom
    for x in range(jigsaw.dim[0]):
        find_and_place_best_piece_at_XY(jigsaw, x, y)
        new_image = jigsaw.create_image_of_jigsaw()
        show_image(new_image, str="Jigsaw", max_side=1000, wait_for_key=True)



def solve_puzzle(jigsaw: Jigsaw, debug=False) -> bool:

    print(f"Solving puzzle")

    edge_pieces = build_top_edge(jigsaw)

    # It might not have been the top edge so move it if needed.
    jigsaw.place_top_edge(edge_pieces)

    build_edges(jigsaw)

    return True

