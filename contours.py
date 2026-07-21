import numpy as np
from .piece import Piece, SideType

def resample_contour(contour, n_points=50):
    """
    Resamples the contour to have exactly n_points spaced uniformly.
    contour: (N, 1, 2) numpy array or (N, 2)
    """
    if len(contour.shape) == 3:
        pts = contour[:, 0, :]
    else:
        pts = contour
        
    # Calculate cumulative distance
    dists = np.sqrt(np.sum(np.diff(pts, axis=0)**2, axis=1))
    cum_dists = np.insert(np.cumsum(dists), 0, 0)
    total_len = cum_dists[-1]
    
    if total_len == 0:
        return np.repeat(pts[0:1], n_points, axis=0)
        
    # Uniform distances
    uniform_dists = np.linspace(0, total_len, n_points)
    
    # Interpolate
    x_interp = np.interp(uniform_dists, cum_dists, pts[:, 0])
    y_interp = np.interp(uniform_dists, cum_dists, pts[:, 1])
    
    return np.column_stack((x_interp, y_interp))

def align_contour(contour):
    """
    Transforms contour so that:
    - First point is at (0, 0)
    - Last point is at (d, 0) where d is the distance between endpoints
    Returns the transformed contour.
    """
    if len(contour) < 2:
        return contour
        
    p1 = contour[0]
    p2 = contour[-1]
    
    # Translation
    centered = contour - p1
    
    # Rotation
    dx, dy = p2 - p1
    angle = np.arctan2(dy, dx)
    
    c, s = np.cos(-angle), np.sin(-angle)
    R = np.array([[c, -s], [s, c]])
    
    # Rotate
    aligned = centered @ R.T
    
    return aligned

def find_matches(pieces: list[Piece]):
    """
    Iterates through pieces and finds matches between Tabs and Sockets.
    Returns a list of matches: [(piece1, side_idx1, piece2, side_idx2, score), ...]
    """
    matches = []
    
    # Pre-process contours for all sides of all pieces?
    # Or just do it on the fly. On the fly is fine for N=50 points.
    
    for i, p1 in enumerate(pieces):
        for s1_idx, side1 in enumerate(p1.sides):
            if side1 is None or side1.type == SideType.FLAT:
                continue
                
            # Target type: Socket <-> Tab, Curve <-> Curve
            if side1.type == SideType.SOCKET:
                target_type = SideType.TAB
            elif side1.type == SideType.TAB:
                target_type = SideType.SOCKET
            else:
                target_type = SideType.CURVE
            
            # Prepare Side 1 canonical form
            # 1. Resample
            c1_resampled = resample_contour(side1.contour)
            # 2. Align
            c1_aligned = align_contour(c1_resampled)
            
            l1 = np.linalg.norm(side1.contour[0][0] - side1.contour[-1][0])
            
            for j, p2 in enumerate(pieces):
                if i == j: 
                    continue
                    
                for s2_idx, side2 in enumerate(p2.sides):
                    if side2 is None or side2.type != target_type:
                        continue
                        
                    # 1. Length check
                    l2 = np.linalg.norm(side2.contour[0][0] - side2.contour[-1][0])

                    print(f"Length check: {l1} vs {l2} ")
                    
                    if abs(l1 - l2) > (l1 * 0.3): # Allow 30% difference? Or fixed pixels?
                        # Using relative threshold is better for scale invariance if we wanted that,
                        # but here we expect same scale. 
                        # Fixed threshold of e.g. 50 pixels might be safer.
                        # Sticking to loose check.
                        if abs(l1 - l2) > 100:
                            continue
                        
                    # 2. Shape matching

                    # For Side 2, we must REVERSE it before aligning
                    # Because if A matches B, A(start->end) matches B(end->start)
                    
                    # Reverse contour
                    # side2.contour is (N, 1, 2)
                    c2_reversed = side2.contour[::-1]
                    
                    # Resample
                    c2_resampled = resample_contour(c2_reversed)
                    
                    # Align
                    c2_aligned = align_contour(c2_resampled)
                    
                    # Compute distance (Mean Squared Error)
                    diff = c1_aligned - c2_aligned
                    mse = np.mean(np.sum(diff**2, axis=1))
                    
                    # Heuristic score: RMSE
                    score = np.sqrt(mse)
                    
                    # Threshold
                    # If match is perfect, score is 0.
                    # Good match might be < 5.0 pixels average error?
                    if score < 1500.0: # Experimental threshold
                        matches.append({
                            "p1": p1, "s1": s1_idx,
                            "p2": p2, "s2": s2_idx,
                            "score": score
                        })
                        
    # Sort by best score (lowest)
    matches.sort(key=lambda x: x["score"])
    
    return matches
