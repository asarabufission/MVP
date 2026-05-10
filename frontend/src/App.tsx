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
import { IdleSessionModal } from "@/components/modals/IdleSessionModal";
import { LogoutConfirmModal } from "@/components/modals/LogoutConfirmModal";
import { useIdleTimer } from "@/hooks/useIdleTimer";
import { queryClient } from "@/lib/queryClient";
import { LoginPage } from "@/pages/LoginPage";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

function PlaceholderPage({ title }: { title: string }) {
  const user = useAuthStore((s) => s.user);
  const setLogoutOpen = useUiStore((s) => s.setLogoutConfirmOpen);
  return (
    <div className="min-h-screen bg-bg p-8 font-sans text-text">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{title}</h1>
          <button
            type="button"
            onClick={() => setLogoutOpen(true)}
            className="rounded-md border border-border px-3 py-1.5 text-sm text-muted hover:text-text"
          >
            Logout
          </button>
        </div>
        {user && (
          <p className="mt-3 text-sm text-muted">
            Signed in as {user.email} ({user.role})
          </p>
        )}
        <p className="mt-6 text-sm text-dim">
          Phase 2 placeholder. Real dashboard ships in Phase 5.
        </p>
      </div>
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

function AuthedShell({ children }: { children: React.ReactNode }) {
  const setIdleOpen = useUiStore((s) => s.setIdleModalOpen);
  useIdleTimer({ onTimeout: () => setIdleOpen(true) });
  return <>{children}</>;
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

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ScrollToTop />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forbidden" element={<ForbiddenPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <AuthedShell>
                  <PlaceholderPage title="Dashboard" />
                </AuthedShell>
              </ProtectedRoute>
            }
          />
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
