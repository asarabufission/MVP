import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { LoginResponse, User } from "@/types/api";

export function useAuth() {
  const { accessToken, refreshToken, user, mspId, isAuthenticated, setAuth, clear } =
    useAuthStore();

  async function login(
    username: string,
    password: string,
    rememberMe: boolean = false,
  ): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>("/auth/login", {
      username,
      password,
      rememberMe,
    });
    setAuth(
      {
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        user: data.user,
        mspId: data.mspId,
      },
      rememberMe,
    );
    return data;
  }

  async function logout(): Promise<void> {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore — we're clearing the session regardless
    }
    clear();
  }

  return {
    accessToken,
    refreshToken,
    user,
    mspId,
    isAuthenticated,
    role: user?.role ?? null,
    login,
    logout,
  };
}

export function useMe() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const { data } = await api.get<User>("/auth/me");
      return data;
    },
    enabled: isAuthenticated,
  });
}
