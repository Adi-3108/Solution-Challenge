from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.models.enums import SeverityLevel
from app.services.bias_engine.constants import DISPLAY_NAMES
from app.services.bias_engine.schemas import (
    BiasThresholdConfig,
    GroupComparison,
    MetricResult,
)


def normalize_series(series: pd.Series) -> pd.Series:
    return series.fillna("Unknown").astype(str)


def to_binary(series: pd.Series, positive_label: str | int | float | bool) -> pd.Series:
    normalized = series.fillna("__missing__").astype(str)
    positive = str(positive_label)
    return normalized.eq(positive).astype(int)


def pick_privileged_and_unprivileged(
    dataframe: pd.DataFrame, protected_attribute: str, outcome: pd.Series
) -> GroupComparison:
    grouped = dataframe.assign(_outcome=outcome).groupby(protected_attribute)["_outcome"].mean()
    if grouped.empty or len(grouped.index) == 1:
        only_group = str(grouped.index[0]) if not grouped.empty else "Unknown"
        return GroupComparison(
            protected_attribute=protected_attribute,
            privileged_group=only_group,
            unprivileged_group=only_group,
        )
    privileged_group = str(grouped.idxmax())
    unprivileged_group = str(grouped.idxmin())
    return GroupComparison(
        protected_attribute=protected_attribute,
        privileged_group=privileged_group,
        unprivileged_group=unprivileged_group,
    )


def rate_for_group(
    dataframe: pd.DataFrame, protected_attribute: str, target: pd.Series, group_name: str
) -> float:
    mask = normalize_series(dataframe[protected_attribute]).eq(group_name)
    if mask.sum() == 0:
        return 0.0
    return float(target.loc[mask].mean())


def severity_for_signed_metric(value: float, green: float, amber: float) -> SeverityLevel:
    absolute = abs(value)
    if absolute <= green:
        return SeverityLevel.GREEN
    if absolute <= amber:
        return SeverityLevel.AMBER
    return SeverityLevel.RED


def severity_for_lower_is_better(value: float, green: float, amber: float) -> SeverityLevel:
    if value <= green:
        return SeverityLevel.GREEN
    if value <= amber:
        return SeverityLevel.AMBER
    return SeverityLevel.RED


def severity_for_disparate_impact(
    value: float, thresholds: BiasThresholdConfig
) -> tuple[SeverityLevel, float]:
    midpoint = min(
        abs(value - thresholds.disparate_impact_lower),
        abs(value - thresholds.disparate_impact_upper),
    )
    if thresholds.disparate_impact_lower <= value <= thresholds.disparate_impact_upper:
        return SeverityLevel.GREEN, midpoint
    return SeverityLevel.RED, midpoint


def severity_for_individual_fairness(
    value: float, thresholds: BiasThresholdConfig
) -> tuple[SeverityLevel, float]:
    if value >= thresholds.individual_fairness_green:
        return SeverityLevel.GREEN, thresholds.individual_fairness_green
    if value >= thresholds.individual_fairness_amber:
        return SeverityLevel.AMBER, thresholds.individual_fairness_amber
    return SeverityLevel.RED, thresholds.individual_fairness_amber


def build_metric_result(
    metric_name: str,
    group_name: str,
    value: float,
    severity: SeverityLevel,
    threshold_used: float,
    explanation: str,
    comparison: GroupComparison | None = None,
    intersectional_groups: dict[str, str] | None = None,
    details: dict[str, object] | None = None,
) -> MetricResult:
    return MetricResult(
        metric_name=metric_name,
        display_name=DISPLAY_NAMES.get(metric_name, metric_name),
        group_name=group_name,
        value=round(value, 4),
        severity=severity,
        threshold_used=round(threshold_used, 4),
        explanation=explanation,
        comparison=comparison,
        affected_group=comparison.unprivileged_group if comparison else None,
        intersectional_groups=intersectional_groups or {},
        details=details or {},
    )


def cramers_v(left: pd.Series, right: pd.Series) -> float:
    contingency = pd.crosstab(normalize_series(left), normalize_series(right))
    if contingency.empty:
        return 0.0
    chi2 = chi2_contingency(contingency)[0]
    total = contingency.to_numpy().sum()
    if total == 0:
        return 0.0
    phi2 = chi2 / total
    rows, cols = contingency.shape
    adjusted_rows = max(rows - 1, 1)
    adjusted_cols = max(cols - 1, 1)
    return float(np.sqrt(phi2 / min(adjusted_rows, adjusted_cols)))


def correlation_strength(left: pd.Series, right: pd.Series) -> float:
    if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
        return float(abs(left.fillna(0).corr(right.fillna(0), method="pearson")))
    return float(abs(cramers_v(left, right)))


def similar_outcome_consistency(
    dataframe: pd.DataFrame,
    target_column: str,
    protected_columns: Iterable[str],
    positive_label: str | int | float | bool,
    prediction_column: str | None = None,
    score_column: str | None = None,
) -> float:
    exclude = {target_column, *protected_columns}
    if prediction_column:
        exclude.add(prediction_column)
    if score_column:
        exclude.add(score_column)
    feature_columns = [column for column in dataframe.columns if column not in exclude]
    if not feature_columns:
        return 1.0

    features = dataframe[feature_columns].copy()
    numeric = [column for column in feature_columns if pd.api.types.is_numeric_dtype(features[column])]
    categorical = [column for column in feature_columns if column not in numeric]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
                ),
                numeric,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )
    transformed = preprocessor.fit_transform(features)
    neighbors = min(5, len(dataframe))
    if neighbors <= 1:
        return 1.0
    model = NearestNeighbors(n_neighbors=neighbors)
    model.fit(transformed)
    indices = model.kneighbors(return_distance=False)
    outcomes = to_binary(dataframe[target_column], positive_label).to_numpy()
    mismatch_rates = []
    for row_index, neighbor_indexes in enumerate(indices):
        comparable = [idx for idx in neighbor_indexes if idx != row_index]
        if not comparable:
            continue
        disagreements = sum(outcomes[idx] != outcomes[row_index] for idx in comparable)
        mismatch_rates.append(disagreements / len(comparable))
    if not mismatch_rates:
        return 1.0
    return float(1 - np.mean(mismatch_rates))
