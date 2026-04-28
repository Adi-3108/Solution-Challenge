from __future__ import annotations

from app.models.enums import SeverityLevel

DISPLAY_NAMES = {
    "disparate_impact_ratio": "Disparate Impact Ratio",
    "statistical_parity_difference": "Statistical Parity Difference",
    "equal_opportunity_difference": "Equal Opportunity Difference",
    "average_odds_difference": "Average Odds Difference",
    "predictive_parity_difference": "Predictive Parity Difference",
    "individual_fairness_score": "Individual Fairness Score",
    "calibration_error_difference": "Calibration Error Difference",
    "demographic_parity_difference": "Demographic Parity Difference",
    "equalized_odds_difference": "Equalized Odds Difference",
    "counterfactual_flip_rate": "Counterfactual Flip Rate",
}

SEVERITY_SCORES = {
    SeverityLevel.GREEN: 15.0,
    SeverityLevel.AMBER: 60.0,
    SeverityLevel.RED: 95.0,
}

DEFAULT_METRIC_WEIGHTS = {
    "disparate_impact_ratio": 1.2,
    "statistical_parity_difference": 1.1,
    "equal_opportunity_difference": 1.0,
    "average_odds_difference": 0.9,
    "predictive_parity_difference": 0.9,
    "individual_fairness_score": 0.8,
    "calibration_error_difference": 0.8,
    "demographic_parity_difference": 0.9,
    "equalized_odds_difference": 0.9,
    "counterfactual_flip_rate": 0.8,
}
