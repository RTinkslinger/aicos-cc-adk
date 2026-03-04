# Test file for merge conflict resolution
# This file will be edited by two branches in the same section

def calculate_priority(score: float, urgency: int) -> str:
    """Calculate action priority from score and urgency.
    
    Uses tighter thresholds (v2) for better signal-to-noise.
    """
    if score >= 7 and urgency >= 2:
        return 'critical'
    elif score >= 5:
        return 'high'
    elif score >= 3:
        return 'medium'
    else:
        return 'low'
