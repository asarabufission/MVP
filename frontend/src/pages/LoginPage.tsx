import { zodResolver } from "@hookform/resolvers/zod";
import { AxiosError } from "axios";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuth } from "@/hooks/useAuth";
import type { ApiError } from "@/types/api";

const loginSchema = z.object({
  username: z.string().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean(),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "", rememberMe: false },
  });

  const onSubmit = async (values: LoginForm) => {
    setServerError(null);
    try {
      await login(values.username, values.password, values.rememberMe);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      const code = axiosError.response?.data?.code;
      if (code === "INVALID_CREDENTIALS") {
        setServerError("Invalid username or password");
      } else {
        setServerError("Something went wrong. Please try again.");
      }
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4 font-sans text-text">
      <div className="w-full max-w-sm rounded-xl border border-border bg-surface p-8 shadow-xl">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">MSP Guardian</h1>
          <p className="mt-1 text-sm text-muted">Sign in to your console</p>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <div>
            <label
              htmlFor="username"
              className="block text-xs font-medium uppercase tracking-wide text-muted"
            >
              Email
            </label>
            <input
              id="username"
              type="email"
              autoComplete="username"
              autoFocus
              {...register("username")}
              className="mt-1 w-full rounded-md border border-border bg-surface2 px-3 py-2 text-sm text-text placeholder-dim focus:border-accent focus:outline-none"
              placeholder="you@example.com"
            />
            {errors.username && (
              <p className="mt-1 text-xs text-red">{errors.username.message}</p>
            )}
          </div>
          <div>
            <label
              htmlFor="password"
              className="block text-xs font-medium uppercase tracking-wide text-muted"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register("password")}
              className="mt-1 w-full rounded-md border border-border bg-surface2 px-3 py-2 text-sm text-text placeholder-dim focus:border-accent focus:outline-none"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red">{errors.password.message}</p>
            )}
          </div>
          <label className="flex cursor-pointer items-center gap-2 text-xs text-muted">
            <input
              type="checkbox"
              {...register("rememberMe")}
              className="h-3.5 w-3.5 rounded border-border bg-surface2 text-accent focus:ring-accent/60"
            />
            <span>Remember me on this device</span>
          </label>
          {serverError && (
            <div
              role="alert"
              className="rounded-md border border-red/40 bg-red/10 px-3 py-2 text-xs text-red"
            >
              {serverError}
            </div>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-accent px-3 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
