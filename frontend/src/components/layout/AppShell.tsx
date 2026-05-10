import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/Sidebar";
import { useIdleTimer } from "@/hooks/useIdleTimer";
import { useUiStore } from "@/stores/ui-store";

export function AppShell() {
  const setIdleOpen = useUiStore((s) => s.setIdleModalOpen);
  useIdleTimer({ onTimeout: () => setIdleOpen(true) });

  return (
    <div className="flex min-h-screen bg-bg font-sans text-text">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
