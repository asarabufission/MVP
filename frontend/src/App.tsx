import { QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppShell } from "@/components/layout/AppShell";
import { IdleSessionModal } from "@/components/modals/IdleSessionModal";
import { LogoutConfirmModal } from "@/components/modals/LogoutConfirmModal";
import { queryClient } from "@/lib/queryClient";
import { ClientDetailPage } from "@/pages/ClientDetailPage";
import { ClientsPage } from "@/pages/ClientsPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { JobRunsPage } from "@/pages/JobRunsPage";
import { LoginPage } from "@/pages/LoginPage";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="text-sm text-muted">
        This page lands in a later phase. Use the sidebar to navigate.
      </p>
    </div>
  );
}

function ForbiddenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg font-sans text-text">
      <div className="text-center">
        <h1 className="text-3xl font-semibold">403 — Forbidden</h1>
        <p className="mt-2 text-sm text-muted">
          Your role does not permit access to this page.
        </p>
      </div>
    </div>
  );
}

function Toaster() {
  const toast = useUiStore((s) => s.toast);
  const clearToast = useUiStore((s) => s.clearToast);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(clearToast, 4000);
    return () => window.clearTimeout(timer);
  }, [toast, clearToast]);

  if (!toast) return null;

  const tone =
    toast.type === "success"
      ? "border-green/40 bg-green/10 text-green"
      : toast.type === "error"
        ? "border-red/40 bg-red/10 text-red"
        : "border-border bg-surface text-text";

  return (
    <div className="pointer-events-none fixed bottom-6 right-6 z-50">
      <div
        role="status"
        className={`pointer-events-auto rounded-md border px-4 py-2 text-sm shadow-lg ${tone}`}
      >
        {toast.message}
      </div>
    </div>
  );
}

function RootRedirect() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function ProtectedShell() {
  return (
    <ProtectedRoute>
      <AppShell />
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ScrollToTop />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forbidden" element={<ForbiddenPage />} />
          <Route element={<ProtectedShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/clients/:id" element={<ClientDetailPage />} />
            <Route
              path="/datasources"
              element={<PlaceholderPage title="Datasources" />}
            />
            <Route
              path="/datasources/add"
              element={<PlaceholderPage title="Add Datasource" />}
            />
            <Route
              path="/reports"
              element={<PlaceholderPage title="Reports" />}
            />
            <Route
              path="/reports/history"
              element={<PlaceholderPage title="Reports History" />}
            />
            <Route path="/job-runs" element={<JobRunsPage />} />
            <Route
              path="/settings"
              element={<PlaceholderPage title="Settings" />}
            />
          </Route>
          <Route path="/" element={<RootRedirect />} />
          <Route path="*" element={<RootRedirect />} />
        </Routes>
        <IdleSessionModal />
        <LogoutConfirmModal />
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
