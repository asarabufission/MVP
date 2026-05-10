import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useUiStore } from "@/stores/ui-store";

export function LogoutConfirmModal() {
  const open = useUiStore((s) => s.logoutConfirmOpen);
  const setOpen = useUiStore((s) => s.setLogoutConfirmOpen);
  const clear = useAuthStore((s) => s.clear);
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);

  if (!open) return null;

  const handleConfirm = async () => {
    setBusy(true);
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore
    }
    clear();
    setOpen(false);
    navigate("/login", { replace: true });
    setBusy(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-sm rounded-xl border border-border bg-surface p-6 font-sans text-text shadow-xl">
        <h2 className="text-lg font-semibold">Log out?</h2>
        <p className="mt-2 text-sm text-muted">
          Are you sure you want to log out of MSP Guardian?
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={() => setOpen(false)}
            disabled={busy}
            className="rounded-md border border-border px-4 py-2 text-sm text-muted hover:text-text disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={busy}
            className="rounded-md bg-red px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
