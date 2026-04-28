from __future__ import annotations

import pandas as pd

from app.services.bias_engine.helpers import build_metric_result, severity_for_signed_metric, to_binary
from app.services.bias_engine.schemas import BiasThresholdConfig, MetricResult


def compute_intersectional_metrics(
    dataframe: pd.DataFrame,
    target_column: str,
    protected_columns: list[str],
    positive_label: str | int | float | bool,
    thresholds: BiasThresholdConfig,
) -> list[MetricResult]:
    if len(protected_columns) < 2:
        return []
    outcome = to_binary(dataframe[target_column], positive_label)
    grouped = dataframe.assign(_outcome=outcome).groupby(protected_columns)
    overall_rate = float(outcome.mean()) if len(outcome.index) else 0.0
    results: list[MetricResult] = []
    for group_keys, group_frame in grouped:
        group_rate = float(group_frame["_outcome"].mean())
        rate_gap = group_rate - overall_rate
        intersection_map = {
            column: str(group_keys[index]) for index, column in enumerate(protected_columns)
        }
        explanation = (
            f"This intersection sees a positive outcome rate gap of {rate_gap:.3f} versus the dataset overall. "
            "Intersectional analysis helps catch harms that do not appear in single-attribute views."
        )
        results.append(
            build_metric_result(
                metric_name="statistical_parity_difference",
                group_name=" x ".join(intersection_map.values()),
                value=rate_gap,
                severity=severity_for_signed_metric(
                    rate_gap,
                    thresholds.parity_green,
                    thresholds.parity_amber,
                ),
                threshold_used=thresholds.parity_green,
                explanation=explanation,
                intersectional_groups=intersection_map,
                details={"group_rate": group_rate, "overall_rate": overall_rate},
            )
        )
    return sorted(results, key=lambda item: abs(item.value), reverse=True)

