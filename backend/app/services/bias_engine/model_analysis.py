from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_curve

from app.services.bias_engine.helpers import (
    build_metric_result,
    normalize_series,
    pick_privileged_and_unprivileged,
    rate_for_group,
    severity_for_signed_metric,
    to_binary,
)
from app.services.bias_engine.schemas import BiasThresholdConfig, MetricResult


def _group_rates(
    dataframe: pd.DataFrame,
    protected_attribute: str,
    actual: pd.Series,
    predicted: pd.Series,
    group_name: str,
) -> dict[str, float]:
    mask = normalize_series(dataframe[protected_attribute]).eq(group_name)
    if mask.sum() == 0:
        return {"tpr": 0.0, "fpr": 0.0, "ppv": 0.0, "selection_rate": 0.0}
    actual_group = actual.loc[mask]
    predicted_group = predicted.loc[mask]
    positives = actual_group.eq(1)
    negatives = actual_group.eq(0)
    predicted_positives = predicted_group.eq(1)
    true_positives = int((positives & predicted_positives).sum())
    false_positives = int((negatives & predicted_positives).sum())
    total_predicted = int(predicted_positives.sum())
    return {
        "tpr": true_positives / max(int(positives.sum()), 1),
        "fpr": false_positives / max(int(negatives.sum()), 1),
        "ppv": true_positives / max(total_predicted, 1),
        "selection_rate": float(predicted_group.mean()),
    }


def _expected_calibration_error(actual: pd.Series, scores: pd.Series, bins: int = 5) -> float:
    frame = pd.DataFrame({"actual": actual, "score": scores})
    frame["bin"] = pd.cut(frame["score"], bins=bins, labels=False, include_lowest=True)
    total = len(frame.index)
    error = 0.0
    for _, group in frame.groupby("bin", dropna=False):
        if group.empty:
            continue
        observed = float(group["actual"].mean())
        expected = float(group["score"].mean())
        error += abs(observed - expected) * len(group.index) / total
    return float(error)


def compute_model_metrics(
    dataframe: pd.DataFrame,
    target_column: str,
    prediction_column: str,
    protected_columns: list[str],
    positive_label: str | int | float | bool,
    thresholds: BiasThresholdConfig,
    score_column: str | None = None,
) -> tuple[list[MetricResult], dict[str, dict[str, int]], dict[str, list[dict[str, float]]], dict[str, list[dict[str, float]]]]:
    actual = to_binary(dataframe[target_column], positive_label)
    predicted = to_binary(dataframe[prediction_column], positive_label)
    scores = dataframe[score_column].astype(float) if score_column else predicted.astype(float)
    metrics: list[MetricResult] = []
    confusion_payload: dict[str, dict[str, int]] = {}
    calibration_payload: dict[str, list[dict[str, float]]] = {}
    roc_payload: dict[str, list[dict[str, float]]] = {}

    for protected in protected_columns:
        comparison = pick_privileged_and_unprivileged(dataframe, protected, actual)
        privileged = _group_rates(dataframe, protected, actual, predicted, comparison.privileged_group)
        unprivileged = _group_rates(dataframe, protected, actual, predicted, comparison.unprivileged_group)
        tpr_diff = unprivileged["tpr"] - privileged["tpr"]
        fpr_diff = unprivileged["fpr"] - privileged["fpr"]
        average_odds = 0.5 * (fpr_diff + tpr_diff)
        predictive_parity = unprivileged["ppv"] - privileged["ppv"]
        demographic_parity = unprivileged["selection_rate"] - privileged["selection_rate"]
        equalized_odds = max(abs(tpr_diff), abs(fpr_diff))
        unprivileged_mask = normalize_series(dataframe[protected]).eq(comparison.unprivileged_group)
        privileged_mask = normalize_series(dataframe[protected]).eq(comparison.privileged_group)
        ece_gap = _expected_calibration_error(actual.loc[unprivileged_mask], scores.loc[unprivileged_mask])
        ece_gap -= _expected_calibration_error(actual.loc[privileged_mask], scores.loc[privileged_mask])
        calibration_diff = abs(ece_gap)

        metric_specs = [
            (
                "equal_opportunity_difference",
                tpr_diff,
                thresholds.equal_opportunity_green,
                thresholds.equal_opportunity_amber,
                f"True positive rates differ by {tpr_diff:.3f} between {comparison.unprivileged_group} and {comparison.privileged_group}.",
            ),
            (
                "average_odds_difference",
                average_odds,
                thresholds.average_odds_green,
                thresholds.average_odds_amber,
                f"Average odds differ by {average_odds:.3f}; this combines false-positive and true-positive gaps.",
            ),
            (
                "predictive_parity_difference",
                predictive_parity,
                thresholds.predictive_parity_green,
                thresholds.predictive_parity_amber,
                f"Precision differs by {predictive_parity:.3f}, meaning one group's positive predictions are more reliable.",
            ),
            (
                "demographic_parity_difference",
                demographic_parity,
                thresholds.parity_green,
                thresholds.parity_amber,
                f"Predicted positive rates differ by {demographic_parity:.3f} between the compared groups.",
            ),
            (
                "equalized_odds_difference",
                equalized_odds,
                thresholds.equal_opportunity_green,
                thresholds.equal_opportunity_amber,
                f"The largest gap across true-positive and false-positive rates is {equalized_odds:.3f}.",
            ),
            (
                "calibration_error_difference",
                calibration_diff,
                thresholds.calibration_error_green,
                thresholds.calibration_error_amber,
                f"Calibration error differs by {calibration_diff:.3f}, showing score confidence is not equally reliable across groups.",
            ),
        ]
        for name, value, green, amber, explanation in metric_specs:
            severity = severity_for_signed_metric(value, green, amber)
            metrics.append(
                build_metric_result(
                    metric_name=name,
                    group_name=protected,
                    value=value,
                    severity=severity,
                    threshold_used=green,
                    explanation=explanation,
                    comparison=comparison,
                    details={"privileged": privileged, "unprivileged": unprivileged},
                )
            )

        for group_name in {comparison.privileged_group, comparison.unprivileged_group}:
            mask = normalize_series(dataframe[protected]).eq(group_name)
            labels = actual.loc[mask]
            preds = predicted.loc[mask]
            matrix = confusion_matrix(labels, preds, labels=[0, 1]).ravel()
            confusion_payload[f"{protected}:{group_name}"] = {
                "tn": int(matrix[0]),
                "fp": int(matrix[1]),
                "fn": int(matrix[2]),
                "tp": int(matrix[3]),
            }
            fpr, tpr, _ = roc_curve(labels, scores.loc[mask])
            roc_payload[f"{protected}:{group_name}"] = [
                {"fpr": round(float(fpr[index]), 4), "tpr": round(float(tpr[index]), 4)}
                for index in range(len(fpr))
            ]
            calibration_payload[f"{protected}:{group_name}"] = _calibration_curve(labels, scores.loc[mask])
    return metrics, confusion_payload, calibration_payload, roc_payload


def _calibration_curve(actual: pd.Series, scores: pd.Series, bins: int = 5) -> list[dict[str, float]]:
    frame = pd.DataFrame({"actual": actual, "score": scores})
    frame["bin"] = pd.cut(frame["score"], bins=bins, labels=False, include_lowest=True)
    payload = []
    for _, group in frame.groupby("bin", dropna=False):
        if group.empty:
            continue
        payload.append(
            {
                "mean_score": round(float(group["score"].mean()), 4),
                "positive_rate": round(float(group["actual"].mean()), 4),
            }
        )
    return payload

