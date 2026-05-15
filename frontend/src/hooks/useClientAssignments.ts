import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { AssignmentCreateBody, ClientAssignment } from "@/types/api";

function useInvalidate(clientId: string) {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ["clients", "detail", clientId] });
    qc.invalidateQueries({ queryKey: ["clients", "list"] });
  };
}

export function useAssignDatasource(clientId: string) {
  const invalidate = useInvalidate(clientId);
  return useMutation({
    mutationFn: async (body: AssignmentCreateBody) => {
      const { data } = await api.post<ClientAssignment>(
        `/clients/${clientId}/assignments`,
        body,
      );
      return data;
    },
    onSuccess: () => invalidate(),
  });
}

export function useInactivateAssignment(clientId: string) {
  const invalidate = useInvalidate(clientId);
  return useMutation({
    mutationFn: async (datasourceId: string) => {
      const { data } = await api.post<ClientAssignment>(
        `/clients/${clientId}/assignments/${datasourceId}/inactivate`,
      );
      return data;
    },
    onSuccess: () => invalidate(),
  });
}

export function useReactivateAssignment(clientId: string) {
  const invalidate = useInvalidate(clientId);
  return useMutation({
    mutationFn: async (datasourceId: string) => {
      const { data } = await api.post<ClientAssignment>(
        `/clients/${clientId}/assignments/${datasourceId}/reactivate`,
      );
      return data;
    },
    onSuccess: () => invalidate(),
  });
}

export function useSetBillingSource(clientId: string) {
  const invalidate = useInvalidate(clientId);
  return useMutation({
    mutationFn: async (datasourceId: string) => {
      const { data } = await api.post<ClientAssignment>(
        `/clients/${clientId}/assignments/${datasourceId}/set-billing-source`,
      );
      return data;
    },
    onSuccess: () => invalidate(),
  });
}

export function useSetIdentityAnchor(clientId: string) {
  const invalidate = useInvalidate(clientId);
  return useMutation({
    mutationFn: async (datasourceId: string) => {
      const { data } = await api.post<ClientAssignment>(
        `/clients/${clientId}/assignments/${datasourceId}/set-identity-anchor`,
      );
      return data;
    },
    onSuccess: () => invalidate(),
  });
}
