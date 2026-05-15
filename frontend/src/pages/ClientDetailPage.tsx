import {
  ArrowLeft,
  Check,
  ChevronDown,
  ChevronRight,
  Database,
  Pencil,
  Plus,
  Trash2,
  X,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { RoleGuard } from "@/components/RoleGuard";
import { AddClientModal } from "@/components/modals/AddClientModal";
import { AssignDatasourceModal } from "@/components/modals/AssignDatasourceModal";
import { SetIdentifierModal } from "@/components/modals/SetIdentifierModal";
import { Badge, type BadgeTone, statusToTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Table, type Column } from "@/components/ui/Table";
import {
  useInactivateAssignment,
  useReactivateAssignment,
  useSetBillingSource,
  useSetIdentityAnchor,
} from "@/hooks/useClientAssignments";
import { useClientDetail } from "@/hooks/useClients";
import { useRole } from "@/hooks/useRole";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import { useUiStore } from "@/stores/ui-store";
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

type ActionKind = "billing" | "anchor" | "remove";

interface PendingAction {
  assignment: ClientAssignment;
  kind: ActionKind;
}

interface InlineConfirmProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  variant: "danger" | "primary";
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function InlineConfirm({
  open,
  title,
  message,
  confirmLabel,
  variant,
  busy,
  onConfirm,
  onCancel,
}: InlineConfirmProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-sm rounded-xl border border-border bg-surface p-6 font-sans text-text shadow-xl">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="mt-2 text-sm text-muted">{message}</p>
        <div className="mt-6 flex justify-end gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={busy}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant={variant}
            onClick={onConfirm}
            loading={busy}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useClientDetail(id);
  const role = useRole();
  const isAdmin = role === "MSP_ADMIN";
  const pushToast = useUiStore((s) => s.pushToast);

  const [editOpen, setEditOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [showInactive, setShowInactive] = useState(false);
  const [identifierTarget, setIdentifierTarget] =
    useState<ClientAssignment | null>(null);
  const [pending, setPending] = useState<PendingAction | null>(null);

  const setBilling = useSetBillingSource(id ?? "");
  const setAnchor = useSetIdentityAnchor(id ?? "");
  const inactivate = useInactivateAssignment(id ?? "");
  const reactivate = useReactivateAssignment(id ?? "");

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
  const activeAssignments = data.assignments.filter((a) => a.status === "ACTIVE");
  const inactiveAssignments = data.assignments.filter(
    (a) => a.status === "INACTIVE",
  );

  const handleReactivate = async (a: ClientAssignment) => {
    try {
      await reactivate.mutateAsync(a.datasourceId);
      pushToast({ type: "success", message: "Assignment reactivated" });
    } catch {
      pushToast({ type: "error", message: "Failed to reactivate assignment" });
    }
  };

  const confirmConfig = (() => {
    if (!pending) return null;
    const name = pending.assignment.datasourceName;
    if (pending.kind === "billing") {
      return {
        title: "Make Billing Source",
        message: `Set ${name} as the billing source for this client? This will replace any current billing source.`,
        confirmLabel: "Confirm",
        variant: "primary" as const,
        run: async () => {
          await setBilling.mutateAsync(pending.assignment.datasourceId);
          pushToast({ type: "success", message: "Billing source updated" });
        },
      };
    }
    if (pending.kind === "anchor") {
      return {
        title: "Make Identity Anchor",
        message: `Set ${name} as the identity anchor for this client? This will replace any current anchor.`,
        confirmLabel: "Confirm",
        variant: "primary" as const,
        run: async () => {
          await setAnchor.mutateAsync(pending.assignment.datasourceId);
          pushToast({ type: "success", message: "Identity anchor updated" });
        },
      };
    }
    return {
      title: "Remove Assignment",
      message: `Remove ${name} from this client? The assignment will be inactivated and can be reactivated later.`,
      confirmLabel: "Remove",
      variant: "danger" as const,
      run: async () => {
        await inactivate.mutateAsync(pending.assignment.datasourceId);
        pushToast({ type: "success", message: "Assignment removed" });
      },
    };
  })();

  const handleConfirm = async () => {
    if (!confirmConfig) return;
    try {
      await confirmConfig.run();
      setPending(null);
    } catch {
      pushToast({ type: "error", message: "Action failed. Please try again." });
    }
  };

  const activeColumns: Column<ClientAssignment>[] = [
    {
      key: "datasourceName",
      header: "Vendor",
      render: (r) => (
        <div className="flex items-center gap-2">
          <span className="font-medium text-text">{r.datasourceName}</span>
          {r.isBillingSource && (
            <Badge tone="amber">Billing</Badge>
          )}
          {r.isIdentityAnchor && (
            <Badge tone="purple">Anchor</Badge>
          )}
        </div>
      ),
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
      header: "Identifier Type",
      render: (r) => (
        <span className={cn(r.identifierType ? "text-text" : "text-muted")}>
          {r.effectiveIdentifierType}
        </span>
      ),
    },
    {
      key: "effectiveIdentifierValue",
      header: "Identifier Value",
      render: (r) => (
        <span className={cn(r.identifierType ? "text-text" : "text-muted")}>
          {r.effectiveIdentifierValue}
        </span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (r) => (
        <Badge tone={statusToTone(r.datasourceStatus)}>{r.datasourceStatus}</Badge>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <RoleGuard role="MSP_ADMIN">
          <div className="flex justify-end gap-1">
            {!r.isBillingSource && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPending({ assignment: r, kind: "billing" })}
              >
                Make Billing
              </Button>
            )}
            {!r.isIdentityAnchor && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPending({ assignment: r, kind: "anchor" })}
              >
                Make Anchor
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Pencil className="h-3.5 w-3.5" />}
              onClick={() => setIdentifierTarget(r)}
            >
              Identifier
            </Button>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Trash2 className="h-3.5 w-3.5" />}
              onClick={() => setPending({ assignment: r, kind: "remove" })}
            >
              Remove
            </Button>
          </div>
        </RoleGuard>
      ),
      className: "text-right",
      headerClassName: "text-right",
    },
  ];

  const inactiveColumns: Column<ClientAssignment>[] = [
    {
      key: "datasourceName",
      header: "Vendor",
      render: (r) => <span className="text-muted">{r.datasourceName}</span>,
    },
    {
      key: "category",
      header: "Category",
      render: (r) => (
        <Badge tone={categoryTone(r.category)}>{r.category}</Badge>
      ),
    },
    {
      key: "inactivatedAt",
      header: "Inactivated",
      render: (r) => (
        <span className="text-muted">
          {r.inactivatedAt ? formatDateTime(r.inactivatedAt) : "—"}
        </span>
      ),
    },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <RoleGuard role="MSP_ADMIN">
          <div className="flex justify-end">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleReactivate(r)}
            >
              Reactivate
            </Button>
          </div>
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
            {activeAssignments.length} active assignment
            {activeAssignments.length === 1 ? "" : "s"}
            {inactiveAssignments.length > 0 &&
              ` · ${inactiveAssignments.length} inactive`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <RoleGuard role="MSP_ADMIN">
            <Button
              leftIcon={<Plus className="h-4 w-4" />}
              onClick={() => setAssignOpen(true)}
            >
              Assign Datasource
            </Button>
            <Button
              variant="secondary"
              leftIcon={<Pencil className="h-4 w-4" />}
              onClick={() => setEditOpen(true)}
            >
              Edit
            </Button>
          </RoleGuard>
        </div>
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
      </Card>

      <Card title="Active Assignments" padded={false}>
        <Table<ClientAssignment>
          columns={activeColumns}
          rows={activeAssignments}
          keyFn={(r) => r.id}
          emptyState={
            <EmptyState
              icon={Database}
              title="No datasources assigned"
              description={
                isAdmin
                  ? "Click Assign Datasource to add the first one."
                  : "An admin must assign a datasource."
              }
            />
          }
        />
      </Card>

      {inactiveAssignments.length > 0 && (
        <Card padded={false}>
          <button
            type="button"
            onClick={() => setShowInactive((v) => !v)}
            className="flex w-full items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-surface2/40"
          >
            <span className="flex items-center gap-2 font-medium text-text">
              {showInactive ? (
                <ChevronDown className="h-4 w-4 text-muted" aria-hidden />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted" aria-hidden />
              )}
              Inactive Assignments
            </span>
            <span className="text-xs text-muted">
              {inactiveAssignments.length}
            </span>
          </button>
          {showInactive && (
            <Table<ClientAssignment>
              columns={inactiveColumns}
              rows={inactiveAssignments}
              keyFn={(r) => r.id}
            />
          )}
        </Card>
      )}

      <AddClientModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        initial={data}
      />
      <AssignDatasourceModal
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
        clientId={data.id}
        clientDefault={{
          type: data.defaultIdentifierType,
          value: data.defaultIdentifierValue,
        }}
        excludeDatasourceIds={activeAssignments.map((a) => a.datasourceId)}
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
      {confirmConfig && (
        <InlineConfirm
          open={pending !== null}
          title={confirmConfig.title}
          message={confirmConfig.message}
          confirmLabel={confirmConfig.confirmLabel}
          variant={confirmConfig.variant}
          busy={
            setBilling.isPending ||
            setAnchor.isPending ||
            inactivate.isPending
          }
          onConfirm={handleConfirm}
          onCancel={() => setPending(null)}
        />
      )}
    </div>
  );
}
