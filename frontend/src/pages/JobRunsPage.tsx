import { Activity, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { RoleGuard } from "@/components/RoleGuard";
import { Badge, statusToTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import {
  useJobRuns,
  type JobRunStatusFilter,
} from "@/hooks/useJobRuns";
import { cn } from "@/lib/cn";
import { formatDateTimeCompact } from "@/lib/format";
import { JOB_RUNS_TABLE_SCROLL_MAX } from "@/lib/layout";
import { useUiStore } from "@/stores/ui-store";
import type { JobRunListItem } from "@/types/api";

const PAGE_SIZE = 10;

const STATUS_OPTIONS: { value: JobRunStatusFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "SUCCESS", label: "Success" },
  { value: "FAILED", label: "Failed" },
  { value: "RUNNING", label: "Running" },
  { value: "PARTIAL", label: "Partial" },
];

function statusDotClass(status: string): string {
  switch (status.toUpperCase()) {
    case "SUCCESS":
      return "bg-green";
    case "FAILED":
      return "bg-red";
    case "RUNNING":
      return "bg-amber animate-pulse";
    case "QUEUED":
    case "PARTIAL":
      return "bg-accent";
    default:
      return "bg-dim";
  }
}

function jobTypeLabel(jobType: string): { label: string; tone: "amber" | "blue" } {
  const upper = jobType.toUpperCase();
  if (upper === "MANUAL" || upper.includes("FILE")) {
    return { label: "FILE UPLOAD", tone: "amber" };
  }
  if (upper === "TEST_CONNECTION") {
    return { label: "TEST", tone: "blue" };
  }
  if (upper === "ACTIVATION") {
    return { label: "ACTIVATION", tone: "blue" };
  }
  if (upper === "REPORT_GENERATION") {
    return { label: "REPORT", tone: "blue" };
  }
  return { label: "SCHEDULED", tone: "blue" };
}

function datasourceShortName(name: string | null): string {
  if (!name) return "—";
  const parts = name.split(" — ");
  return parts[0] ?? name;
}

export function JobRunsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const pushToast = useUiStore((s) => s.pushToast);
  const initialStatus = (searchParams.get("status")?.toUpperCase() ??
    "ALL") as JobRunStatusFilter;
  const focusId = searchParams.get("focusId");

  const [statusFilter, setStatusFilter] =
    useState<JobRunStatusFilter>(initialStatus);
  const [page, setPage] = useState(0);

  useEffect(() => {
    const fromUrl = (searchParams.get("status")?.toUpperCase() ??
      "ALL") as JobRunStatusFilter;
    setStatusFilter(fromUrl);
  }, [searchParams]);

  const { data, isLoading, isError, refetch, isFetching } = useJobRuns(
    statusFilter,
    100,
  );

  const rows = data ?? [];

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const from = rows.length === 0 ? 0 : page * PAGE_SIZE + 1;
  const to = Math.min((page + 1) * PAGE_SIZE, rows.length);

  useEffect(() => {
    setPage(0);
  }, [statusFilter]);

  useEffect(() => {
    if (!focusId || pageRows.length === 0) return;
    const el = document.getElementById(`job-run-${focusId}`);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [focusId, pageRows]);

  const onStatusChange = (value: string) => {
    const next = value as JobRunStatusFilter;
    setStatusFilter(next);
    const params = new URLSearchParams(searchParams);
    if (next === "ALL") params.delete("status");
    else params.set("status", next);
    setSearchParams(params, { replace: true });
  };

  const onRetry = (row: JobRunListItem) => {
    pushToast({
      type: "info",
      message: `Retry for ${datasourceShortName(row.datasourceName)} is not wired to the API yet.`,
    });
  };

  const columns: Column<JobRunListItem>[] = useMemo(
    () => [
      {
        key: "status",
        header: "Status",
        render: (row) => (
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "inline-block h-2 w-2 shrink-0 rounded-full",
                statusDotClass(row.status),
              )}
              aria-hidden
            />
            <Badge tone={statusToTone(row.status)}>{row.status}</Badge>
          </div>
        ),
      },
      {
        key: "datasource",
        header: "Datasource",
        render: (row) => (
          <span className="font-medium">{datasourceShortName(row.datasourceName)}</span>
        ),
      },
      {
        key: "client",
        header: "Client",
        render: (row) => (
          <span className="text-muted">{row.clientName ?? "—"}</span>
        ),
      },
      {
        key: "type",
        header: "Type",
        render: (row) => {
          const { label, tone } = jobTypeLabel(row.jobType);
          return <Badge tone={tone}>{label}</Badge>;
        },
      },
      {
        key: "time",
        header: "Time",
        render: (row) => (
          <span className="font-mono text-xs text-dim">
            {formatDateTimeCompact(row.startedAt)}
          </span>
        ),
      },
      {
        key: "records",
        header: "Records",
        className: "font-mono text-sm tabular-nums",
        render: (row) =>
          row.records == null || row.records === 0 ? "—" : row.records.toLocaleString(),
      },
      {
        key: "error",
        header: "Error Details",
        render: (row) =>
          row.errorMessage ? (
            <p
              className={cn(
                "max-w-xs text-xs leading-relaxed",
                row.status === "RUNNING"
                  ? "text-amber"
                  : row.status === "FAILED"
                    ? "text-red"
                    : "text-muted",
              )}
            >
              {row.errorMessage}
            </p>
          ) : (
            <span className="text-dim">—</span>
          ),
      },
      {
        key: "actions",
        header: "",
        className: "w-24 text-right",
        headerClassName: "text-right",
        render: (row) =>
          row.status === "FAILED" ? (
            <RoleGuard role="MSP_ADMIN">
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
                onClick={() => onRetry(row)}
              >
                Retry
              </Button>
            </RoleGuard>
          ) : null,
      },
    ],
    [pushToast],
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Job Runs</h1>
        {/* <Button
          variant="secondary"
          size="sm"
          leftIcon={<RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />}
          onClick={() => refetch()}
          disabled={isFetching}
        >
          Refresh
        </Button> */}
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <div className="w-44">
          <Select
            label="Status"
            value={statusFilter}
            onChange={(e) => onStatusChange(e.target.value)}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {isLoading && (
        <Card>
          <p className="text-sm text-muted">Loading job runs…</p>
        </Card>
      )}

      {isError && (
        <Card>
          <p className="text-sm text-red">Failed to load job runs.</p>
        </Card>
      )}

      {!isLoading && !isError && (
        <Card padded={false} className="flex max-w-full flex-col overflow-hidden">
          <Table<JobRunListItem>
            columns={columns}
            rows={pageRows}
            keyFn={(r) => r.id}
            scrollable
            scrollMaxHeight={JOB_RUNS_TABLE_SCROLL_MAX}
            rowId={(r) => `job-run-${r.id}`}
            rowClassName={(r) =>
              cn(
                r.status === "FAILED" && "bg-red/5",
                focusId === r.id && "bg-accent/10 ring-1 ring-inset ring-accent/30",
              )
            }
            emptyState={
              <EmptyState
                icon={Activity}
                title="No job runs"
                description={
                  statusFilter === "ALL"
                    ? "Scheduled ingestions and connection tests will appear here."
                    : `No runs with status ${statusFilter}.`
                }
              />
            }
          />
          {rows.length > 0 && (
            <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted">
              <span>
                Showing {from}–{to} of {rows.length}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  « Prev
                </Button>
                <span className="tabular-nums">
                  {page + 1} / {totalPages}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                >
                  Next »
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

    </div>
  );
}
