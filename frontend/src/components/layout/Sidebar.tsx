import {
  Activity,
  Database,
  FileBarChart,
  LayoutDashboard,
  Link2,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Settings as SettingsIcon,
  Users,
  type LucideIcon,
} from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router-dom";

import { RoleGuard } from "@/components/RoleGuard";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/clients", label: "Clients", icon: Users },
  { to: "/datasources", label: "Datasources", icon: Database },
  { to: "/client-source-mapping", label: "Client Source Mapping", icon: Link2 },
  { to: "/reports", label: "Reports", icon: FileBarChart },
  { to: "/job-runs", label: "Job Runs", icon: Activity },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export function Sidebar() {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggle = useUiStore((s) => s.toggleSidebar);
  const setLogoutOpen = useUiStore((s) => s.setLogoutConfirmOpen);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-border bg-surface2 transition-[width] duration-200 ease",
        collapsed ? "w-16" : "w-60",
      )}
    >
      {/* Brand */}
      <div className="flex h-16 items-center justify-between border-b border-border px-3">
        {collapsed ? (
          <Link
            to="/dashboard"
            aria-label="Go to dashboard"
            className="mx-auto rounded font-mono text-sm font-semibold tracking-tight text-text hover:text-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
          >
            MG
          </Link>
        ) : (
          <Link
            to="/dashboard"
            aria-label="Go to dashboard"
            className="rounded text-base font-semibold tracking-tight text-text hover:text-accent focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
          >
            MSP Guardian
          </Link>
        )}
        <button
          type="button"
          onClick={toggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="rounded-md p-1.5 text-muted hover:bg-surface hover:text-text"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Admin CTA */}
      <RoleGuard role="MSP_ADMIN">
        <div className="border-b border-border p-3">
          {collapsed ? (
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/datasources/add")}
              className="w-full p-0"
              title="Add Datasource"
              aria-label="Add Datasource"
            >
              <Plus className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/datasources/add")}
              leftIcon={<Plus className="h-4 w-4" />}
              className="w-full"
            >
              Add Datasource
            </Button>
          )}
        </div>
      </RoleGuard>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md border-l-2 px-3 py-2 text-sm transition-colors",
                    isActive
                      ? "border-accent bg-surface text-text"
                      : "border-transparent text-muted hover:bg-surface/60 hover:text-text",
                    collapsed && "justify-center px-0",
                  )
                }
              >
                <item.icon className="h-4 w-4 flex-none" aria-hidden />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-border p-3">
        {collapsed ? (
          <button
            type="button"
            onClick={() => setLogoutOpen(true)}
            title="Logout"
            aria-label="Logout"
            className="flex w-full items-center justify-center rounded-md p-2 text-muted hover:bg-surface hover:text-red"
          >
            <LogOut className="h-4 w-4" />
          </button>
        ) : (
          <div className="flex items-center justify-between gap-2">
            {user && (
              <div className="min-w-0">
                <p className="truncate text-xs font-medium text-text">
                  {user.fullName ?? user.email}
                </p>
                <p className="truncate text-[11px] text-muted">{user.role}</p>
              </div>
            )}
            <button
              type="button"
              onClick={() => setLogoutOpen(true)}
              aria-label="Logout"
              className="rounded-md p-1.5 text-muted hover:bg-surface hover:text-red"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
