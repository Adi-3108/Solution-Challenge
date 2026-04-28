import { Card } from "@/components/Common/Card";
import { StatusBadge } from "@/components/Common/StatusBadge";
import { CounterfactualAssessment } from "@/types/api";
import { formatPercent } from "@/utils/format";

export const CounterfactualPanel = ({
  assessments,
}: {
  assessments: CounterfactualAssessment[];
}) => {
  if (assessments.length === 0) {
    return (
      <Card className="space-y-2">
        <h2 className="text-lg font-semibold text-slate-950 dark:text-white">
          Counterfactual fairness
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Counterfactual checks become available when the run includes recorded predictions or an
          uploaded model that can be replayed against hypothetical group changes.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {assessments.map((assessment) => (
        <Card key={assessment.protected_attribute} className="space-y-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Protected attribute
              </p>
              <h2 className="mt-1 text-lg font-semibold text-slate-950 dark:text-white">
                {assessment.protected_attribute}
              </h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                Source: {assessment.source}
              </p>
            </div>
            <StatusBadge severity={assessment.severity} />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Flip rate
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                {formatPercent(assessment.flip_rate)}
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Affected records
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                {assessment.affected_records}
              </p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {formatPercent(assessment.affected_record_rate)} of sampled rows
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Tested pairs
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                {assessment.tested_pairs}
              </p>
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-950 dark:text-white">
                Highest-risk transitions
              </h3>
              <div className="space-y-2">
                {assessment.transition_summary.map((transition) => (
                  <div
                    key={`${transition.from_group}-${transition.to_group}`}
                    className="rounded-xl bg-slate-50 p-3 dark:bg-slate-900/60"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium text-slate-900 dark:text-slate-100">
                        {transition.from_group} to {transition.to_group}
                      </p>
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {formatPercent(transition.flip_rate)}
                      </p>
                    </div>
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      {transition.flipped} flips across {transition.tested} tests
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-950 dark:text-white">
                Example flips
              </h3>
              {assessment.sample_flips.length > 0 ? (
                <div className="space-y-2">
                  {assessment.sample_flips.map((sample) => (
                    <div
                      key={`${sample.row_index}-${sample.from_group}-${sample.to_group}`}
                      className="rounded-xl bg-slate-50 p-3 text-sm text-slate-600 dark:bg-slate-900/60 dark:text-slate-300"
                    >
                      <p className="font-medium text-slate-900 dark:text-slate-100">
                        Row {sample.row_index}: {sample.from_group} to {sample.to_group}
                      </p>
                      <p className="mt-1">
                        Prediction changed from {sample.original_prediction} to{" "}
                        {sample.counterfactual_prediction}.
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl bg-slate-50 p-3 text-sm text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
                  No sampled rows changed under this attribute swap.
                </div>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};
