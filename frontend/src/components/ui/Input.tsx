import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { label, error, hint, id, className, ...rest },
  ref,
) {
  const inputId = id ?? rest.name;
  return (
    <div className="space-y-1">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-medium uppercase tracking-wide text-muted"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        ref={ref}
        className={cn(
          "w-full rounded-md border bg-surface2 px-3 py-2 text-sm text-text placeholder-dim focus:outline-none",
          error ? "border-red focus:border-red" : "border-border focus:border-accent",
          className,
        )}
        {...rest}
      />
      {error ? (
        <p className="text-xs text-red">{error}</p>
      ) : hint ? (
        <p className="text-xs text-muted">{hint}</p>
      ) : null}
    </div>
  );
});
