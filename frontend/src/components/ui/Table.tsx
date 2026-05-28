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
  rowId?: (row: T) => string | undefined;
  rowClassName?: (row: T) => string | undefined;
  /** Sticky header + vertical/horizontal scroll inside max height */
  scrollable?: boolean;
  scrollMaxHeight?: string;
}

export function Table<T>({
  columns,
  rows,
  keyFn,
  emptyState,
  onRowClick,
  rowId,
  rowClassName,
  scrollable = false,
  scrollMaxHeight = "max-h-60",
}: Props<T>) {
  if (rows.length === 0 && emptyState) {
    return <div className="py-8">{emptyState}</div>;
  }

  const wrapClass = scrollable
    ? cn("overflow-auto", scrollMaxHeight)
    : "overflow-x-auto";

  const headRowClass = scrollable
    ? "sticky top-0 z-10 bg-surface2 text-left text-[11px] font-medium uppercase tracking-wide text-muted shadow-[0_1px_0_0_rgba(42,46,59,1)]"
    : "bg-surface2 text-left text-[11px] font-medium uppercase tracking-wide text-muted";

  return (
    <div className={wrapClass}>
      <table className="min-w-full text-sm">
        <thead>
          <tr className={headRowClass}>
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
                id={rowId?.(row)}
                onClick={clickable ? () => onRowClick?.(row) : undefined}
                className={cn(
                  "border-t border-border/60 text-text",
                  idx % 2 === 1 && "bg-surface2/30",
                  clickable && "cursor-pointer hover:bg-surface2/60",
                  rowClassName?.(row),
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
