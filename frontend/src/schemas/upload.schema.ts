import { z } from "zod";

export const uploadWizardSchema = z.object({
  datasetFile: z.instanceof(File, { message: "Choose a dataset file." }),
  modelFile: z.instanceof(File).optional(),
  targetColumn: z.string().min(1, "Select the target column."),
  protectedColumns: z.array(z.string()).min(1, "Select at least one protected attribute."),
  positiveLabel: z.string().min(1, "Provide the positive outcome label."),
  predictionColumn: z.string().optional(),
  scoreColumn: z.string().optional(),
});

export type UploadWizardValues = z.infer<typeof uploadWizardSchema>;

