from __future__ import annotations

import numpy as np
import pandas as pd


def compute_shap_payload(
    loaded_model: object | None,
    dataframe: pd.DataFrame,
    protected_columns: list[str],
    target_column: str,
    prediction_column: str | None = None,
    score_column: str | None = None,
) -> dict[str, object]:
    if loaded_model is None:
        return {}
    feature_columns = [
        column
        for column in dataframe.columns
        if column not in {target_column, prediction_column, score_column, *protected_columns}
    ]
    if not feature_columns:
        return {}
    numeric_frame = pd.get_dummies(dataframe[feature_columns], dummy_na=True).astype(float)
    try:
        import shap

        explainer = shap.Explainer(loaded_model, numeric_frame)
        shap_values = explainer(numeric_frame)
        values = np.asarray(shap_values.values)
        global_importance = np.abs(values).mean(axis=0)
        groups_payload = {}
        for protected in protected_columns:
            groups_payload[protected] = {}
            for group_name, group_frame in dataframe.groupby(protected):
                indices = group_frame.index.to_list()
                if not indices:
                    continue
                group_values = np.abs(values[indices]).mean(axis=0)
                groups_payload[protected][str(group_name)] = [
                    {"feature": feature, "importance": round(float(group_values[idx]), 4)}
                    for idx, feature in enumerate(numeric_frame.columns)
                ][:10]
        return {
            "global": [
                {"feature": feature, "importance": round(float(global_importance[idx]), 4)}
                for idx, feature in enumerate(numeric_frame.columns)
            ][:10],
            "by_group": groups_payload,
        }
    except Exception:
        if hasattr(loaded_model, "feature_importances_"):
            raw = getattr(loaded_model, "feature_importances_")
        elif hasattr(loaded_model, "coef_"):
            raw = np.ravel(getattr(loaded_model, "coef_"))
        else:
            raw = np.zeros(len(numeric_frame.columns))
        return {
            "global": [
                {"feature": feature, "importance": round(float(abs(raw[idx])), 4)}
                for idx, feature in enumerate(numeric_frame.columns)
            ][:10],
            "by_group": {},
        }

