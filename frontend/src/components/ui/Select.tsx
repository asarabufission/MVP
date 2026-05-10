import { forwardRef, type SelectHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Select = forwardRef<HTMLSelectElement, Props>(function Select(
  { label, error, hint, id, className, children, ...rest },
  ref,
) {
  const selectId = id ?? rest.name;
  return (
    <div className="space-y-1">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-xs font-medium uppercase tracking-wide text-muted"
        >
          {label}
        </label>
      )}
      <select
        id={selectId}
        ref={ref}
        className={cn(
          "w-full rounded-md border bg-surface2 px-3 py-2 text-sm text-text focus:outline-none",
          error ? "border-red focus:border-red" : "border-border focus:border-accent",
          className,
        )}
        {...rest}
      >
        {children}
      </select>
      {error ? (
        <p className="text-xs text-red">{error}</p>
      ) : hint ? (
        <p className="text-xs text-muted">{hint}</p>
      ) : null}
    </div>
  );
});
