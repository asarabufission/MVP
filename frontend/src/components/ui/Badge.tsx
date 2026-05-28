import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type BadgeTone = "green" | "red" | "amber" | "gray" | "blue" | "purple";

const TONE: Record<BadgeTone, string> = {
  green: "border-green/40 bg-green/15 text-green",
  red: "border-red/40 bg-red/15 text-red",
  amber: "border-amber/40 bg-amber/15 text-amber",
  gray: "border-border bg-surface2 text-muted",
  blue: "border-accent/40 bg-accent/15 text-accent",
  purple: "border-licensing/40 bg-licensing/15 text-licensing",
};

interface Props {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
}

export function Badge({ tone = "gray", children, className }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide",
        TONE[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function statusToTone(status: string): BadgeTone {
  switch (status.toUpperCase()) {
    case "SUCCESS":
    case "ACTIVE":
    case "READY":
      return "green";
    case "FAILED":
    case "ERROR":
      return "red";
    case "RUNNING":
    case "PARTIAL":
    case "DEGRADED":
    case "PENDING":
      return "amber";
    case "ACTIVATING":
    case "QUEUED":
      return "blue";
    case "DRAFT":
    case "INACTIVE":
    case "DISABLED":
    default:
      return "gray";
  }
}
