# Test file for merge conflict resolution
# This file will be edited by two branches in the same section

def calculate_priority(score: float, urgency: int, weight: float = 1.0) -> str:
    """Calculate action priority from score, urgency, and optional weight.

    Uses tighter thresholds (v2) for better signal-to-noise.
    """
    weighted_score = score * weight
    if weighted_score >= 7 and urgency >= 2:
        return 'critical'
    elif weighted_score >= 5:
        return 'high'
    elif weighted_score >= 3:
        return 'medium'
    else:
        return 'low'
