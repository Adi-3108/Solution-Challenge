import { z } from "zod";

export const projectSchema = z.object({
  name: z.string().min(3, "Project name must be at least 3 characters."),
  description: z.string().max(2000, "Description is too long.").optional().or(z.literal("")),
});

export type ProjectValues = z.infer<typeof projectSchema>;

