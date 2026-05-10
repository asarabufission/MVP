import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { DashboardSummary } from "@/types/api";

export function useDashboardSummary() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const { data } = await api.get<DashboardSummary>("/dashboard/summary");
      return data;
    },
    enabled: isAuthenticated,
  });
}
