import { AxiosError } from "axios";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { RoleGuard } from "@/components/RoleGuard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useClientList, useCreateClient } from "@/hooks/useClients";
import { useUiStore } from "@/stores/ui-store";
import type { ApiError, ClientListItem } from "@/types/api";

type StatusFilter = "all" | "ready" | "notready";
type SortKey = "az" | "za" | "src";

const PAGE_SIZE = 10;

function readinessTone(ready: boolean): BadgeTone {
  return ready ? "green" : "amber";
}

function useDebounced<T>(value: T, delay = 250): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

function deriveDefaultIdentifierValue(name: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "")
    .slice(0, 60);
  return slug ? `${slug}.com` : "tbd.local";
}

export function ClientsPage() {
  const navigate = useNavigate();
  const pushToast = useUiStore((s) => s.pushToast);

  const [addOpen, setAddOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebounced(searchInput, 250);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [sortKey, setSortKey] = useState<SortKey>("az");
  const [page, setPage] = useState(0);

  useEffect(() => {
    setPage(0);
  }, [debouncedSearch, statusFilter, sortKey]);

  const { data, isLoading, isError } = useClientList({
    search: debouncedSearch || undefined,
    limit: 200,
  });
  const create = useCreateClient();

  const rows: ClientListItem[] = data?.items ?? [];

  const filtered = useMemo(() => {
    return rows.filter((c) => {
      if (statusFilter === "ready") return c.readiness === "READY";
      if (statusFilter === "notready") return c.readiness !== "READY";
      return true;
    });
  }, [rows, statusFilter]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    if (sortKey === "az") arr.sort((a, b) => a.name.localeCompare(b.name));
    else if (sortKey === "za") arr.sort((a, b) => b.name.localeCompare(a.name));
    else if (sortKey === "src")
      arr.sort((a, b) => b.assignedCount - a.assignedCount);
    return arr;
  }, [filtered, sortKey]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const pageRows = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const from = sorted.length === 0 ? 0 : page * PAGE_SIZE + 1;
  const to = Math.min((page + 1) * PAGE_SIZE, sorted.length);

  const resetForm = () => {
    setNewName("");
    setNewDescription("");
    setNameError(null);
    setServerError(null);
  };

  const onCreate = async () => {
    const trimmed = newName.trim();
    if (!trimmed) return;
    setNameError(null);
    setServerError(null);
    try {
      await create.mutateAsync({
        name: trimmed,
        description: newDescription.trim() ? newDescription.trim() : null,
        defaultIdentifierType: "EMAIL_DOMAIN_CONTAINS",
        defaultIdentifierValue: deriveDefaultIdentifierValue(trimmed),
      });
      pushToast({ type: "success", message: "Client created successfully" });
      resetForm();
      setAddOpen(false);
    } catch (err) {
      const ax = err as AxiosError<ApiError>;
      if (ax.response?.data?.code === "CLIENT_NAME_TAKEN") {
        setNameError("Client name already exists");
      } else {
        setServerError("Something went wrong. Please try again.");
      }
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Clients</h1>
        <RoleGuard role="MSP_ADMIN">
          <Button
            onClick={() => {
              if (addOpen) {
                resetForm();
              }
              setAddOpen((v) => !v);
            }}
          >
            + Add Client
          </Button>
        </RoleGuard>
      </div>

      {addOpen && (
        <Card className="max-w-md">
          <h3 className="mb-3 text-sm font-semibold">New Client</h3>
          <div className="space-y-3">
            <Input
              label="Client Name *"
              autoFocus
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value);
                if (nameError) setNameError(null);
              }}
              placeholder="e.g. Acme Corp"
              error={nameError ?? undefined}
            />
            <Input
              label="Description"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              placeholder="Industry / notes"
            />
            {serverError && (
              <div
                role="alert"
                className="rounded-md border border-red/40 bg-red/10 px-3 py-2 text-xs text-red"
              >
                {serverError}
              </div>
            )}
            <div className="flex gap-2 pt-1">
              <Button
                onClick={onCreate}
                disabled={!newName.trim()}
                loading={create.isPending}
              >
                Create Client
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setAddOpen(false);
                  resetForm();
                }}
                disabled={create.isPending}
              >
                Cancel
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="🔍 Search clients..."
          className="w-64 rounded-md border border-border bg-surface2 px-3 py-2 text-sm text-text placeholder-dim focus:border-accent focus:outline-none"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          className="rounded-md border border-border bg-surface2 px-3 py-2 text-sm text-text focus:border-accent focus:outline-none"
        >
          <option value="all">All Statuses</option>
          <option value="ready">Ready</option>
          <option value="notready">Not Ready</option>
        </select>
        <select
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="rounded-md border border-border bg-surface2 px-3 py-2 text-sm text-text focus:border-accent focus:outline-none"
        >
          <option value="az">Name (A-Z)</option>
          <option value="za">Name (Z-A)</option>
          <option value="src">Most Sources</option>
        </select>
      </div>

      <Card padded={false}>
        {isLoading && rows.length === 0 ? (
          <div className="p-8 text-sm text-muted">Loading clients…</div>
        ) : isError ? (
          <div className="p-8 text-sm text-red">Failed to load clients.</div>
        ) : pageRows.length === 0 ? (
          <div className="p-8 text-sm text-muted">
            {debouncedSearch || statusFilter !== "all"
              ? "No clients match the current filters."
              : "No clients yet. Click + Add Client to create one."}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-surface2 text-left text-[11px] font-medium uppercase tracking-wide text-muted">
                  <th className="px-4 py-2.5">Client</th>
                  <th className="px-4 py-2.5">Sources</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="w-10 px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((cl) => {
                  const ready = cl.readiness === "READY";
                  return (
                    <tr
                      key={cl.id}
                      onClick={() => navigate(`/clients/${cl.id}`)}
                      className="cursor-pointer border-t border-border/60 hover:bg-surface2/60"
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium text-text">{cl.name}</div>
                        {cl.description && (
                          <div className="text-[10px] text-dim">
                            {cl.description}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-text">
                        {cl.assignedCount} source
                        {cl.assignedCount === 1 ? "" : "s"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={readinessTone(ready)}>
                          {ready ? "Ready" : "Not Ready"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-dim">→</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {sorted.length > 0 && totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-2.5 text-xs text-muted">
            <span>
              Showing {from}–{to} of {sorted.length}
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
              <span>
                {page + 1} / {totalPages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages - 1}
                onClick={() =>
                  setPage((p) => Math.min(totalPages - 1, p + 1))
                }
              >
                Next »
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
