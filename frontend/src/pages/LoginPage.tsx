import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { AuthFormLayout } from "@/components/Auth/AuthForm";
import { Button } from "@/components/Common/Button";
import { loginSchema, LoginValues } from "@/schemas/auth.schema";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/stores/auth.store";

export const LoginPage = () => {
  const navigate = useNavigate();
  const { setUser } = useAuthStore();
  const form = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });
  const mutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (data) => {
      setUser(data.user);
      navigate("/dashboard");
    },
  });

  return (
    <AuthFormLayout
      title="Log in to FairSight"
      subtitle="Review data and model fairness with a calm, evidence-based workflow for analysts and compliance teams."
      footerLabel="Create an account"
      footerLink="/register"
      footerText="Need a workspace?"
    >
      <form onSubmit={form.handleSubmit((values) => mutation.mutate(values))} className="space-y-5">
        <label className="block space-y-2">
          <span className="font-medium text-slate-700 dark:text-slate-100">Email</span>
          <input className="button-secondary w-full justify-start text-left font-normal" {...form.register("email")} />
          {form.formState.errors.email && (
            <p className="text-sm text-rose-600">{form.formState.errors.email.message}</p>
          )}
        </label>
        <label className="block space-y-2">
          <span className="font-medium text-slate-700 dark:text-slate-100">Password</span>
          <input type="password" className="button-secondary w-full justify-start text-left font-normal" {...form.register("password")} />
          {form.formState.errors.password && (
            <p className="text-sm text-rose-600">{form.formState.errors.password.message}</p>
          )}
        </label>
        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Logging in..." : "Log in"}
        </Button>
      </form>
    </AuthFormLayout>
  );
};
