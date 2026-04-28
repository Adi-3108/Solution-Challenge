from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SeverityLevel


class ThresholdBand(BaseModel):
    green: tuple[float, float] | None = None
    amber: tuple[float, float] | None = None
    lower_is_better: bool = False
    higher_is_better: bool = False


class BiasThresholdConfig(BaseModel):
    disparate_impact_lower: float = 0.8
    disparate_impact_upper: float = 1.25
    parity_green: float = 0.1
    parity_amber: float = 0.2
    equal_opportunity_green: float = 0.1
    equal_opportunity_amber: float = 0.2
    average_odds_green: float = 0.1
    average_odds_amber: float = 0.2
    predictive_parity_green: float = 0.1
    predictive_parity_amber: float = 0.2
    individual_fairness_green: float = 0.9
    individual_fairness_amber: float = 0.75
    calibration_error_green: float = 0.05
    calibration_error_amber: float = 0.1
    proxy_correlation_threshold: float = 0.7
    counterfactual_flip_rate_green: float = 0.05
    counterfactual_flip_rate_amber: float = 0.15


class GroupComparison(BaseModel):
    protected_attribute: str
    privileged_group: str
    unprivileged_group: str


class MetricResult(BaseModel):
    metric_name: str
    display_name: str
    group_name: str
    value: float
    severity: SeverityLevel
    threshold_used: float
    explanation: str
    comparison: GroupComparison | None = None
    affected_group: str | None = None
    recommended_action: str | None = None
    intersectional_groups: dict[str, str] = Field(default_factory=dict)
    details: dict[str, object] = Field(default_factory=dict)


class ProxyVariableFinding(BaseModel):
    protected_attribute: str
    candidate_column: str
    correlation: float
    severity: SeverityLevel


class DistributionSeries(BaseModel):
    protected_attribute: str
    groups: list[dict[str, object]]


class RemediationSnippet(BaseModel):
    title: str
    strategy: str
    summary: str
    affected_group: str
    metric_name: str
    before_value: float
    after_value: float
    chart_points: list[dict[str, float]]
    code_snippet: str


class CounterfactualTransition(BaseModel):
    from_group: str
    to_group: str
    tested: int
    flipped: int
    flip_rate: float


class CounterfactualSample(BaseModel):
    row_index: int
    from_group: str
    to_group: str
    original_prediction: int
    counterfactual_prediction: int


class CounterfactualAssessment(BaseModel):
    protected_attribute: str
    flip_rate: float
    affected_records: int
    affected_record_rate: float
    tested_pairs: int
    source: str
    severity: SeverityLevel
    transition_summary: list[CounterfactualTransition]
    sample_flips: list[CounterfactualSample]


class DriftMetricChange(BaseModel):
    metric_name: str
    display_name: str
    group_name: str
    intersectional_groups: dict[str, str] = Field(default_factory=dict)
    current_value: float
    previous_value: float
    delta: float
    current_severity: SeverityLevel
    previous_severity: SeverityLevel
    direction: str


class DriftRiskPoint(BaseModel):
    run_id: str
    label: str
    completed_at: str
    bias_risk_score: float
    model_label: str
    period_label: str


class DriftPeriodSummary(BaseModel):
    period: str
    average_risk_score: float
    runs: int


class DriftModelVersionSummary(BaseModel):
    model_id: str | None = None
    model_label: str
    average_risk_score: float
    latest_risk_score: float
    latest_completed_at: str | None = None
    runs: int


class DriftAlert(BaseModel):
    title: str
    body: str
    severity: SeverityLevel


class DriftSummary(BaseModel):
    trend_status: str
    risk_delta: float | None
    compared_run_id: str | None = None
    compared_completed_at: str | None = None
    risk_history: list[DriftRiskPoint]
    period_summary: list[DriftPeriodSummary]
    model_versions: list[DriftModelVersionSummary]
    metric_drift: list[DriftMetricChange]
    alerts: list[DriftAlert]


class BiasAuditResult(BaseModel):
    bias_risk_score: float
    metrics: list[MetricResult]
    distributions: list[DistributionSeries]
    missing_data_rates: dict[str, list[dict[str, float | str]]]
    proxy_findings: list[ProxyVariableFinding]
    proxy_matrix: dict[str, dict[str, float]]
    shap_payload: dict[str, object]
    confusion_matrices: dict[str, dict[str, int]]
    calibration_curves: dict[str, list[dict[str, float]]]
    roc_curves: dict[str, list[dict[str, float]]]
    intersectionality: list[MetricResult]
    counterfactual: list[CounterfactualAssessment]
    recommendations: list[RemediationSnippet]
    explanations: dict[str, str]
    summary: dict[str, object]


class AuditInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    dataframe: object
    target_column: str
    protected_columns: list[str]
    positive_label: str | int | float | bool
    prediction_column: str | None = None
    score_column: str | None = None
    thresholds: BiasThresholdConfig = Field(default_factory=BiasThresholdConfig)
    loaded_model: object | None = None

    @classmethod
    def model_validate_mapping(cls, payload: Mapping[str, object]) -> "AuditInput":
        return cls.model_validate(dict(payload))
