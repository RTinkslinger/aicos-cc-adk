from __future__ import annotations

"""Action Scoring — wraps the AI CoS action scoring model.

Score ranges:
- >=7: "surface" — immediate action candidates
- 4-6.99: "low_confidence" — worth context enrichment
- <4: "context_only" — informational, no action
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ActionInput:
    """Input parameters for action scoring. All fields 0-10 scale."""

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


DEFAULT_WEIGHTS = {
    "bucket_impact": 0.25,
    "conviction_change": 0.25,
    "time_sensitivity": 0.2,
    "action_novelty": 0.15,
    "effort_vs_impact": 0.15,
}


def score_action(
    action: ActionInput,
    weights: Optional[dict[str, float]] = None,
) -> float:
    """Compute action score from weighted input components.

    Returns float on 0-10 scale.
    """
    action.validate()
    w = weights if weights is not None else DEFAULT_WEIGHTS

    weight_sum = sum(w.values())
    if not (0.95 <= weight_sum <= 1.05):
        raise ValueError(f"Weights must sum to ~1.0, got {weight_sum}")

    score = (
        w["bucket_impact"] * action.bucket_impact
        + w["conviction_change"] * action.conviction_change
        + w["time_sensitivity"] * action.time_sensitivity
        + w["action_novelty"] * action.action_novelty
        + w["effort_vs_impact"] * action.effort_vs_impact
    )
    return min(10.0, max(0.0, score))


def classify_action(score: float) -> str:
    """Classify: 'surface' (>=7), 'low_confidence' (4-7), 'context_only' (<4)."""
    if score >= 7:
        return "surface"
    elif score >= 4:
        return "low_confidence"
    return "context_only"
