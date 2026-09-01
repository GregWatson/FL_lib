import numpy as np
from fl_types import J_Piece, PieceType, SideType
from show_matching_pair import show_matching_pair


def find_best_match(piece: J_Piece, pieces: list[J_Piece]) -> J_Piece | None:

    # Find another piece (other than self) that has a side that best matches a side of the given piece.

    if piece.info.piece_type == PieceType.CORNER or piece.info.piece_type == PieceType.EDGE:
        possibles = [p for p in pieces if p != piece and (p.info.piece_type == PieceType.CORNER or p.info.piece_type == PieceType.EDGE)]
    else:
        possibles = [p for p in pieces if p != piece ]

    if not len(possibles):
        print("There don't seem to be any other pieces that could match.")
        return None


    # 1. Choose one side of the four sides of piece that is either TAB or BLANK.
    # If it's an EDGE piece then don't choose the side opposite the EDGE.
    chosen_side_idx = None
    chosen_side_type = None
    for s_idx, s in enumerate(piece.info.side_types):
        if s in (SideType.TAB, SideType.BLANK and (piece.info.piece_type != PieceType.EDGE or piece.side_type_opposite(s_idx) != SideType.EDGE)):
            chosen_side_idx = s_idx
            chosen_side_type = s
            break

    if chosen_side_idx is None:
        print("Weird, the piece doesn't seem to have any tabs or blanks.")
        return None

    # 2. Find a target_piece in pieces that has a matching_side that is either BLANK or TAB that best matches the TAB or BLANK chosen in step 1.
    matching_side_type = SideType.BLANK if chosen_side_type == SideType.TAB else SideType.TAB
    matching_piece_type_has_edge = piece.info.piece_type == PieceType.EDGE or piece.info.piece_type == PieceType.CORNER

    # 3. If piece has an EDGE side that is next to the side chosen in step 1 then
    # if that EDGE is on the clockwise side of the chosen side then the target_piece
    # must have an EDGE side on the counter-clockwise side of the piece relative to the matching_side.
    cw_side_idx = (chosen_side_idx + 1) % 4
    has_cw_edge = (piece.info.side_types[cw_side_idx] == SideType.EDGE)
    ccw_side_idx = (chosen_side_idx - 1) % 4
    has_ccw_edge = (piece.info.side_types[ccw_side_idx] == SideType.EDGE)

    chosen_triangle = piece.rot['triangles'][chosen_side_idx]

    best_target_piece = None
    best_dist = float('inf')
    best_target_s_idx = None

    for target_piece in possibles:
        if matching_piece_type_has_edge and not target_piece.has_an_edge():
            continue
        for t_s_idx, t_s in enumerate(target_piece.info.side_types):
            if t_s != matching_side_type:
                continue

            if matching_piece_type_has_edge:
                # Check clockwise-adjacent edge constraint
                if has_cw_edge:
                    target_ccw_idx = (t_s_idx - 1) % 4
                    if target_piece.info.side_types[target_ccw_idx] != SideType.EDGE:
                        continue
                # Check counter-clockwise-adjacent edge constraint
                if has_ccw_edge:
                    target_cw_idx = (t_s_idx + 1) % 4
                    if target_piece.info.side_types[target_cw_idx] != SideType.EDGE:
                        continue

            # Calculate how well target_triangle matches chosen_triangle
            target_triangle = target_piece.rot['triangles'][t_s_idx]

            # Show angles.
            # print(f"Piece {piece.info.id} angles: ",end='')
            # for angle in chosen_triangle.angles: print(f"{angle:4.2f} ",end='')
            # print(f"\nPiece {target_piece.info.id} angles: ", end='')
            # for angle in target_triangle.angles: print(f"{angle:4.2f} ",end='')
            # print()

            angle_diff = sum(abs(chosen_triangle.angles[i] - target_triangle.angles[i]) for i in range(3)) * 100

            # Base length difference
            base_diff = abs(chosen_triangle.lengths[2] - target_triangle.lengths[2])
            # Leg lengths difference

            leg_diff = abs(chosen_triangle.lengths[0] - target_triangle.lengths[0]) + abs(chosen_triangle.lengths[1] - target_triangle.lengths[1])
            
            dist = base_diff + leg_diff + angle_diff
            print(f"DIST:{dist:.1f}  ---  Base diff: {base_diff:.1f} lef_diff: {leg_diff:.1f} Angle diff: {angle_diff:.1f}")
            if dist < best_dist:
                best_dist = dist
                best_target_piece = target_piece
                best_target_s_idx = t_s_idx
                print(f"Found better match: piece {target_piece.info.id}  best_dist:{best_dist} ")

    if best_target_piece is not None:
        print(f"Found best matching piece: ID {best_target_piece.info.id} with score {best_dist:.2f}")
        show_matching_pair(piece, chosen_side_idx, best_target_piece, best_target_s_idx)
        return best_target_piece

    print("No matching piece met the criteria.")
    return None

# Compute the quality of the match for the given piece, given the surrounding pieces.
def get_match_quality(piece, surrounding_pieces):

    match_value = 0
    # For each side of the piece, compute a match value based on how well it fits
    # the adjacent piece.

    for dir, other_piece in surrounding_pieces.items(): # dir in NESW
        if not other_piece: continue
        print(f"Trying dir {dir} against piece {other_piece.info.id}")

        # FIX THIS HERE



    return match_value

# Given the one-to-four pieces surrounding an unplaced location, as well as the side
# constraints of that location, find the best matching piece from a list of possibles.
# Return the piece and the desired rotation dictionary.
def find_best_match_given_surrounding_pieces(surrounding_pieces, side_constraints, possibles):
    best_piece = None
    best_score = float(0.0)
    best_dir = None  # rotation for the best piece.


    for possible in possibles:
        # get all the possible (1-4) different piece rotations that meet the constraints.
        possible_dirs = possible.get_dirs_by_constraints(side_constraints)
        if not possible_dirs: continue
        # Have at LEAST one rotation that meets the constraints.

        # Save original rotation (dir)
        orig_dir = possible.dir.copy()

        for possible_dir in possible_dirs:
            # Set the piece direction
            possible.set_direction(possible_dir)

            # calculate the quality of the match using the surrounding pieces.
            match_quality = get_match_quality(possible, surrounding_pieces)
            if match_quality > best_score:
                best_score = match_quality
                best_piece = possible
                best_dir = possible_dir

        # restore original dir.
        possible.set_direction(orig_dir)

    return (best_piece, best_dir, best_score)


