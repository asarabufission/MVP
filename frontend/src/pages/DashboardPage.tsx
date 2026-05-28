import {
  Activity,
  AlertTriangle,
  Database,
  FileBarChart,
  FilePlus2,
  Inbox,
  Plus,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { RoleGuard } from "@/components/RoleGuard";
import { Badge, statusToTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Table, type Column } from "@/components/ui/Table";
import { useDashboardSummary } from "@/hooks/useDashboard";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import { DASHBOARD_ACTIVITY_TABLE_SCROLL_MAX } from "@/lib/layout";
import { useAuthStore } from "@/stores/auth-store";
import type { RecentActivityItem } from "@/types/api";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: number | string;
  to: string;
}

function StatCard({ icon: Icon, label, value, to }: StatCardProps) {
  const navigate = useNavigate();
  return (
    <button
      type="button"
      onClick={() => navigate(to)}
      className={cn(
        "group flex flex-col items-start gap-3 rounded-lg border border-border bg-surface p-5 text-left transition-colors hover:border-accent/60 hover:bg-surface/80",
      )}
    >
      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent/15 text-accent">
        <Icon className="h-5 w-5" aria-hidden />
      </div>
      <div>
        <p className="text-3xl font-semibold tabular-nums text-text">{value}</p>
        <p className="mt-1 text-xs uppercase tracking-wide text-muted">
          {label}
        </p>
      </div>
    </button>
  );
}

const ACTIVITY_COLUMNS: Column<RecentActivityItem>[] = [
  {
    key: "status",
    header: "Status",
    render: (row) => (
      <Badge tone={statusToTone(row.status)}>{row.status}</Badge>
    ),
  },
  {
    key: "datasourceName",
    header: "Datasource",
    render: (row) => row.datasourceName ?? "—",
  },
  {
    key: "clientName",
    header: "Client",
    render: (row) => row.clientName ?? "—",
  },
  { key: "type", header: "Type" },
  {
    key: "startedAt",
    header: "Started",
    render: (row) => (
      <span className="text-muted">{formatDateTime(row.startedAt)}</span>
    ),
  },
  {
    key: "records",
    header: "Records",
    className: "text-right tabular-nums",
    headerClassName: "text-right",
    render: (row) => (row.records == null ? "—" : row.records.toLocaleString()),
  },
];

export function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { data, isLoading, isError } = useDashboardSummary();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        {user && (
          <p className="mt-1 text-sm text-muted">
            Welcome, {user.fullName ?? user.email}
          </p>
        )}
      </div>

      {isLoading && (
        <Card>
          <p className="text-sm text-muted">Loading dashboard…</p>
        </Card>
      )}

      {isError && (
        <Card>
          <p className="text-sm text-red">Failed to load dashboard summary.</p>
        </Card>
      )}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              icon={Users}
              label="Clients Ready"
              value={data.clientsReady}
              to="/clients"
            />
            <StatCard
              icon={Database}
              label="Active Datasources"
              value={`${data.activeDatasources} / ${data.totalDatasources}`}
              to="/datasources"
            />
            <StatCard
              icon={Activity}
              label="Recent Job Runs"
              value={data.recentRunsCount}
              to="/job-runs"
            />
            <StatCard
              icon={FileBarChart}
              label="Reports Generated"
              value={data.reportsGenerated}
              to="/reports/history"
            />
          </div>

          {data.failedRuns.length > 0 && (
            <div className="rounded-lg border border-red/40 bg-red/10 p-5">
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 flex-none items-center justify-center rounded-md bg-red/20 text-red">
                  <AlertTriangle className="h-5 w-5" aria-hidden />
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-red">
                    {data.failedRuns.length} failed run
                    {data.failedRuns.length === 1 ? "" : "s"} in the last 48
                    hours
                  </h3>
                  <p className="mt-1 text-sm text-text">
                    <span className="font-medium">
                      {data.failedRuns[0].datasourceName ?? "Unknown source"}
                    </span>
                    {data.failedRuns[0].error && (
                      <>
                        {" — "}
                        <span className="text-muted">
                          {data.failedRuns[0].error}
                        </span>
                      </>
                    )}
                  </p>
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/job-runs?status=FAILED&focusId=${data.failedRuns[0].id}`,
                      )
                    }
                    className="mt-2 text-xs font-medium text-accent hover:underline"
                  >
                    View in Job Runs →
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="primary"
              leftIcon={<FilePlus2 className="h-4 w-4" />}
              onClick={() => navigate("/reports")}
            >
              Generate Report
            </Button>
            <RoleGuard role="MSP_ADMIN">
              <Button
                variant="secondary"
                leftIcon={<Plus className="h-4 w-4" />}
                onClick={() => navigate("/datasources/add")}
              >
                Add Datasource
              </Button>
            </RoleGuard>
            <RoleGuard role="MSP_ADMIN">
              <Button
                variant="secondary"
                leftIcon={<Plus className="h-4 w-4" />}
                onClick={() => navigate("/clients")}
              >
                Add Client
              </Button>
            </RoleGuard>
          </div>

          <Card title="Recent Activity" padded={false}>
            <Table<RecentActivityItem>
              columns={ACTIVITY_COLUMNS}
              rows={data.recentActivity}
              keyFn={(r) => r.id}
              scrollable
              scrollMaxHeight={DASHBOARD_ACTIVITY_TABLE_SCROLL_MAX}
              emptyState={
                <EmptyState
                  icon={Inbox}
                  title="No job runs yet"
                  description="Activated datasources will start showing scheduled runs here."
                />
              }
            />
          </Card>
        </>
      )}
    </div>
  );
}
