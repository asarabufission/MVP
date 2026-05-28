import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { JobRunListItem } from "@/types/api";

export type JobRunStatusFilter =
  | "ALL"
  | "SUCCESS"
  | "FAILED"
  | "RUNNING"
  | "PARTIAL";

export function useJobRuns(status: JobRunStatusFilter = "ALL", limit = 50) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery<JobRunListItem[]>({
    queryKey: ["job-runs", status, limit],
    queryFn: async () => {
      const params: Record<string, string | number> = { limit };
      if (status !== "ALL") params.status = status;
      const { data } = await api.get<JobRunListItem[]>("/job-runs", { params });
      return data;
    },
    enabled: isAuthenticated,
  });
}
