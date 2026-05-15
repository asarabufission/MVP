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

export type Readiness = "READY" | "NEEDS_SETUP" | "DEGRADED";
export type AssignmentStatus = "ACTIVE" | "INACTIVE";
export type DatasourceCategory = "LICENSING" | "ENDPOINT" | "RECONCILIATION";

export interface ClientListItem {
  id: string;
  name: string;
  description: string | null;
  defaultIdentifierType: string;
  defaultIdentifierValue: string;
  readiness: Readiness;
  assignedCount: number;
  billingSourceName: string | null;
  identityAnchorName: string | null;
  createdAt: string;
}

export interface ClientListResponse {
  items: ClientListItem[];
  nextCursor: string | null;
  totalCount: number;
}

export interface ClientAssignment {
  id: string;
  datasourceId: string;
  datasourceName: string;
  category: DatasourceCategory;
  sourceType: string;
  scope: string;
  datasourceStatus: string;
  isBillingSource: boolean;
  isIdentityAnchor: boolean;
  identifierType: string | null;
  identifierValue: string | null;
  effectiveIdentifierType: string;
  effectiveIdentifierValue: string;
  status: AssignmentStatus;
  assignedAt: string;
  inactivatedAt: string | null;
}

export interface ClientDetail extends ClientListItem {
  updatedAt: string;
  assignments: ClientAssignment[];
}

export interface ClientCreateBody {
  name: string;
  description?: string | null;
  defaultIdentifierType: string;
  defaultIdentifierValue: string;
}

export type ClientPatchBody = Partial<ClientCreateBody>;

export interface IdentifierOverrideBody {
  identifierType: string;
  identifierValue: string;
}

export interface AssignmentCreateBody {
  datasourceId: string;
  identifierType?: string | null;
  identifierValue?: string | null;
}

export interface DatasourceListItem {
  id: string;
  name: string;
  vendor: string;
  category: DatasourceCategory;
  sourceType: string;
  scope: string;
  status: string;
  lastRunAt: string | null;
  createdAt: string;
  clientId: string | null;
  blueprintId: string | null;
}

export interface DatasourceListResponse {
  items: DatasourceListItem[];
  totalCount: number;
}
