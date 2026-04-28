from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.models.enums import SeverityLevel
from app.services.bias_engine.orchestrator import BiasAuditEngine
from app.services.bias_engine.schemas import AuditInput

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load_fixture(name: str) -> pd.DataFrame:
    return pd.read_csv(FIXTURES / name)


def test_known_biased_dataset_flags_red_metrics() -> None:
    dataframe = load_fixture("adult_census_biased.csv")
    engine = BiasAuditEngine()
    result = engine.run(
        AuditInput(
            dataframe=dataframe,
            target_column="hired",
            prediction_column="predicted_hired",
            score_column="score",
            protected_columns=["gender", "race"],
            positive_label=1,
        )
    )
    metric_map = {f"{metric.metric_name}:{metric.group_name}": metric for metric in result.metrics}
    assert metric_map["disparate_impact_ratio:gender"].severity == SeverityLevel.RED
    assert metric_map["statistical_parity_difference:gender"].severity in {
        SeverityLevel.AMBER,
        SeverityLevel.RED,
    }
    assert result.bias_risk_score > 50


def test_balanced_dataset_passes_core_metrics() -> None:
    dataframe = load_fixture("synthetic_balanced.csv")
    engine = BiasAuditEngine()
    result = engine.run(
        AuditInput(
            dataframe=dataframe,
            target_column="approved",
            prediction_column="predicted_approved",
            score_column="score",
            protected_columns=["gender", "race"],
            positive_label=1,
        )
    )
    severities = {metric.metric_name: metric.severity for metric in result.metrics}
    assert severities["individual_fairness_score"] in {SeverityLevel.GREEN, SeverityLevel.AMBER}
    assert severities["disparate_impact_ratio"] == SeverityLevel.GREEN
    assert result.bias_risk_score < 45


def test_counterfactual_analysis_is_attached_to_prediction_audits() -> None:
    dataframe = load_fixture("adult_census_biased.csv")
    engine = BiasAuditEngine()
    result = engine.run(
        AuditInput(
            dataframe=dataframe,
            target_column="hired",
            prediction_column="predicted_hired",
            score_column="score",
            protected_columns=["gender", "race"],
            positive_label=1,
        )
    )
    counterfactual_metrics = [
        metric for metric in result.metrics if metric.metric_name == "counterfactual_flip_rate"
    ]
    assert {metric.group_name for metric in counterfactual_metrics} == {"gender", "race"}
    assert len(result.counterfactual) == 2
    assert all(0 <= assessment.flip_rate <= 1 for assessment in result.counterfactual)


def test_single_group_dataset_handles_edge_case() -> None:
    dataframe = load_fixture("synthetic_balanced.csv").query("gender == 'F'").copy()
    engine = BiasAuditEngine()
    result = engine.run(
        AuditInput(
            dataframe=dataframe,
            target_column="approved",
            protected_columns=["gender"],
            positive_label=1,
        )
    )
    assert result.metrics[0].comparison is not None
    assert result.metrics[0].comparison.privileged_group == "F"
    assert result.metrics[0].comparison.unprivileged_group == "F"


def test_zero_positive_outcome_group_does_not_crash() -> None:
    dataframe = load_fixture("adult_census_biased.csv").copy()
    dataframe.loc[dataframe["gender"] == "F", "predicted_hired"] = 0
    engine = BiasAuditEngine()
    result = engine.run(
        AuditInput(
            dataframe=dataframe,
            target_column="hired",
            prediction_column="predicted_hired",
            protected_columns=["gender"],
            positive_label=1,
        )
    )
    equal_opportunity = [
        metric for metric in result.metrics if metric.metric_name == "equal_opportunity_difference"
    ][0]
    assert equal_opportunity.value <= 0


def test_nan_values_in_protected_column_are_grouped_as_unknown() -> None:
    dataframe = load_fixture("adult_census_biased.csv").copy()
    dataframe.loc[0, "gender"] = None
    engine = BiasAuditEngine()
    result = engine.run(
        AuditInput(
            dataframe=dataframe,
            target_column="hired",
            protected_columns=["gender"],
            positive_label=1,
        )
    )
    distribution_groups = result.distributions[0].groups
    assert any(row["group"] == "Unknown" for row in distribution_groups)
