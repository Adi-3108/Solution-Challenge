from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.services.bias_engine.helpers import (
    build_metric_result,
    normalize_series,
    severity_for_lower_is_better,
    to_binary,
)
from app.services.bias_engine.schemas import (
    AuditInput,
    CounterfactualAssessment,
    CounterfactualSample,
    CounterfactualTransition,
    MetricResult,
)

MAX_COUNTERFACTUAL_ROWS = 500


@dataclass(slots=True)
class PredictionStrategy:
    source: str
    predict: Callable[[pd.DataFrame], pd.Series]


def counterfactual_fairness_analysis(
    dataframe: pd.DataFrame,
    audit_input: AuditInput,
) -> tuple[list[MetricResult], list[CounterfactualAssessment]]:
    sampled = _sample_dataframe(dataframe)
    strategy = _build_prediction_strategy(sampled, audit_input)
    if strategy is None:
        return [], []

    original_predictions = strategy.predict(sampled).reset_index(drop=True)
    metrics: list[MetricResult] = []
    assessments: list[CounterfactualAssessment] = []

    for protected_attribute in audit_input.protected_columns:
        assessment = _assess_protected_attribute(
            sampled,
            protected_attribute,
            original_predictions,
            strategy,
            audit_input,
        )
        if assessment is None:
            continue
        assessments.append(assessment)
        explanation = (
            f"Changing only {protected_attribute} flipped the predicted decision in "
            f"{assessment.flip_rate * 100:.1f}% of tested counterfactual pairs using {assessment.source}. "
            f"{assessment.affected_records} of {len(sampled)} sampled records changed under at least one alternate group value."
        )
        metrics.append(
            build_metric_result(
                metric_name="counterfactual_flip_rate",
                group_name=protected_attribute,
                value=assessment.flip_rate,
                severity=assessment.severity,
                threshold_used=audit_input.thresholds.counterfactual_flip_rate_green,
                explanation=explanation,
                details={
                    "source": assessment.source,
                    "affected_records": assessment.affected_records,
                    "affected_record_rate": assessment.affected_record_rate,
                    "tested_pairs": assessment.tested_pairs,
                    "sampled_records": len(sampled),
                    "transition_summary": [
                        transition.model_dump(mode="json") for transition in assessment.transition_summary
                    ],
                    "sample_flips": [
                        sample.model_dump(mode="json") for sample in assessment.sample_flips
                    ],
                },
            )
        )
    return metrics, assessments


def _sample_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if len(dataframe.index) <= MAX_COUNTERFACTUAL_ROWS:
        return dataframe.copy().reset_index(drop=True)
    return dataframe.sample(n=MAX_COUNTERFACTUAL_ROWS, random_state=42).sort_index().reset_index(drop=True)


def _build_prediction_strategy(
    dataframe: pd.DataFrame,
    audit_input: AuditInput,
) -> PredictionStrategy | None:
    if audit_input.loaded_model is not None:
        try:
            predictor = _build_uploaded_model_predictor(dataframe, audit_input)
            predictor(dataframe.head(min(len(dataframe.index), 2)))
            return PredictionStrategy(source="uploaded model predictions", predict=predictor)
        except Exception:
            pass

    if audit_input.prediction_column:
        surrogate = _build_surrogate_predictor(
            dataframe,
            label_column=audit_input.prediction_column,
            audit_input=audit_input,
        )
        if surrogate is not None:
            return PredictionStrategy(source="surrogate of recorded predictions", predict=surrogate)

    surrogate = _build_surrogate_predictor(
        dataframe,
        label_column=audit_input.target_column,
        audit_input=audit_input,
    )
    if surrogate is not None:
        return PredictionStrategy(source="surrogate of recorded outcomes", predict=surrogate)
    return None


def _build_uploaded_model_predictor(
    dataframe: pd.DataFrame,
    audit_input: AuditInput,
) -> Callable[[pd.DataFrame], pd.Series]:
    model = audit_input.loaded_model
    feature_columns = _feature_columns(dataframe, audit_input, audit_input.target_column)

    def predict(frame: pd.DataFrame) -> pd.Series:
        features = frame[feature_columns].copy()
        if hasattr(model, "feature_names_in_"):
            required = [str(column) for column in model.feature_names_in_]
            missing = [column for column in required if column not in features.columns]
            if missing:
                raise ValueError(f"Missing required model features: {missing}")
            features = features.reindex(columns=required)
        raw_predictions = model.predict(features)
        return _normalize_predictions(raw_predictions, audit_input.positive_label)

    return predict


def _build_surrogate_predictor(
    dataframe: pd.DataFrame,
    label_column: str,
    audit_input: AuditInput,
) -> Callable[[pd.DataFrame], pd.Series] | None:
    feature_columns = _feature_columns(dataframe, audit_input, label_column)
    if not feature_columns:
        return None

    labels = to_binary(dataframe[label_column], audit_input.positive_label)
    if labels.nunique(dropna=True) <= 1:
        return None

    features = dataframe[feature_columns].copy()
    numeric_columns = [
        column for column in feature_columns if pd.api.types.is_numeric_dtype(features[column])
    ]
    categorical_columns = [column for column in feature_columns if column not in numeric_columns]
    pipeline = Pipeline(
        steps=[
            (
                "preprocess",
                ColumnTransformer(
                    transformers=[
                        (
                            "numeric",
                            Pipeline(
                                [
                                    ("imputer", SimpleImputer(strategy="median")),
                                    ("scaler", StandardScaler()),
                                ]
                            ),
                            numeric_columns,
                        ),
                        (
                            "categorical",
                            Pipeline(
                                [
                                    ("imputer", SimpleImputer(strategy="most_frequent")),
                                    ("encoder", OneHotEncoder(handle_unknown="ignore")),
                                ]
                            ),
                            categorical_columns,
                        ),
                    ]
                ),
            ),
            ("classifier", LogisticRegression(max_iter=500, class_weight="balanced")),
        ]
    )
    pipeline.fit(features, labels)

    def predict(frame: pd.DataFrame) -> pd.Series:
        predictions = pipeline.predict(frame[feature_columns].copy())
        return pd.Series(predictions, dtype=int)

    return predict


def _feature_columns(
    dataframe: pd.DataFrame,
    audit_input: AuditInput,
    label_column: str,
) -> list[str]:
    excluded = {label_column, audit_input.score_column}
    if audit_input.target_column != label_column:
        excluded.add(audit_input.target_column)
    if audit_input.prediction_column and audit_input.prediction_column != label_column:
        excluded.add(audit_input.prediction_column)
    return [column for column in dataframe.columns if column not in excluded]


def _normalize_predictions(
    predictions: object,
    positive_label: str | int | float | bool,
) -> pd.Series:
    series = pd.Series(predictions)
    unique_values = set(series.dropna().astype(str).unique())
    if unique_values.issubset({"0", "1"}) or len(unique_values) <= 2:
        return to_binary(series, positive_label).reset_index(drop=True)
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float).ge(0.5).astype(int).reset_index(drop=True)
    return to_binary(series, positive_label).reset_index(drop=True)


def _assess_protected_attribute(
    dataframe: pd.DataFrame,
    protected_attribute: str,
    original_predictions: pd.Series,
    strategy: PredictionStrategy,
    audit_input: AuditInput,
) -> CounterfactualAssessment | None:
    group_options = _representative_groups(dataframe[protected_attribute])
    if len(group_options) <= 1:
        return None

    variants: list[pd.Series] = []
    metadata: list[tuple[int, str, str, int]] = []
    normalized_groups = normalize_series(dataframe[protected_attribute]).reset_index(drop=True)

    for row_index, (_, row) in enumerate(dataframe.iterrows()):
        original_group = normalized_groups.iloc[row_index]
        original_prediction = int(original_predictions.iloc[row_index])
        for target_label, target_value in group_options:
            if target_label == original_group:
                continue
            variant = row.copy()
            variant[protected_attribute] = target_value
            variants.append(variant)
            metadata.append((row_index, str(original_group), target_label, original_prediction))

    if not variants:
        return None

    variant_predictions = strategy.predict(pd.DataFrame(variants, columns=dataframe.columns)).reset_index(drop=True)
    flipped_rows: set[int] = set()
    transition_counts: dict[tuple[str, str], dict[str, int]] = {}
    sample_flips: list[CounterfactualSample] = []

    for index, (row_index, from_group, to_group, original_prediction) in enumerate(metadata):
        counterfactual_prediction = int(variant_predictions.iloc[index])
        key = (from_group, to_group)
        counts = transition_counts.setdefault(key, {"tested": 0, "flipped": 0})
        counts["tested"] += 1
        if counterfactual_prediction == original_prediction:
            continue
        counts["flipped"] += 1
        flipped_rows.add(row_index)
        if len(sample_flips) < 5:
            sample_flips.append(
                CounterfactualSample(
                    row_index=row_index,
                    from_group=from_group,
                    to_group=to_group,
                    original_prediction=original_prediction,
                    counterfactual_prediction=counterfactual_prediction,
                )
            )

    tested_pairs = len(metadata)
    flipped_pairs = sum(item["flipped"] for item in transition_counts.values())
    flip_rate = flipped_pairs / tested_pairs if tested_pairs else 0.0
    severity = severity_for_lower_is_better(
        flip_rate,
        audit_input.thresholds.counterfactual_flip_rate_green,
        audit_input.thresholds.counterfactual_flip_rate_amber,
    )

    transitions = sorted(
        [
            CounterfactualTransition(
                from_group=from_group,
                to_group=to_group,
                tested=counts["tested"],
                flipped=counts["flipped"],
                flip_rate=round(counts["flipped"] / counts["tested"], 4) if counts["tested"] else 0.0,
            )
            for (from_group, to_group), counts in transition_counts.items()
        ],
        key=lambda item: (item.flip_rate, item.flipped),
        reverse=True,
    )

    return CounterfactualAssessment(
        protected_attribute=protected_attribute,
        flip_rate=round(flip_rate, 4),
        affected_records=len(flipped_rows),
        affected_record_rate=round(len(flipped_rows) / len(dataframe.index), 4),
        tested_pairs=tested_pairs,
        source=strategy.source,
        severity=severity,
        transition_summary=transitions[:6],
        sample_flips=sample_flips,
    )


def _representative_groups(series: pd.Series) -> list[tuple[str, object]]:
    options: list[tuple[str, object]] = []
    seen: set[str] = set()
    normalized = normalize_series(series).reset_index(drop=True)
    raw_series = series.reset_index(drop=True)
    for index, label in enumerate(normalized):
        label_str = str(label)
        if label_str in seen:
            continue
        raw_value = raw_series.iloc[index]
        options.append((label_str, None if pd.isna(raw_value) else raw_value))
        seen.add(label_str)
    return options
