import numpy as np
from fl_types import J_Piece, PieceType, SideType
from show_matching_pair import show_matching_pair

opp_dir = { 'N':'S', 'W':'E', 'S':'N', 'E':'W'}

# Given pieces p1 and p2 where p1 connects to p2 on p1's 'dir' side (dir in NESW),
# compute the quality of the triangle match.
def compute_triangle_match(p1: J_Piece, p2:J_Piece, dir:str):
    p1_idx = p1.dir[dir]
    p2_idx = p2.dir[opp_dir[dir]]
    p1_triangle = p1.rot['triangles'][p1_idx]
    p2_triangle = p2.rot['triangles'][p2_idx]

    # Calculate how well p2_triangle matches p1_triangle

    # Show angles.
    # print(f"Piece {piece.info.id} angles: ",end='')
    # for angle in p1_triangle.angles: print(f"{angle:4.2f} ",end='')
    # print(f"\nPiece {target_piece.info.id} angles: ", end='')
    # for angle in p2_triangle.angles: print(f"{angle:4.2f} ",end='')
    # print()

    angle_diff = sum(abs(p1_triangle.angles[i] - p2_triangle.angles[i]) for i in range(3)) * 100

    # Base length difference
    base_diff = abs(p1_triangle.lengths[2] - p2_triangle.lengths[2])
    # Leg lengths difference

    leg_diff = abs(p1_triangle.lengths[0] - p2_triangle.lengths[0]) + abs(p1_triangle.lengths[1] - p2_triangle.lengths[1])
    
    dist = base_diff + leg_diff + angle_diff

    return dist


# Compute the quality of the match for the given piece, given the surrounding pieces.
def get_match_quality(piece, surrounding_pieces):

    match_value = float(0.0)
    # For each side of the piece, compute a match value based on how well it fits
    # the adjacent piece.

    for dir, other_piece in surrounding_pieces.items(): # key is in NESW
        if not other_piece: continue
        # print(f"     Trying dir {dir} against piece {other_piece.info.id}")

        match_difference = compute_triangle_match(piece, other_piece, dir)
        match_value += match_difference

    return match_value

# Given the one-to-four pieces surrounding an unplaced location, as well as the side
# constraints of that location, find the best matching piece from a list of possibles.
# Return the piece and the desired rotation dictionary.
# Best match has lowest value.
def find_best_match_given_surrounding_pieces(surrounding_pieces, constraints, possibles):
    best_piece = None
    best_score = float('inf')
    best_dir = None  # rotation for the best piece.
    for c,v in constraints.items(): print(f"Constraint {c} is {v}")
    for possible in possibles:
        if possible.info.piece_type not in constraints['P']: continue

        # get all the possible (1-4) different piece rotations that meet the constraints.
        possible_dirs = possible.get_dirs_by_constraints(constraints)
        if not possible_dirs: continue

        # We have at LEAST one rotation that meets the constraints.
        # print(f"Trying possible piece {possible.info.id}")

        # Save original rotation (dir)
        orig_dir = possible.dir.copy()

        for possible_dir in possible_dirs:
            # Set the piece direction
            possible.set_orientation(possible_dir)

            # calculate the quality of the match using the surrounding pieces.
            match_quality = get_match_quality(possible, surrounding_pieces)
            if match_quality < best_score:
                # print(f"  Found smaller match deviation: {match_quality} for piece {possible.info.id}")

                best_score = match_quality
                best_piece = possible
                best_dir = possible_dir

        # restore original dir.
        possible.set_orientation(orig_dir)

    return (best_piece, best_dir, best_score)


