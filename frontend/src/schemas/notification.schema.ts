import { z } from "zod";

export const notificationSchema = z.object({
  type: z.enum(["email", "webhook"]),
  destination: z.string().min(3, "Destination is required."),
  enabled: z.boolean(),
});

export const notificationUpdateSchema = z.object({
  notifications: z.array(notificationSchema),
});

