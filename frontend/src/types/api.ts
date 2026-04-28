export type ApiMeta = {
  request_id: string;
  next_cursor?: string | null;
};

export type ApiResponse<T> = {
  data: T;
  meta: ApiMeta;
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export type UserRole = "admin" | "analyst" | "viewer";
export type RunStatus = "queued" | "running" | "completed" | "failed";
export type Severity = "green" | "amber" | "red";

export type User = {
  id: string;
  email: string;
  role: UserRole;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  user: User;
};

export type ProjectSummary = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  archived_at: string | null;
  last_run_date: string | null;
  last_run_status: RunStatus | null;
  risk_score: number | null;
  run_count: number;
};

export type DatasetRecord = {
  id: string;
  filename: string;
  file_hash: string;
  row_count: number;
  col_count: number;
  target_column: string;
  protected_columns: string[];
  positive_label: string;
  prediction_column: string | null;
  score_column: string | null;
  uploaded_at: string;
  expires_at: string;
  column_types: Record<string, string>;
};

export type ModelRecord = {
  id: string;
  filename: string;
  file_hash: string;
  model_type: "pkl" | "joblib" | "onnx";
  uploaded_at: string;
};

export type RunSummary = {
  id: string;
  project_id: string;
  dataset_id: string;
  model_id: string | null;
  status: RunStatus;
  bias_risk_score: number | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  stage_label: string;
  summary: Record<string, unknown>;
};

export type MetricResult = {
  id?: string;
  metric_name: string;
  display_name?: string;
  group_name: string;
  intersectional_groups?: Record<string, string>;
  value: number;
  severity: Severity;
  threshold_used: number;
  explanation: string;
  details?: Record<string, unknown>;
  comparison?: {
    protected_attribute: string;
    privileged_group: string;
    unprivileged_group: string;
  } | null;
};

export type DistributionSeries = {
  protected_attribute: string;
  groups: Array<{
    group: string;
    count: number;
    positive_rate: number;
  }>;
};

export type ProxyFinding = {
  protected_attribute: string;
  candidate_column: string;
  correlation: number;
  severity: Severity;
};

export type RemediationRecommendation = {
  title: string;
  strategy: string;
  summary: string;
  affected_group: string;
  metric_name: string;
  before_value: number;
  after_value: number;
  chart_points: Array<{ value: number; index: number }>;
  code_snippet: string;
};

export type CounterfactualTransition = {
  from_group: string;
  to_group: string;
  tested: number;
  flipped: number;
  flip_rate: number;
};

export type CounterfactualSample = {
  row_index: number;
  from_group: string;
  to_group: string;
  original_prediction: number;
  counterfactual_prediction: number;
};

export type CounterfactualAssessment = {
  protected_attribute: string;
  flip_rate: number;
  affected_records: number;
  affected_record_rate: number;
  tested_pairs: number;
  source: string;
  severity: Severity;
  transition_summary: CounterfactualTransition[];
  sample_flips: CounterfactualSample[];
};

export type DriftMetricChange = {
  metric_name: string;
  display_name: string;
  group_name: string;
  intersectional_groups: Record<string, string>;
  current_value: number;
  previous_value: number;
  delta: number;
  current_severity: Severity;
  previous_severity: Severity;
  direction: "improving" | "stable" | "regressing";
};

export type DriftRiskPoint = {
  run_id: string;
  label: string;
  completed_at: string;
  bias_risk_score: number;
  model_label: string;
  period_label: string;
};

export type DriftPeriodSummary = {
  period: string;
  average_risk_score: number;
  runs: number;
};

export type DriftModelVersionSummary = {
  model_id: string | null;
  model_label: string;
  average_risk_score: number;
  latest_risk_score: number;
  latest_completed_at: string | null;
  runs: number;
};

export type DriftAlert = {
  title: string;
  body: string;
  severity: Severity;
};

export type DriftSummary = {
  trend_status: "improving" | "stable" | "regressing" | "insufficient_history";
  risk_delta: number | null;
  compared_run_id: string | null;
  compared_completed_at: string | null;
  risk_history: DriftRiskPoint[];
  period_summary: DriftPeriodSummary[];
  model_versions: DriftModelVersionSummary[];
  metric_drift: DriftMetricChange[];
  alerts: DriftAlert[];
};

export type RunResultsPayload = {
  run: RunSummary;
  metrics: MetricResult[];
  shap: {
    global?: Array<{ feature: string; importance: number }>;
    by_group?: Record<string, Record<string, Array<{ feature: string; importance: number }>>>;
  };
  proxy: {
    matrix: Record<string, Record<string, number>>;
    findings: ProxyFinding[];
  };
  distributions: {
    distributions: DistributionSeries[];
    missing_data_rates: Record<string, Array<{ group: string; missing_rate: number }>>;
    confusion_matrices: Record<string, Record<string, number>>;
    calibration_curves: Record<string, Array<{ mean_score: number; positive_rate: number }>>;
    roc_curves: Record<string, Array<{ fpr: number; tpr: number }>>;
    intersectionality: MetricResult[];
  };
  counterfactual: CounterfactualAssessment[];
  recommendations: RemediationRecommendation[];
  summary: Record<string, unknown>;
  drift: DriftSummary;
};

export type ProjectDetail = ProjectSummary & {
  datasets: DatasetRecord[];
  models: ModelRecord[];
  runs: RunSummary[];
};

export type NotificationRecord = {
  id: string;
  project_id: string;
  type: "email" | "webhook";
  destination: string;
  enabled: boolean;
};

export type AuditLogRecord = {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ReportRecord = {
  id: string;
  run_id: string;
  format: "pdf" | "json";
  file_hash: string;
  generated_at: string;
};
