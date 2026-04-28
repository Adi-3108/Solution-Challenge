from __future__ import annotations

from app.models.enums import SeverityLevel
from app.services.bias_engine.schemas import MetricResult, RemediationSnippet


def remediation_recommendations(metrics: list[MetricResult]) -> list[RemediationSnippet]:
    recommendations: list[RemediationSnippet] = []
    for metric in metrics:
        if metric.severity == SeverityLevel.GREEN:
            continue
        strategy, code_snippet = _strategy_for_metric(metric.metric_name)
        after_value = _simulate_improvement(metric)
        recommendations.append(
            RemediationSnippet(
                title=f"{metric.display_name} remediation",
                strategy=strategy,
                summary=_summary_for_metric(metric, strategy),
                affected_group=metric.affected_group or metric.group_name,
                metric_name=metric.metric_name,
                before_value=round(metric.value, 4),
                after_value=round(after_value, 4),
                chart_points=[
                    {"value": round(metric.value, 4), "index": 0.0},
                    {"value": round(after_value, 4), "index": 1.0},
                ],
                code_snippet=code_snippet,
            )
        )
    return recommendations[:12]


def _strategy_for_metric(metric_name: str) -> tuple[str, str]:
    mapping = {
        "disparate_impact_ratio": (
            "Pre-processing: reweighing samples",
            """from aif360.algorithms.preprocessing import Reweighing
rw = Reweighing(unprivileged_groups=unprivileged_groups, privileged_groups=privileged_groups)
dataset_transformed = rw.fit_transform(dataset)""",
        ),
        "statistical_parity_difference": (
            "Pre-processing: disparate impact remover",
            """from aif360.algorithms.preprocessing import DisparateImpactRemover
repairer = DisparateImpactRemover(repair_level=0.8)
dataset_transformed = repairer.fit_transform(dataset)""",
        ),
        "equal_opportunity_difference": (
            "Post-processing: threshold optimizer",
            """from fairlearn.postprocessing import ThresholdOptimizer
optimizer = ThresholdOptimizer(estimator=model, constraints='equal_opportunity')
optimizer.fit(X_train, y_train, sensitive_features=sensitive_features)""",
        ),
        "average_odds_difference": (
            "Post-processing: equalized odds",
            """from aif360.algorithms.postprocessing import EqOddsPostprocessing
postprocessor = EqOddsPostprocessing(unprivileged_groups=unprivileged_groups, privileged_groups=privileged_groups)
adjusted = postprocessor.fit_predict(dataset_true, dataset_pred)""",
        ),
        "predictive_parity_difference": (
            "In-processing: prejudice remover regularizer",
            """from aif360.algorithms.inprocessing import PrejudiceRemover
model = PrejudiceRemover(sensitive_attr='protected_attribute', eta=25.0)
model.fit(dataset)""",
        ),
    }
    fallback = (
        "In-processing: adversarial debiasing",
        """from aif360.algorithms.inprocessing import AdversarialDebiasing
debiaser = AdversarialDebiasing(
    privileged_groups=privileged_groups,
    unprivileged_groups=unprivileged_groups,
    scope_name='fairsight_debiasing'
)
debiaser.fit(dataset)""",
    )
    return mapping.get(metric_name, fallback)


def _simulate_improvement(metric: MetricResult) -> float:
    if metric.metric_name == "disparate_impact_ratio":
        return 1.0 + (metric.value - 1.0) * 0.35
    if metric.metric_name == "individual_fairness_score":
        return min(0.95, metric.value + 0.12)
    return metric.value * 0.45


def _summary_for_metric(metric: MetricResult, strategy: str) -> str:
    target_group = metric.affected_group or metric.group_name
    return (
        f"{strategy} is recommended because {metric.display_name} flagged a fairness gap affecting "
        f"{target_group}. The simulated result shows how the metric could move closer to the configured threshold."
    )

