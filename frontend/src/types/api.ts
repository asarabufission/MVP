export type Role = "MSP_ADMIN" | "MSP_ANALYST";

export interface User {
  id: string;
  mspId: string;
  username: string;
  email: string;
  fullName: string | null;
  role: Role;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  user: User;
  mspId: string;
}

export interface ApiError {
  detail: unknown;
  code: string;
}

export interface FailedRunItem {
  id: string;
  datasourceName: string | null;
  error: string | null;
  startedAt: string;
}

export interface RecentActivityItem {
  id: string;
  status: string;
  datasourceName: string | null;
  clientName: string | null;
  type: string;
  startedAt: string;
  endedAt: string | null;
  records: number | null;
}

export interface DashboardSummary {
  clientsReady: number;
  totalClients: number;
  activeDatasources: number;
  totalDatasources: number;
  recentRunsCount: number;
  reportsGenerated: number;
  failedRuns: FailedRunItem[];
  recentActivity: RecentActivityItem[];
}
