import { Plus, Search, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { RoleGuard } from "@/components/RoleGuard";
import { AddClientModal } from "@/components/modals/AddClientModal";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Table, type Column } from "@/components/ui/Table";
import { useClientList } from "@/hooks/useClients";
import { formatDate } from "@/lib/format";
import type { ClientListItem, Readiness } from "@/types/api";

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

function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export function ClientsPage() {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState("");
  const debouncedSearch = useDebounced(searchInput, 300);
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [accumulated, setAccumulated] = useState<ClientListItem[]>([]);
  const [addOpen, setAddOpen] = useState(false);

  // Reset accumulated rows when search changes.
  useEffect(() => {
    setCursor(undefined);
    setAccumulated([]);
  }, [debouncedSearch]);

  const { data, isLoading, isError } = useClientList({
    search: debouncedSearch || undefined,
    limit: 50,
    cursor,
  });

  useEffect(() => {
    if (!data) return;
    if (cursor) {
      setAccumulated((prev) => {
        const existing = new Set(prev.map((p) => p.id));
        const fresh = data.items.filter((i) => !existing.has(i.id));
        return [...prev, ...fresh];
      });
    } else {
      setAccumulated(data.items);
    }
  }, [data, cursor]);

  const rows = accumulated;

  const columns = useMemo<Column<ClientListItem>[]>(
    () => [
      {
        key: "name",
        header: "Name",
        render: (r) => <span className="font-medium text-text">{r.name}</span>,
      },
      {
        key: "description",
        header: "Description",
        render: (r) => (
          <span className="line-clamp-1 text-muted" title={r.description ?? ""}>
            {r.description ?? "—"}
          </span>
        ),
      },
      {
        key: "readiness",
        header: "Readiness",
        render: (r) => (
          <Badge tone={readinessTone(r.readiness)}>{r.readiness}</Badge>
        ),
      },
      {
        key: "assignedCount",
        header: "Assigned",
        className: "text-right tabular-nums",
        headerClassName: "text-right",
        render: (r) => r.assignedCount,
      },
      {
        key: "billingSourceName",
        header: "Billing Source",
        render: (r) => r.billingSourceName ?? "—",
      },
      {
        key: "identityAnchorName",
        header: "Identity Anchor",
        render: (r) => r.identityAnchorName ?? "—",
      },
      {
        key: "createdAt",
        header: "Created",
        render: (r) => (
          <span className="text-muted">{formatDate(r.createdAt)}</span>
        ),
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Clients</h1>
          <p className="mt-1 text-sm text-muted">
            {data ? `${data.totalCount} total` : "Loading…"}
          </p>
        </div>
        <RoleGuard role="MSP_ADMIN">
          <Button
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setAddOpen(true)}
          >
            Add Client
          </Button>
        </RoleGuard>
      </div>

      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by name…"
          className="w-full rounded-md border border-border bg-surface2 pl-9 pr-3 py-2 text-sm text-text placeholder-dim focus:border-accent focus:outline-none"
        />
      </div>

      <Card padded={false}>
        {isLoading && rows.length === 0 ? (
          <div className="p-8 text-sm text-muted">Loading clients…</div>
        ) : isError ? (
          <div className="p-8 text-sm text-red">Failed to load clients.</div>
        ) : (
          <Table<ClientListItem>
            columns={columns}
            rows={rows}
            keyFn={(r) => r.id}
            onRowClick={(r) => navigate(`/clients/${r.id}`)}
            emptyState={
              <EmptyState
                icon={Users}
                title={debouncedSearch ? "No matches" : "No clients yet"}
                description={
                  debouncedSearch
                    ? `No clients match "${debouncedSearch}".`
                    : "Add a client to get started."
                }
              />
            }
          />
        )}
      </Card>

      {data?.nextCursor && (
        <div className="flex justify-center">
          <Button
            variant="secondary"
            onClick={() => setCursor(data.nextCursor ?? undefined)}
          >
            Load more
          </Button>
        </div>
      )}

      <AddClientModal open={addOpen} onClose={() => setAddOpen(false)} />
    </div>
  );
}
