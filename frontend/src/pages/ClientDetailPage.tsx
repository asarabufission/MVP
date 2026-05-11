import {
  ArrowLeft,
  Check,
  Database,
  Pencil,
  X,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { RoleGuard } from "@/components/RoleGuard";
import { AddClientModal } from "@/components/modals/AddClientModal";
import { SetIdentifierModal } from "@/components/modals/SetIdentifierModal";
import { Badge, type BadgeTone, statusToTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Table, type Column } from "@/components/ui/Table";
import { useClientDetail } from "@/hooks/useClients";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import type {
  ClientAssignment,
  ClientDetail,
  DatasourceCategory,
  Readiness,
} from "@/types/api";

function readinessTone(r: Readiness): BadgeTone {
  switch (r) {
    case "READY":
      return "green";
    case "DEGRADED":
      return "red";
    case "NEEDS_SETUP":
    default:
      return "amber";
  }
}

function categoryTone(c: DatasourceCategory): BadgeTone {
  switch (c) {
    case "LICENSING":
      return "purple";
    case "ENDPOINT":
      return "green";
    case "RECONCILIATION":
      return "amber";
    default:
      return "gray";
  }
}

interface ChecklistItem {
  label: string;
  ok: boolean;
}

function buildChecklist(detail: ClientDetail): ChecklistItem[] {
  const active = detail.assignments.filter((a) => a.status === "ACTIVE");
  return [
    {
      label: "Has Licensing datasource",
      ok: active.some((a) => a.category === "LICENSING"),
    },
    {
      label: "Has Endpoint datasource",
      ok: active.some((a) => a.category === "ENDPOINT"),
    },
    {
      label: "Identity anchor set",
      ok: active.some((a) => a.isIdentityAnchor),
    },
    {
      label: "Billing source set",
      ok: active.some((a) => a.isBillingSource),
    },
    {
      label: "No degraded assignments",
      ok: active.every((a) => a.datasourceStatus !== "DEGRADED"),
    },
  ];
}

function DetailField({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: React.ReactNode;
  icon?: LucideIcon;
}) {
  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted">
        {label}
      </p>
      <p className="mt-1 flex items-center gap-2 text-sm text-text">
        {Icon && <Icon className="h-4 w-4 text-muted" aria-hidden />}
        {value ?? "—"}
      </p>
    </div>
  );
}

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useClientDetail(id);

  const [editOpen, setEditOpen] = useState(false);
  const [identifierTarget, setIdentifierTarget] =
    useState<ClientAssignment | null>(null);

  const back = (
    <Button
      variant="ghost"
      leftIcon={<ArrowLeft className="h-4 w-4" />}
      onClick={() => navigate("/clients")}
    >
      Back to Clients
    </Button>
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        {back}
        <Card>
          <p className="text-sm text-muted">Loading client…</p>
        </Card>
      </div>
    );
  }

  if (isError || !data) {
    const status =
      typeof error === "object" && error && "response" in error
        ? // @ts-expect-error axios error shape
          (error.response?.status as number | undefined)
        : undefined;
    return (
      <div className="space-y-4">
        {back}
        <Card>
          <p className="text-sm text-red">
            {status === 404 ? "Client not found." : "Failed to load client."}
          </p>
        </Card>
      </div>
    );
  }

  const checklist = buildChecklist(data);
  const metCount = checklist.filter((c) => c.ok).length;

  const assignmentColumns: Column<ClientAssignment>[] = [
    {
      key: "datasourceName",
      header: "Vendor",
      render: (r) => <span className="font-medium text-text">{r.datasourceName}</span>,
    },
    {
      key: "category",
      header: "Category",
      render: (r) => (
        <Badge tone={categoryTone(r.category)}>{r.category}</Badge>
      ),
    },
    { key: "scope", header: "Scope" },
    {
      key: "effectiveIdentifierType",
      header: "Effective Identifier Type",
      render: (r) => (
        <span className={cn(r.identifierType ? "text-text" : "text-muted")}>
          {r.effectiveIdentifierType}
        </span>
      ),
    },
    {
      key: "effectiveIdentifierValue",
      header: "Effective Identifier Value",
      render: (r) => (
        <span className={cn(r.identifierType ? "text-text" : "text-muted")}>
          {r.effectiveIdentifierValue}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (r) => {
        const label =
          r.status === "INACTIVE" ? "INACTIVE" : r.datasourceStatus;
        return <Badge tone={statusToTone(label)}>{label}</Badge>;
      },
    },
    {
      key: "assignedAt",
      header: "Assigned",
      render: (r) => (
        <span className="text-muted">{formatDateTime(r.assignedAt)}</span>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <RoleGuard role="MSP_ADMIN">
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<Pencil className="h-3.5 w-3.5" />}
            onClick={() => setIdentifierTarget(r)}
            disabled={r.status === "INACTIVE"}
          >
            Edit Identifier
          </Button>
        </RoleGuard>
      ),
      className: "text-right",
      headerClassName: "text-right",
    },
  ];

  return (
    <div className="space-y-6">
      {back}

      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">
              {data.name}
            </h1>
            <Badge tone={readinessTone(data.readiness)}>{data.readiness}</Badge>
          </div>
          <p className="mt-1 text-sm text-muted">
            {data.assignedCount} active assignment
            {data.assignedCount === 1 ? "" : "s"}
          </p>
        </div>
        <RoleGuard role="MSP_ADMIN">
          <Button
            variant="secondary"
            leftIcon={<Pencil className="h-4 w-4" />}
            onClick={() => setEditOpen(true)}
          >
            Edit
          </Button>
        </RoleGuard>
      </div>

      <Card title="Details">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <DetailField label="Description" value={data.description ?? "—"} />
          <DetailField
            label="Default Identifier Type"
            value={
              <span className="font-mono text-text">
                {data.defaultIdentifierType}
              </span>
            }
          />
          <DetailField
            label="Default Identifier Value"
            value={
              <span className="font-mono text-text">
                {data.defaultIdentifierValue}
              </span>
            }
          />
          <DetailField
            label="Billing Source"
            value={data.billingSourceName ?? "—"}
          />
          <DetailField
            label="Identity Anchor"
            value={data.identityAnchorName ?? "—"}
          />
          <DetailField label="Created" value={formatDateTime(data.createdAt)} />
          <DetailField label="Updated" value={formatDateTime(data.updatedAt)} />
        </div>
      </Card>

      <Card
        title="Readiness"
        description={`${metCount} / ${checklist.length} conditions met`}
      >
        <ul className="space-y-2">
          {checklist.map((c) => (
            <li
              key={c.label}
              className="flex items-center gap-3 text-sm text-text"
            >
              {c.ok ? (
                <Check className="h-4 w-4 flex-none text-green" aria-hidden />
              ) : (
                <X className="h-4 w-4 flex-none text-muted" aria-hidden />
              )}
              <span className={cn(c.ok ? "text-text" : "text-muted")}>
                {c.label}
              </span>
            </li>
          ))}
        </ul>
        {metCount === checklist.length && data.readiness !== "READY" && (
          <p className="mt-3 text-xs text-muted">
            All conditions met. Backend recompute lands in Phase 6 — refresh
            after assignment changes to update the badge.
          </p>
        )}
      </Card>

      <Card title="Datasources" padded={false}>
        <Table<ClientAssignment>
          columns={assignmentColumns}
          rows={data.assignments}
          keyFn={(r) => r.id}
          emptyState={
            <EmptyState
              icon={Database}
              title="No datasources assigned"
              description="Use Client Source Mapping to assign datasources."
            />
          }
        />
      </Card>

      <AddClientModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        initial={data}
      />
      <SetIdentifierModal
        open={identifierTarget !== null}
        onClose={() => setIdentifierTarget(null)}
        clientId={data.id}
        clientDefault={{
          type: data.defaultIdentifierType,
          value: data.defaultIdentifierValue,
        }}
        assignment={identifierTarget}
      />
    </div>
  );
}
