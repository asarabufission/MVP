import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { DatasourceListResponse } from "@/types/api";

interface ListOptions {
  status?: string;
}

export function useDatasourceList(opts: ListOptions = {}) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery<DatasourceListResponse>({
    queryKey: ["datasources", "list", opts],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (opts.status) params.status = opts.status;
      const { data } = await api.get<DatasourceListResponse>("/datasources", {
        params,
      });
      return data;
    },
    enabled: isAuthenticated,
  });
}
