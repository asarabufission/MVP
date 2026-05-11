import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type {
  ClientAssignment,
  ClientCreateBody,
  ClientDetail,
  ClientListResponse,
  ClientPatchBody,
  IdentifierOverrideBody,
} from "@/types/api";

interface ListOptions {
  search?: string;
  limit?: number;
  cursor?: string;
}

export function useClientList(opts: ListOptions = {}) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery<ClientListResponse>({
    queryKey: ["clients", "list", opts],
    queryFn: async () => {
      const params: Record<string, string | number> = {};
      if (opts.search) params.search = opts.search;
      if (opts.limit != null) params.limit = opts.limit;
      if (opts.cursor) params.cursor = opts.cursor;
      const { data } = await api.get<ClientListResponse>("/clients", { params });
      return data;
    },
    enabled: isAuthenticated,
  });
}

export function useClientDetail(id: string | undefined) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery<ClientDetail>({
    queryKey: ["clients", "detail", id],
    queryFn: async () => {
      const { data } = await api.get<ClientDetail>(`/clients/${id}`);
      return data;
    },
    enabled: isAuthenticated && Boolean(id),
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ClientCreateBody) => {
      const { data } = await api.post<ClientDetail>("/clients", body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}

export function useUpdateClient(id: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ClientPatchBody) => {
      const { data } = await api.patch<ClientDetail>(`/clients/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}

export function useDeleteClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/clients/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}

interface SetIdentifierArgs extends IdentifierOverrideBody {
  clientId: string;
  datasourceId: string;
}

export function useSetAssignmentIdentifier() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (args: SetIdentifierArgs) => {
      const { data } = await api.patch<ClientAssignment>(
        `/clients/${args.clientId}/assignments/${args.datasourceId}/identifier`,
        {
          identifierType: args.identifierType,
          identifierValue: args.identifierValue,
        },
      );
      return data;
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["clients", "detail", vars.clientId] });
      qc.invalidateQueries({ queryKey: ["clients", "list"] });
    },
  });
}
