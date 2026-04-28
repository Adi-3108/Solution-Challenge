import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/Common/Button";
import { Card } from "@/components/Common/Card";
import { uploadWizardSchema, UploadWizardValues } from "@/schemas/upload.schema";
import { datasetsService } from "@/services/datasets.service";
import { runsService } from "@/services/runs.service";
import { parseLocalPreview } from "@/utils/filePreview";

type UploadWizardProps = {
  projectId: string;
  onCompleted: (runId: string) => void;
};

export const UploadWizard = ({ projectId, onCompleted }: UploadWizardProps) => {
  const [step, setStep] = useState(1);
  const [previewColumns, setPreviewColumns] = useState<string[]>([]);
  const [previewRows, setPreviewRows] = useState<Record<string, string>[]>([]);
  const form = useForm<UploadWizardValues>({
    resolver: zodResolver(uploadWizardSchema),
    defaultValues: {
      protectedColumns: [],
      positiveLabel: "1",
      predictionColumn: "",
      scoreColumn: "",
    },
  });

  const selectedDataset = form.watch("datasetFile");
  const selectedModel = form.watch("modelFile");
  const protectedColumns = form.watch("protectedColumns");

  const uploadMutation = useMutation({
    mutationFn: async (values: UploadWizardValues) => {
      const dataset = await datasetsService.uploadDataset({
        projectId,
        datasetFile: values.datasetFile,
        targetColumn: values.targetColumn,
        protectedColumns: values.protectedColumns,
        positiveLabel: values.positiveLabel,
        predictionColumn: values.predictionColumn,
        scoreColumn: values.scoreColumn,
      });
      const model = values.modelFile
        ? await datasetsService.uploadModel({ projectId, modelFile: values.modelFile })
        : null;
      const run = await runsService.create(projectId, {
        dataset_id: dataset.id,
        model_id: model?.id ?? null,
      });
      return run;
    },
    onSuccess: (run) => onCompleted(run.id),
  });

  const canAdvance = useMemo(() => !uploadMutation.isPending, [uploadMutation.isPending]);

  const handlePreview = async (file: File): Promise<void> => {
    const preview = await parseLocalPreview(file);
    setPreviewColumns(preview?.columns ?? []);
    setPreviewRows(preview?.rows ?? []);
  };

  const onSubmit = form.handleSubmit((values) => uploadMutation.mutate(values));

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        {[1, 2, 3].map((index) => (
          <div
            key={index}
            className={`flex-1 rounded-full px-4 py-2 text-center text-sm font-semibold ${
              index === step
                ? "bg-brand-600 text-white"
                : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            Step {index}
          </div>
        ))}
      </div>

      <form onSubmit={onSubmit} className="space-y-6">
        {step === 1 && (
          <Card className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Upload dataset</h2>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Upload CSV, JSON, or Parquet. FairSight will validate structure before accepting it.
              </p>
            </div>
            <label className="panel-muted flex cursor-pointer flex-col items-center gap-3 px-6 py-10 text-center">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-100">
                Drag a file here or click to browse
              </span>
              <input
                type="file"
                accept=".csv,.json,.parquet"
                className="hidden"
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (!file) {
                    return;
                  }
                  form.setValue("datasetFile", file, { shouldValidate: true });
                  await handlePreview(file);
                }}
              />
            </label>
            {selectedDataset && (
              <div className="space-y-3 rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
                <p className="font-medium text-slate-900 dark:text-white">{selectedDataset.name}</p>
                {previewColumns.length > 0 ? (
                  <>
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-left text-xs">
                        <thead>
                          <tr>
                            {previewColumns.map((column) => (
                              <th key={column} className="px-2 py-2 font-semibold text-slate-500">
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewRows.map((row, index) => (
                            <tr key={`${index}-${Object.values(row).join("-")}`}>
                              {previewColumns.map((column) => (
                                <td key={column} className="px-2 py-2 text-slate-600 dark:text-slate-300">
                                  {row[column]}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    Column preview is shown immediately for CSV and JSON files. Parquet files will be validated on upload.
                  </p>
                )}
              </div>
            )}
            {form.formState.errors.datasetFile && (
              <p className="text-sm text-rose-600">{form.formState.errors.datasetFile.message}</p>
            )}
          </Card>
        )}

        {step === 2 && (
          <Card className="space-y-5">
            <div>
              <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Configure audit</h2>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Choose the target outcome, protected attributes, and any optional prediction columns.
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="font-medium text-slate-700 dark:text-slate-100">Target column</span>
                <select className="button-secondary w-full justify-start" {...form.register("targetColumn")}>
                  <option value="">Select a column</option>
                  {previewColumns.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
                {form.formState.errors.targetColumn && (
                  <p className="text-sm text-rose-600">{form.formState.errors.targetColumn.message}</p>
                )}
              </label>
              <label className="space-y-2">
                <span className="font-medium text-slate-700 dark:text-slate-100">Positive label</span>
                <input className="button-secondary w-full justify-start text-left font-normal" {...form.register("positiveLabel")} />
                {form.formState.errors.positiveLabel && (
                  <p className="text-sm text-rose-600">{form.formState.errors.positiveLabel.message}</p>
                )}
              </label>
            </div>
            <fieldset className="space-y-3">
              <legend className="font-medium text-slate-700 dark:text-slate-100">Protected attributes</legend>
              <div className="grid gap-2 md:grid-cols-3">
                {previewColumns.map((column) => (
                  <label key={column} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-700">
                    <input
                      type="checkbox"
                      value={column}
                      onChange={(event) => {
                        const nextValues = event.target.checked
                          ? [...protectedColumns, column]
                          : protectedColumns.filter((value) => value !== column);
                        form.setValue("protectedColumns", nextValues, { shouldValidate: true });
                      }}
                    />
                    {column}
                  </label>
                ))}
              </div>
              {form.formState.errors.protectedColumns && (
                <p className="text-sm text-rose-600">{form.formState.errors.protectedColumns.message}</p>
              )}
            </fieldset>
            <div className="grid gap-4 md:grid-cols-3">
              <label className="space-y-2">
                <span className="font-medium text-slate-700 dark:text-slate-100">Prediction column</span>
                <select className="button-secondary w-full justify-start" {...form.register("predictionColumn")}>
                  <option value="">Optional</option>
                  {previewColumns.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-2">
                <span className="font-medium text-slate-700 dark:text-slate-100">Score column</span>
                <select className="button-secondary w-full justify-start" {...form.register("scoreColumn")}>
                  <option value="">Optional</option>
                  {previewColumns.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-2">
                <span className="font-medium text-slate-700 dark:text-slate-100">Model artifact</span>
                <input
                  type="file"
                  accept=".pkl,.joblib,.onnx"
                  className="button-secondary block w-full cursor-pointer p-3 font-normal"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) {
                      form.setValue("modelFile", file);
                    }
                  }}
                />
              </label>
            </div>
          </Card>
        )}

        {step === 3 && (
          <Card className="space-y-5">
            <div>
              <h2 className="text-lg font-semibold text-slate-950 dark:text-white">Review and launch</h2>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                Confirm the uploaded files and audit configuration, then start the asynchronous run.
              </p>
            </div>
            <dl className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
                <dt className="text-slate-500 dark:text-slate-400">Dataset</dt>
                <dd className="mt-1 font-medium text-slate-950 dark:text-white">{selectedDataset?.name}</dd>
              </div>
              <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
                <dt className="text-slate-500 dark:text-slate-400">Model</dt>
                <dd className="mt-1 font-medium text-slate-950 dark:text-white">
                  {selectedModel?.name ?? "No model artifact"}
                </dd>
              </div>
              <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
                <dt className="text-slate-500 dark:text-slate-400">Target column</dt>
                <dd className="mt-1 font-medium text-slate-950 dark:text-white">{form.getValues("targetColumn")}</dd>
              </div>
              <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-900/60">
                <dt className="text-slate-500 dark:text-slate-400">Protected attributes</dt>
                <dd className="mt-1 font-medium text-slate-950 dark:text-white">
                  {form.getValues("protectedColumns").join(", ")}
                </dd>
              </div>
            </dl>
          </Card>
        )}

        <div className="flex items-center justify-between">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setStep((value) => Math.max(1, value - 1))}
            disabled={step === 1}
          >
            Back
          </Button>
          {step < 3 ? (
            <Button
              type="button"
              onClick={async () => {
                const valid =
                  step === 1
                    ? await form.trigger(["datasetFile"])
                    : await form.trigger(["targetColumn", "protectedColumns", "positiveLabel"]);
                if (valid) {
                  setStep((value) => value + 1);
                }
              }}
              disabled={!canAdvance}
            >
              Continue
            </Button>
          ) : (
            <Button type="submit" disabled={uploadMutation.isPending}>
              {uploadMutation.isPending ? "Launching audit..." : "Launch audit"}
            </Button>
          )}
        </div>
      </form>
    </div>
  );
};
