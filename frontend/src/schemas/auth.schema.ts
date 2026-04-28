import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(8, "Password must be at least 8 characters."),
});

export const registerSchema = loginSchema.extend({
  role: z.enum(["admin", "analyst", "viewer"]).default("analyst"),
});

export const resetPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address."),
});

export const resetPasswordConfirmSchema = z.object({
  token: z.string().min(10, "Reset token is required."),
  new_password: z.string().min(8, "Password must be at least 8 characters."),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;

