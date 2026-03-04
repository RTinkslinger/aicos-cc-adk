# Test file for merge conflict resolution
# This file will be edited by two branches in the same section

def calculate_priority(score: float, urgency: int, weight: float = 1.0) -> str:
    """Calculate action priority from score, urgency, and optional weight."""
    weighted_score = score * weight
    if weighted_score >= 8 and urgency >= 3:
        return 'critical'
    elif weighted_score >= 6:
        return 'high'
    elif weighted_score >= 4:
        return 'medium'
    else:
        return 'low'
