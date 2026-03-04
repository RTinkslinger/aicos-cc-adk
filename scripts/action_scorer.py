#!/usr/bin/env python3
"""
Action Scorer — AI Chief of Staff action optimizer utility.

Implements the Action Scoring Model for prioritizing actions across:
- New cap tables (highest impact)
- Deepening existing cap tables (high impact, continuous)
- New founders / companies (high impact)
- Thesis evolution (variable impact)

Score ranges:
- ≥7: "surface" — immediate action candidates
- 4-6.99: "low_confidence" — worth context enrichment
- <4: "context_only" — informational, no action
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ActionInput:
    """Input parameters for action scoring.
    
    All fields are on a 0-10 scale.
    """
    bucket_impact: float
    """0-10: Which priority bucket? (10=new cap tables, 8=deepen/founders, 6=thesis)"""
    
    conviction_change: float
    """0-10: Could this change conviction on an investment?"""
    
    time_sensitivity: float
    """0-10: How urgent is this? (decays over time)"""
    
    action_novelty: float
    """0-10: Is this a new insight or repetitive?"""
    
    effort_vs_impact: float
    """0-10: High impact / low effort = high score"""
    
    def validate(self) -> None:
        """Ensure all fields are in valid range [0, 10]."""
        fields = [
            ("bucket_impact", self.bucket_impact),
            ("conviction_change", self.conviction_change),
            ("time_sensitivity", self.time_sensitivity),
            ("action_novelty", self.action_novelty),
            ("effort_vs_impact", self.effort_vs_impact),
        ]
        for name, value in fields:
            if not (0 <= value <= 10):
                raise ValueError(f"{name} must be 0-10, got {value}")


def score_action(
    action: ActionInput,
    weights: Optional[dict] = None
) -> float:
    """Compute action score from weighted input components.
    
    Args:
        action: ActionInput with all scoring dimensions
        weights: Optional custom weights dict. Keys: bucket_impact, conviction_change,
                 time_sensitivity, action_novelty, effort_vs_impact.
                 Must sum to 1.0. Defaults to balanced weights.
    
    Returns:
        float: Final action score (0-10 scale)
        
    Raises:
        ValueError: If action fields are out of range or weights don't sum to ~1.0
    """
    action.validate()
    
    # Default weights: balanced with slight emphasis on impact & conviction
    default_weights = {
        "bucket_impact": 0.25,
        "conviction_change": 0.25,
        "time_sensitivity": 0.2,
        "action_novelty": 0.15,
        "effort_vs_impact": 0.15,
    }
    
    w = weights if weights is not None else default_weights
    
    # Validate weights sum to approximately 1.0
    weight_sum = sum(w.values())
    if not (0.95 <= weight_sum <= 1.05):
        raise ValueError(f"Weights must sum to ~1.0, got {weight_sum}")
    
    # Compute weighted sum
    score = (
        w["bucket_impact"] * action.bucket_impact +
        w["conviction_change"] * action.conviction_change +
        w["time_sensitivity"] * action.time_sensitivity +
        w["action_novelty"] * action.action_novelty +
        w["effort_vs_impact"] * action.effort_vs_impact
    )
    
    return min(10.0, max(0.0, score))  # Clamp to [0, 10]


def classify_action(score: float) -> str:
    """Classify action based on score.
    
    Args:
        score: Action score (typically 0-10)
    
    Returns:
        str: One of "surface", "low_confidence", or "context_only"
    """
    if score >= 7:
        return "surface"
    elif 4 <= score < 7:
        return "low_confidence"
    else:
        return "context_only"


def main() -> None:
    """Example usage of the action scorer."""
    # Example 1: Strong action (new cap table opportunity)
    action1 = ActionInput(
        bucket_impact=9.0,       # New cap table = highest bucket
        conviction_change=7.5,   # Good conviction impact
        time_sensitivity=8.0,    # Urgent window
        action_novelty=8.0,      # Fresh opportunity
        effort_vs_impact=7.5,    # Reasonable lift
    )
    
    score1 = score_action(action1)
    classification1 = classify_action(score1)
    print(f"Action 1 (New Cap Table): {score1:.2f} → {classification1}")
    
    # Example 2: Weak action (thesis research, low urgency)
    action2 = ActionInput(
        bucket_impact=5.0,       # Thesis evolution = lower bucket
        conviction_change=4.0,   # Modest conviction impact
        time_sensitivity=2.0,    # No urgency
        action_novelty=3.0,      # Incremental
        effort_vs_impact=3.0,    # High effort, low impact
    )
    
    score2 = score_action(action2)
    classification2 = classify_action(score2)
    print(f"Action 2 (Thesis Research): {score2:.2f} → {classification2}")
    
    # Example 3: Custom weights (emphasize conviction change)
    action3 = ActionInput(
        bucket_impact=6.0,
        conviction_change=9.0,   # Strong conviction signal
        time_sensitivity=5.0,
        action_novelty=6.0,
        effort_vs_impact=6.0,
    )
    
    custom_weights = {
        "bucket_impact": 0.15,
        "conviction_change": 0.4,    # Increased weight
        "time_sensitivity": 0.15,
        "action_novelty": 0.15,
        "effort_vs_impact": 0.15,
    }
    
    score3 = score_action(action3, weights=custom_weights)
    classification3 = classify_action(score3)
    print(f"Action 3 (High Conviction): {score3:.2f} → {classification3} (custom weights)")


if __name__ == "__main__":
    main()
