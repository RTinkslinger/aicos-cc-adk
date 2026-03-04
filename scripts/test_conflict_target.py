# Test file for merge conflict resolution
# This file will be edited by two branches in the same section

def calculate_priority(score: float, urgency: int) -> str:
    """Calculate action priority from score and urgency."""
    if score >= 8 and urgency >= 3:
        return 'critical'
    elif score >= 6:
        return 'high'
    elif score >= 4:
        return 'medium'
    else:
        return 'low'
