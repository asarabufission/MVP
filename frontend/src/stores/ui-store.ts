import { create } from "zustand";

export type ToastKind = "success" | "error" | "info";

export interface Toast {
  message: string;
  type: ToastKind;
}

interface UiState {
  idleModalOpen: boolean;
  logoutConfirmOpen: boolean;
  sidebarCollapsed: boolean;
  toast: Toast | null;
  setIdleModalOpen: (open: boolean) => void;
  setLogoutConfirmOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  pushToast: (toast: Toast) => void;
  clearToast: () => void;
}

export const useUiStore = create<UiState>((set) => ({
  idleModalOpen: false,
  logoutConfirmOpen: false,
  sidebarCollapsed: false,
  toast: null,
  setIdleModalOpen: (open) => set({ idleModalOpen: open }),
  setLogoutConfirmOpen: (open) => set({ logoutConfirmOpen: open }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  pushToast: (toast) => set({ toast }),
  clearToast: () => set({ toast: null }),
}));
