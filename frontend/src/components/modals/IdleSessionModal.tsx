import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";
import type { LoginResponse } from "@/types/api";

const AUTO_LOGOUT_SECONDS = 60;

export function IdleSessionModal() {
  const open = useUiStore((s) => s.idleModalOpen);
  const setOpen = useUiStore((s) => s.setIdleModalOpen);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const setAuth = useAuthStore((s) => s.setAuth);
  const clear = useAuthStore((s) => s.clear);
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(AUTO_LOGOUT_SECONDS);

  const autoLogoutRef = useRef<() => Promise<void> | void>(() => {});

  // Always keep the latest auto-logout callback referenced so the
  // countdown effect doesn't need to re-subscribe to changing closures.
  autoLogoutRef.current = async () => {
    setBusy(true);
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore — we're forcing a logout anyway
    }
    clear();
    setOpen(false);
    navigate("/login", { replace: true });
    setBusy(false);
  };

  // Countdown + auto-logout: starts when the modal opens, resets when it closes.
  useEffect(() => {
    if (!open) {
      setSecondsLeft(AUTO_LOGOUT_SECONDS);
      return;
    }

    setSecondsLeft(AUTO_LOGOUT_SECONDS);
    const interval = window.setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          window.clearInterval(interval);
          void autoLogoutRef.current();
          return 0;
        }
        return s - 1;
      });
    }, 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, [open]);

  if (!open) return null;

  const handleContinue = async () => {
    if (!refreshToken) {
      clear();
      navigate("/login", { replace: true });
      setOpen(false);
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post<LoginResponse>("/auth/refresh", {
        refreshToken,
      });
      setAuth({
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        user: data.user,
        mspId: data.mspId,
      });
      setOpen(false);
    } catch {
      clear();
      navigate("/login", { replace: true });
      setOpen(false);
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = () => autoLogoutRef.current();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-sm rounded-xl border border-border bg-surface p-6 font-sans text-text shadow-xl">
        <h2 className="text-lg font-semibold">Your session is about to expire</h2>
        <p className="mt-2 text-sm text-muted">
          You've been idle for a while. Continue your session, or log out.
        </p>
        <p
          className="mt-3 text-xs font-medium text-amber"
          role="status"
          aria-live="polite"
        >
          Auto logout in {secondsLeft}s
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={handleLogout}
            disabled={busy}
            className="rounded-md border border-border px-4 py-2 text-sm text-muted hover:text-text disabled:opacity-50"
          >
            Logout
          </button>
          <button
            type="button"
            onClick={handleContinue}
            disabled={busy}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
