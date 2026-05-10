import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface Column<T> {
  key: string;
  header: ReactNode;
  render?: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  keyFn: (row: T) => string;
  emptyState?: ReactNode;
  onRowClick?: (row: T) => void;
}

export function Table<T>({
  columns,
  rows,
  keyFn,
  emptyState,
  onRowClick,
}: Props<T>) {
  if (rows.length === 0 && emptyState) {
    return <div className="py-8">{emptyState}</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-surface2 text-left text-[11px] font-medium uppercase tracking-wide text-muted">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn("px-4 py-2.5", col.headerClassName)}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => {
            const k = keyFn(row);
            const clickable = Boolean(onRowClick);
            return (
              <tr
                key={k}
                onClick={clickable ? () => onRowClick?.(row) : undefined}
                className={cn(
                  "border-t border-border/60 text-text",
                  idx % 2 === 1 && "bg-surface2/30",
                  clickable && "cursor-pointer hover:bg-surface2/60",
                )}
              >
                {columns.map((col) => {
                  const value =
                    col.render?.(row) ??
                    (row as Record<string, unknown>)[col.key];
                  return (
                    <td key={col.key} className={cn("px-4 py-3", col.className)}>
                      {value as ReactNode}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
