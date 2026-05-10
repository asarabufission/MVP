import type { ReactNode } from "react";

import { useRole } from "@/hooks/useRole";
import type { Role } from "@/types/api";

interface Props {
  role: Role | Role[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function RoleGuard({ role, children, fallback = null }: Props) {
  const current = useRole();
  const allowed = Array.isArray(role) ? role : [role];
  if (current && allowed.includes(current)) {
    return <>{children}</>;
  }
  return <>{fallback}</>;
}
