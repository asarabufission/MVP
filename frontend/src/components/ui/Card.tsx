import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

interface Props extends Omit<HTMLAttributes<HTMLDivElement>, "title"> {
  title?: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  padded?: boolean;
}

export function Card({
  title,
  description,
  action,
  padded = true,
  children,
  className,
  ...rest
}: Props) {
  const hasHeader = Boolean(title || description || action);
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-surface",
        padded && !hasHeader && "p-5",
        className,
      )}
      {...rest}
    >
      {hasHeader && (
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-text">{title}</h3>}
            {description && (
              <p className="mt-1 text-xs text-muted">{description}</p>
            )}
          </div>
          {action}
        </div>
      )}
      <div className={cn(hasHeader ? "p-5" : padded ? "" : "p-0")}>{children}</div>
    </div>
  );
}
