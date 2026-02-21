def calculate_final_score(ela_score: float, layout_score: float):
    """
    Combines ELA and Layout scores into a final weighted fraud confidence score.
    Returns: (final_score, classification)
    """
    # Weights: ELA (Pixel level) is usually more definitive for tampering
    # Layout (Structural) is a strong supporting signal
    W_ELA = 0.6
    W_LAYOUT = 0.4
    
    final_score = (ela_score * W_ELA) + (layout_score * W_LAYOUT)
    final_score_pct = float(final_score * 100)
    
    classification = "Authentic"
    if final_score_pct > 70:
        classification = "Highly Forged"
    elif final_score_pct > 30:
        classification = "Suspicious"
        
    return round(final_score_pct, 2), classification
