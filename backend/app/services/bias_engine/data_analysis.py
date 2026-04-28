from __future__ import annotations

import pandas as pd

from app.models.enums import SeverityLevel
from app.services.bias_engine.helpers import (
    build_metric_result,
    correlation_strength,
    normalize_series,
    pick_privileged_and_unprivileged,
    rate_for_group,
    severity_for_disparate_impact,
    severity_for_individual_fairness,
    severity_for_signed_metric,
    similar_outcome_consistency,
    to_binary,
)
from app.services.bias_engine.schemas import (
    BiasThresholdConfig,
    DistributionSeries,
    MetricResult,
    ProxyVariableFinding,
)


def class_distribution_by_group(
    dataframe: pd.DataFrame,
    protected_columns: list[str],
    target_column: str,
    positive_label: str | int | float | bool,
) -> list[DistributionSeries]:
    outcome = to_binary(dataframe[target_column], positive_label)
    series_list: list[DistributionSeries] = []
    for protected in protected_columns:
        groups = []
        grouped = dataframe.assign(_outcome=outcome, _group=normalize_series(dataframe[protected])).groupby("_group")
        for group_name, group_frame in grouped:
            groups.append(
                {
                    "group": str(group_name),
                    "count": int(len(group_frame)),
                    "positive_rate": round(float(group_frame["_outcome"].mean()), 4),
                }
            )
        series_list.append(DistributionSeries(protected_attribute=protected, groups=groups))
    return series_list


def disparate_impact_and_parity(
    dataframe: pd.DataFrame,
    protected_attribute: str,
    target_column: str,
    positive_label: str | int | float | bool,
    thresholds: BiasThresholdConfig,
) -> list[MetricResult]:
    outcome = to_binary(dataframe[target_column], positive_label)
    comparison = pick_privileged_and_unprivileged(dataframe, protected_attribute, outcome)
    privileged_rate = rate_for_group(dataframe, protected_attribute, outcome, comparison.privileged_group)
    unprivileged_rate = rate_for_group(dataframe, protected_attribute, outcome, comparison.unprivileged_group)
    ratio = 1.0 if privileged_rate == 0 else unprivileged_rate / privileged_rate
    parity = unprivileged_rate - privileged_rate
    ratio_severity, ratio_threshold = severity_for_disparate_impact(ratio, thresholds)
    parity_severity = severity_for_signed_metric(
        parity,
        thresholds.parity_green,
        thresholds.parity_amber,
    )

    ratio_text = (
        f"The unprivileged group receives the positive outcome at {ratio * 100:.1f}% "
        f"the rate of the privileged group. The 80% rule (four-fifths rule) is a widely used legal standard."
    )
    parity_text = (
        f"The gap in positive outcome rates between {comparison.unprivileged_group} and "
        f"{comparison.privileged_group} is {parity:.3f}. Larger gaps suggest unequal access to beneficial outcomes."
    )
    return [
        build_metric_result(
            metric_name="disparate_impact_ratio",
            group_name=protected_attribute,
            value=ratio,
            severity=ratio_severity,
            threshold_used=ratio_threshold,
            explanation=ratio_text,
            comparison=comparison,
            details={"privileged_rate": privileged_rate, "unprivileged_rate": unprivileged_rate},
        ),
        build_metric_result(
            metric_name="statistical_parity_difference",
            group_name=protected_attribute,
            value=parity,
            severity=parity_severity,
            threshold_used=thresholds.parity_green,
            explanation=parity_text,
            comparison=comparison,
            details={"privileged_rate": privileged_rate, "unprivileged_rate": unprivileged_rate},
        ),
    ]


def missing_data_rates(dataframe: pd.DataFrame, protected_columns: list[str]) -> dict[str, list[dict[str, float | str]]]:
    payload: dict[str, list[dict[str, float | str]]] = {}
    for protected in protected_columns:
        grouped = dataframe.assign(_group=normalize_series(dataframe[protected])).groupby("_group")
        rows = []
        for group_name, group_frame in grouped:
            missing_rate = float(group_frame.isna().mean().mean())
            rows.append({"group": str(group_name), "missing_rate": round(missing_rate, 4)})
        payload[protected] = rows
    return payload


def proxy_variable_detection(
    dataframe: pd.DataFrame,
    protected_columns: list[str],
    thresholds: BiasThresholdConfig,
) -> tuple[list[ProxyVariableFinding], dict[str, dict[str, float]]]:
    matrix: dict[str, dict[str, float]] = {}
    findings: list[ProxyVariableFinding] = []
    candidate_columns = [column for column in dataframe.columns if column not in protected_columns]
    for candidate in candidate_columns:
        matrix[candidate] = {}
        for protected in protected_columns:
            score = round(correlation_strength(dataframe[candidate], dataframe[protected]), 4)
            matrix[candidate][protected] = score
            if score < thresholds.proxy_correlation_threshold:
                continue
            findings.append(
                ProxyVariableFinding(
                    protected_attribute=protected,
                    candidate_column=candidate,
                    correlation=score,
                    severity=SeverityLevel.RED if score >= 0.85 else SeverityLevel.AMBER,
                )
            )
    findings.sort(key=lambda item: item.correlation, reverse=True)
    return findings, matrix


def individual_fairness_metric(
    dataframe: pd.DataFrame,
    target_column: str,
    protected_columns: list[str],
    positive_label: str | int | float | bool,
    thresholds: BiasThresholdConfig,
    prediction_column: str | None = None,
    score_column: str | None = None,
) -> MetricResult:
    fairness_score = similar_outcome_consistency(
        dataframe,
        target_column,
        protected_columns,
        positive_label,
        prediction_column,
        score_column,
    )
    severity, threshold_used = severity_for_individual_fairness(fairness_score, thresholds)
    explanation = (
        f"Similar individuals receive the same outcome {fairness_score * 100:.1f}% of the time. "
        "Lower scores suggest the system treats comparable people inconsistently."
    )
    return build_metric_result(
        metric_name="individual_fairness_score",
        group_name="overall",
        value=fairness_score,
        severity=severity,
        threshold_used=threshold_used,
        explanation=explanation,
        details={"consistency_rate": fairness_score},
    )

