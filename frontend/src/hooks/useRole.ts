import { useAuthStore } from "@/stores/auth-store";
import type { Role } from "@/types/api";

export function useRole(): Role | null {
  return useAuthStore((s) => s.user?.role ?? null);
}
