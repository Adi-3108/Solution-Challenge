from __future__ import annotations

import pandas as pd

from app.models.enums import SeverityLevel
from app.services.bias_engine.constants import DEFAULT_METRIC_WEIGHTS, SEVERITY_SCORES
from app.services.bias_engine.counterfactual import counterfactual_fairness_analysis
from app.services.bias_engine.data_analysis import (
    class_distribution_by_group,
    disparate_impact_and_parity,
    individual_fairness_metric,
    missing_data_rates,
    proxy_variable_detection,
)
from app.services.bias_engine.explainability import compute_shap_payload
from app.services.bias_engine.intersectional import compute_intersectional_metrics
from app.services.bias_engine.model_analysis import compute_model_metrics
from app.services.bias_engine.remediation import remediation_recommendations
from app.services.bias_engine.schemas import AuditInput, BiasAuditResult, MetricResult


class BiasAuditEngine:
    def run(self, audit_input: AuditInput) -> BiasAuditResult:
        dataframe = self._prepare_dataframe(audit_input.dataframe)
        metrics = self._dataset_metrics(dataframe, audit_input)
        confusion = {}
        calibration = {}
        roc = {}
        if audit_input.prediction_column:
            model_metrics, confusion, calibration, roc = compute_model_metrics(
                dataframe=dataframe,
                target_column=audit_input.target_column,
                prediction_column=audit_input.prediction_column,
                protected_columns=audit_input.protected_columns,
                positive_label=audit_input.positive_label,
                thresholds=audit_input.thresholds,
                score_column=audit_input.score_column,
            )
            metrics.extend(model_metrics)
        counterfactual_metrics, counterfactual_assessments = counterfactual_fairness_analysis(
            dataframe,
            audit_input,
        )
        metrics.extend(counterfactual_metrics)
        shap_payload = compute_shap_payload(
            audit_input.loaded_model,
            dataframe,
            audit_input.protected_columns,
            audit_input.target_column,
            audit_input.prediction_column,
            audit_input.score_column,
        )
        proxy_findings, proxy_matrix = proxy_variable_detection(
            dataframe, audit_input.protected_columns, audit_input.thresholds
        )
        intersections = compute_intersectional_metrics(
            dataframe,
            audit_input.target_column,
            audit_input.protected_columns,
            audit_input.positive_label,
            audit_input.thresholds,
        )
        recommendations = remediation_recommendations(metrics + intersections)
        summary = self._build_summary(metrics, intersections, proxy_findings, counterfactual_assessments)
        return BiasAuditResult(
            bias_risk_score=self._risk_score(metrics + intersections),
            metrics=metrics,
            distributions=class_distribution_by_group(
                dataframe,
                audit_input.protected_columns,
                audit_input.target_column,
                audit_input.positive_label,
            ),
            missing_data_rates=missing_data_rates(dataframe, audit_input.protected_columns),
            proxy_findings=proxy_findings,
            proxy_matrix=proxy_matrix,
            shap_payload=shap_payload,
            confusion_matrices=confusion,
            calibration_curves=calibration,
            roc_curves=roc,
            intersectionality=intersections,
            counterfactual=counterfactual_assessments,
            recommendations=recommendations,
            explanations={metric.metric_name: metric.explanation for metric in metrics},
            summary=summary,
        )

    def _prepare_dataframe(self, dataframe: object) -> pd.DataFrame:
        if isinstance(dataframe, pd.DataFrame):
            return dataframe.copy().reset_index(drop=True)
        raise TypeError("AuditInput.dataframe must be a pandas DataFrame")

    def _dataset_metrics(self, dataframe: pd.DataFrame, audit_input: AuditInput) -> list[MetricResult]:
        metrics: list[MetricResult] = []
        for protected in audit_input.protected_columns:
            metrics.extend(
                disparate_impact_and_parity(
                    dataframe,
                    protected,
                    audit_input.target_column,
                    audit_input.positive_label,
                    audit_input.thresholds,
                )
            )
        metrics.append(
            individual_fairness_metric(
                dataframe,
                audit_input.target_column,
                audit_input.protected_columns,
                audit_input.positive_label,
                audit_input.thresholds,
                audit_input.prediction_column,
                audit_input.score_column,
            )
        )
        return metrics

    def _risk_score(self, metrics: list[MetricResult]) -> float:
        if not metrics:
            return 0.0
        weighted_total = 0.0
        total_weight = 0.0
        for metric in metrics:
            weight = DEFAULT_METRIC_WEIGHTS.get(metric.metric_name, 1.0)
            weighted_total += SEVERITY_SCORES[metric.severity] * weight
            total_weight += weight
        return round(weighted_total / total_weight, 2)

    def _build_summary(
        self,
        metrics: list[MetricResult],
        intersections: list[MetricResult],
        proxy_findings: list[object],
        counterfactual_assessments: list[object],
    ) -> dict[str, object]:
        red_count = len([metric for metric in metrics if metric.severity == SeverityLevel.RED])
        amber_count = len([metric for metric in metrics if metric.severity == SeverityLevel.AMBER])
        critical = sorted(metrics + intersections, key=lambda item: abs(item.value), reverse=True)[:3]
        return {
            "red_issues": red_count,
            "amber_issues": amber_count,
            "proxy_flags": len(proxy_findings),
            "counterfactual_flags": len(
                [item for item in counterfactual_assessments if item.severity != SeverityLevel.GREEN]
            ),
            "top_issues": [item.model_dump() for item in critical],
        }
