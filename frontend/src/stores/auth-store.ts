import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { User } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  mspId: string | null;
  isAuthenticated: boolean;
  setAuth: (args: {
    accessToken: string;
    refreshToken: string;
    user: User;
    mspId: string;
  }) => void;
  updateAccessToken: (accessToken: string) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      mspId: null,
      isAuthenticated: false,
      setAuth: ({ accessToken, refreshToken, user, mspId }) =>
        set({ accessToken, refreshToken, user, mspId, isAuthenticated: true }),
      updateAccessToken: (accessToken) => set({ accessToken }),
      clear: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          mspId: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "msp-guardian-auth",
      partialize: (state) => ({
        refreshToken: state.refreshToken,
        user: state.user,
        mspId: state.mspId,
      }),
      onRehydrateStorage: () => (state) => {
        if (state && state.refreshToken && state.user) {
          state.isAuthenticated = true;
        }
      },
    },
  ),
);
