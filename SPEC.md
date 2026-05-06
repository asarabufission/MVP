# MSP Guardian POC — Code Generation Prompt (v4)

> **How to use:** paste this entire document into any frontier AI coding tool (Claude, ChatGPT, Cursor, Copilot Chat, Cline, etc.). It is self-contained. Do not split it across messages unless your tool's context limit forces a split — in that case break at section boundaries, not mid-section.
>
> **What changed in v4** (from the April 29 LeafTech wireframe walkthrough): per-source client identifiers; 4–5 row sample data preview in Step 3 mapping; soft-delete (inactivation) for datasources and assignments; per-report datasource inclusion/exclusion; new `MSP_ANALYST` viewer role; Client Source Mapping UX — Assign panel promoted higher.

---

## 1. Role

You are a **senior full-stack engineer** specializing in React + Python FastAPI + AWS. You write production-quality POC code: typed, tested, runnable in Docker on day one, with no TODOs in critical paths. You are pragmatic — this is a POC for a client demo, not a production system. You favor working code over perfect code, but you do not cut corners on security primitives (password hashing, secret handling, SQL injection prevention) or on state-management discipline.

---

## 2. Goal

Build a working end-to-end POC of **"MSP Guardian"** — a multi-tenant platform for Managed Service Providers (MSPs) like LeafTech to onboard third-party SaaS APIs as data sources, assign them to clients with **per-source identifiers**, and produce audit reports. The POC must demo the following live to a client:

1. MSP Admin logs in with seeded credentials.
2. MSP Admin lands on a dashboard showing seeded clients, datasources, and recent job runs.
3. MSP Admin **adds a new client** in real time (form → Postgres row → list refresh).
4. MSP Admin adds a new **Endpoint** datasource via a 4-step wizard:
   - **Step 1 — Identify:** name, vendor, category (`Endpoint`), source type (`API`), scope.
   - **Step 2 — Connect:** API URL + credentials → click **Test Connection** → real Lambda call → schema **and 4–5 sample rows** inferred and cached in Redis.
   - **Step 3 — Map Fields:** sample rows preview shown above mapping table; dropdowns populated from cached schema; user maps source columns to standard Endpoint fields.
   - **Step 4 — Schedule:** pick frequency/time (stored only — no actual scheduler).
5. MSP Admin clicks **Activate Datasource** → backend writes mapping to DynamoDB, fetches the full data file from the source API, saves to landing S3, registers a Glue Catalog table.
6. MSP Admin opens **Client Source Mapping**, assigns the newly activated Endpoint datasource to the newly created client, **specifies the client identifier for that source** (since it may differ across vendors), designates billing source / identity anchor where applicable.
7. MSP Admin opens **Reports**, generates an **Endpoint Audit** report for that client, **selects which datasources to include** in the report → backend reads landing JSON, applies the DynamoDB mapping, renders an XLSX, returns presigned URL.
8. **Demonstrate role separation:** log out, log in as `analyst@mvp.com` → sidebar Datasources/Mapping pages have no write buttons; analyst can still generate reports.
9. MSP Admin can log out via a confirmation modal; idle timeout (1 minute, demo-tuned) prompts continue/logout.

**This POC is not for scale, not for multi-region, not for production hardening.** It is for a 15-minute demo that hits every screen.

---

## 3. Scope — What's IN, What's OUT

**IN scope (must fully work end-to-end):**
- Login + JWT auth + login history + protected routes + logout confirmation + idle timeout (1 min)
- **Two roles: `MSP_ADMIN` (write) and `MSP_ANALYST` (read + report-generate only)** with backend role guards and frontend button-hiding
- Dashboard with `/dashboard/summary` API + seeded data
- **Clients module — real-time CRUD** (list, add, view detail). Must match prototype behavior.
- **Client Source Mapping — real-time** (assign/unassign datasources, **per-source identifier capture**, set billing source, set identity anchor). Must match prototype behavior with the v4 layout tweak (Assign panel promoted higher).
- **Datasource Onboarding Wizard for both `Licensing` AND `Endpoint` categories**, end-to-end (Steps 1 → 5). Endpoint category is the demo focus.
- **Step 3 Map Fields shows a 4–5 row tabular preview** of actual sample data above the mapping table.
- **Soft-delete (inactivation) for datasources and client-source assignments** — historical reports keep working.
- **Report Generation — real**, for both `license` and `endpoint` report types. **User picks specific datasources to include per report run.** Must read landing JSON from S3, apply the DynamoDB mapping, output XLSX to S3 (real AWS), return presigned URL.
- LocalStack for AWS service emulation (S3, Secrets Manager, Lambda, DynamoDB, Glue Catalog)
- Docker Compose for full local stack
- Idempotent seed script with realistic data (including 2 users — admin + analyst)
- README with Windows + Docker + VS Code instructions

**OUT of scope (stub or skip):**
- **Reconciliation category** — wizard accepts the category in the dropdown but Steps 3+ show "POC: Reconciliation not implemented yet." Activation returns 501.
- Real scheduled ingestion (no EventBridge, no cron triggers — schedule metadata is stored, never executed).
- Multi-MSP isolation enforcement (single MSP only — `mspId` is taken from the JWT but not heavily validated cross-tenant).
- Cognito (custom JWT instead).
- HTTPS / TLS (HTTP localhost only).
- Job Runs page advanced filtering (basic status filter only).
- Settings page persistence (renders prototype UI, no backend wiring).
- File-upload datasource type (API only).
- Anomaly detection (post-MVP).
- Training manual generation (PRD / README mention only — actual content authored separately).

---

## 4. Hard Constraints

| Item | Value |
|---|---|
| Backend language | **Python 3.14.3** |
| Backend framework | FastAPI 0.115+ (async) |
| ORM | SQLAlchemy 2.x with **asyncpg** driver |
| Migrations | Alembic (async config) |
| Validation | Pydantic v2 (use `model_config`, not nested `Config`) |
| Auth library | `python-jose[cryptography]` for JWT, `passlib[bcrypt]` for hashing |
| Cache | Redis 7 (`redis.asyncio`) |
| Database | PostgreSQL 16 |
| **Database name** | **`MSP_Guardian`** (exact case, with underscore) |
| Frontend build | **Vite 5** + React 18 + **TypeScript** (strict mode) |
| Frontend styling | Tailwind CSS 3 (dark theme, palette in §11) |
| **Server-state library** | **TanStack Query v5** (all server data) |
| **Client-state library** | **Zustand 5** (auth, wizard, UI flags, modals — single store per slice) |
| Frontend forms | React Hook Form + Zod resolver |
| HTTP client | axios (single instance with interceptors) |
| Routing | React Router v6 |
| Reports renderer | `openpyxl` (Python) for XLSX |
| AWS SDK (backend) | `boto3` |
| AWS local emulation | **LocalStack Community** (S3, Secrets Manager, Lambda, DynamoDB, Glue) |
| AWS region | `us-east-1` (LocalStack default) |
| S3 bucket name | `msp-guardian-poc` |
| DynamoDB table | `msp_guardian_mappings` |
| Glue database | `msp_guardian_poc` |
| Container runtime | Docker + Docker Compose v2 |
| Idle timeout | 1 minute (demo-tuned — this is intentional, do not change) |

**Naming conventions:** snake_case for Python and DB; camelCase for frontend-facing API JSON (Pydantic alias generator); PascalCase for React components and TS types; kebab-case for non-component files.

**State-management discipline (non-negotiable):**
- All server data flows through TanStack Query — never call axios directly from a component.
- All client-side global state lives in Zustand stores. No prop drilling, no React Context for app state.
- Component-local state uses `useState` only when it does not need to be shared.
- Junior dev reading any component should answer "where does this data come from?" in <10 seconds.

---

## 5. Project Structure

```
msp-guardian-poc/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/{env.py, versions/0001_initial.py}
│   ├── app/
│   │   ├── main.py
│   │   ├── core/{config.py, security.py, logging.py, exceptions.py, roles.py}
│   │   ├── db/{session.py, base.py}
│   │   ├── models/
│   │   │   ├── msp.py, user.py, login_history.py, client.py
│   │   │   ├── datasource_draft.py, datasource.py, datasource_schedule.py
│   │   │   ├── client_datasource_assignment.py
│   │   │   └── job_run.py, report_run.py
│   │   ├── schemas/{auth, dashboard, client, datasource, mapping, report, common}.py
│   │   ├── api/
│   │   │   ├── deps.py                  # auth dependency, db dep, role guard
│   │   │   └── v1/{auth, dashboard, clients, client_assignments,
│   │   │            datasource_drafts, datasources, job_runs, reports}.py
│   │   ├── services/
│   │   │   ├── auth_service.py, login_history_service.py, dashboard_service.py
│   │   │   ├── client_service.py, client_assignment_service.py
│   │   │   ├── secrets_service.py, redis_service.py, schema_inference.py
│   │   │   ├── lambda_service.py, s3_landing_service.py, glue_catalog_service.py
│   │   │   ├── mapping_service.py, transforms.py, report_service.py
│   │   │   └── aws_clients.py
│   │   └── seed.py
│   ├── lambdas/
│   │   ├── test_datasource_connection/{handler.py, requirements.txt}
│   │   └── report_generator/{handler.py, requirements.txt, deploy.sh, README.md}
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py, test_roles.py
│       ├── test_clients.py, test_assignments.py
│       ├── test_datasource_activation.py
│       ├── test_soft_delete.py
│       └── test_report_generation.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json, tsconfig.json, vite.config.ts, tailwind.config.js, index.html
│   ├── .env.example
│   └── src/
│       ├── main.tsx, App.tsx
│       ├── lib/{api.ts, queryClient.ts}
│       ├── stores/{auth-store.ts, wizard-store.ts, ui-store.ts}
│       ├── hooks/
│       │   ├── useIdleTimer.ts, useAuth.ts, useDashboard.ts
│       │   ├── useClients.ts, useDatasources.ts, useClientAssignments.ts
│       │   ├── useSchemaPreview.ts, useReports.ts
│       │   └── useRole.ts
│       ├── components/
│       │   ├── layout/{Sidebar.tsx, AppShell.tsx}
│       │   ├── modals/
│       │   │   ├── IdleSessionModal.tsx, LogoutConfirmModal.tsx
│       │   │   ├── AddClientModal.tsx, AssignDatasourceModal.tsx
│       │   │   ├── SetIdentifierModal.tsx, InactivateConfirmModal.tsx
│       │   │   └── DatasourcePickerModal.tsx
│       │   ├── ProtectedRoute.tsx, RoleGuard.tsx
│       │   ├── ui/{Button, Input, Select, Card, Table, Badge, EmptyState}.tsx
│       │   └── wizard/
│       │       ├── WizardStepper.tsx, StepIdentify.tsx, StepConnect.tsx
│       │       ├── StepMapFields.tsx, SampleRowsPreview.tsx
│       │       └── StepSchedule.tsx
│       ├── pages/
│       │   ├── LoginPage.tsx, DashboardPage.tsx
│       │   ├── ClientsPage.tsx, ClientDetailPage.tsx
│       │   ├── DatasourcesPage.tsx, AddDatasourcePage.tsx
│       │   ├── ClientSourceMappingPage.tsx
│       │   ├── ReportsPage.tsx, ReportPreviewPage.tsx
│       │   ├── JobRunsPage.tsx, SettingsPage.tsx
│       │   └── ForbiddenPage.tsx
│       └── types/api.ts
└── infra/localstack/init/01-bootstrap.sh
```

---

## 6. PostgreSQL Schema (database `MSP_Guardian`)

UUID v4 ids (`uuid-ossp`). `TIMESTAMPTZ` defaults `now()`. Common columns `created_at`, `updated_at`.

```
msps
  id UUID PK
  name VARCHAR(120) NOT NULL
  email VARCHAR(160) NOT NULL UNIQUE
  created_at, updated_at

users
  id UUID PK
  msp_id UUID FK -> msps.id
  username VARCHAR(120) UNIQUE NOT NULL
  email VARCHAR(120) UNIQUE NOT NULL
  password_hash VARCHAR(255) NOT NULL
  full_name VARCHAR(160)
  role VARCHAR(40) NOT NULL DEFAULT 'MSP_ADMIN'
        CHECK (role IN ('MSP_ADMIN','MSP_ANALYST'))     -- v4: roles enum
  is_active BOOLEAN NOT NULL DEFAULT TRUE
  created_at, updated_at

login_history
  id UUID PK
  user_id FK, msp_id FK
  access_token_hash CHAR(64) NOT NULL                   -- SHA-256 hex
  refresh_token_hash CHAR(64) NOT NULL
  login_time TIMESTAMPTZ NOT NULL
  logout_time TIMESTAMPTZ NULL
  ip_address VARCHAR(64) NULL
  user_agent VARCHAR(500) NULL
  status VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE','LOGGED_OUT','EXPIRED','REVOKED'))
  created_at, updated_at

clients
  id UUID PK
  msp_id UUID FK -> msps.id
  name VARCHAR(160) NOT NULL
  description TEXT
  default_identifier_type VARCHAR(60) NOT NULL          -- v4: renamed; still default
  default_identifier_value VARCHAR(160) NOT NULL
  readiness VARCHAR(20) NOT NULL DEFAULT 'NEEDS_SETUP'
  created_at, updated_at
  UNIQUE(msp_id, name)

datasource_drafts
  id UUID PK
  msp_id UUID FK, created_by UUID FK -> users.id
  name VARCHAR(160) NOT NULL
  vendor VARCHAR(160) NOT NULL
  category VARCHAR(40) NOT NULL CHECK (category IN ('LICENSING','ENDPOINT','RECONCILIATION'))
  source_type VARCHAR(40) NOT NULL CHECK (source_type IN ('API','FILE_UPLOAD'))
  scope VARCHAR(40) NOT NULL CHECK (scope IN ('MSP_LEVEL','CLIENT_SPECIFIC'))
  secret_arn VARCHAR(400) NULL
  last_attempt_id UUID NULL
  status VARCHAR(40) NOT NULL DEFAULT 'DRAFT'
  created_at, updated_at

datasources
  id UUID PK
  msp_id UUID FK
  draft_id UUID FK NULL
  name VARCHAR(160) NOT NULL
  vendor VARCHAR(160) NOT NULL
  category VARCHAR(40) NOT NULL
  source_type VARCHAR(40) NOT NULL
  scope VARCHAR(40) NOT NULL
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','ACTIVATING','DRAFT','DEGRADED','DISABLED','INACTIVE'))
  active_mapping_version INT NOT NULL DEFAULT 1
  secret_arn VARCHAR(400) NOT NULL
  glue_table_name VARCHAR(200) NULL
  landing_path VARCHAR(500) NULL
  last_run_at TIMESTAMPTZ NULL
  inactivated_at TIMESTAMPTZ NULL                       -- v4: soft delete
  inactivated_by UUID FK -> users.id NULL               -- v4
  created_at, updated_at

datasource_schedules
  id UUID PK
  datasource_id UUID FK UNIQUE
  frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('MANUAL','DAILY','WEEKLY','MONTHLY'))
  time_of_day VARCHAR(5) NULL
  timezone VARCHAR(60) NOT NULL DEFAULT 'America/New_York'
  cron_expression VARCHAR(120) NULL
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE
  created_at, updated_at

client_datasource_assignments
  id UUID PK
  msp_id UUID FK
  client_id UUID FK -> clients.id ON DELETE CASCADE
  datasource_id UUID FK -> datasources.id ON DELETE RESTRICT
        -- v4: changed from CASCADE to RESTRICT — never lose history; inactivate instead
  is_billing_source BOOLEAN NOT NULL DEFAULT FALSE
  is_identity_anchor BOOLEAN NOT NULL DEFAULT FALSE
  identifier_type VARCHAR(60) NULL                      -- v4: per-source override
  identifier_value VARCHAR(160) NULL                    -- v4: per-source override
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'          -- v4: ACTIVE | INACTIVE
        CHECK (status IN ('ACTIVE','INACTIVE'))
  inactivated_at TIMESTAMPTZ NULL                       -- v4
  inactivated_by UUID FK -> users.id NULL               -- v4
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now()
  assigned_by UUID FK -> users.id
  UNIQUE(client_id, datasource_id)
  -- Partial unique indexes (one billing source / one identity anchor per client, only among ACTIVE):
  --   CREATE UNIQUE INDEX ux_client_billing_source
  --     ON client_datasource_assignments(client_id) WHERE is_billing_source = TRUE AND status = 'ACTIVE'
  --   CREATE UNIQUE INDEX ux_client_identity_anchor
  --     ON client_datasource_assignments(client_id) WHERE is_identity_anchor = TRUE AND status = 'ACTIVE'

job_runs
  id UUID PK
  msp_id FK, datasource_id FK NULL, client_id FK NULL
  job_type VARCHAR(40) NOT NULL                         -- TEST_CONNECTION, ACTIVATION, SCHEDULED, MANUAL, REPORT_GENERATION
  status VARCHAR(20) NOT NULL                           -- SUCCESS, FAILED, PARTIAL, RUNNING
  started_at TIMESTAMPTZ NOT NULL
  ended_at TIMESTAMPTZ NULL
  records_count INT NULL
  error_message TEXT NULL
  landing_s3_path VARCHAR(500) NULL
  glue_table_name VARCHAR(200) NULL
  created_at

report_runs
  id UUID PK
  msp_id FK, client_id FK
  report_type VARCHAR(40) NOT NULL                      -- 'license' | 'endpoint'
  period VARCHAR(20) NOT NULL                           -- 'YYYY-MM'
  status VARCHAR(20) NOT NULL DEFAULT 'PENDING'         -- PENDING, GENERATING, READY, FAILED
  s3_uri VARCHAR(500) NULL
  rows_count INT NULL
  exceptions_count INT NULL
  included_datasource_ids UUID[] NOT NULL DEFAULT '{}'  -- v4: audit trail of user's selection
  generated_at TIMESTAMPTZ NULL
  generated_by FK -> users.id
  error_message TEXT NULL
  created_at
```

Indexes: `users(email)`, `login_history(user_id, status)`, `datasources(msp_id, status)`, `job_runs(msp_id, started_at DESC)`, `client_datasource_assignments(client_id, status)`, `client_datasource_assignments(datasource_id, status)`.

---

## 7. API Contracts

All endpoints under `/api/v1`. Frontend-facing JSON `camelCase`. Errors `{ "detail": "...", "code": "..." }`.

### Auth (no role guard)
```
POST   /auth/login    {username,password}
       → 200 { accessToken, refreshToken, expiresIn, user, mspId }
       → 401 INVALID_CREDENTIALS
POST   /auth/refresh  {refreshToken}             → 200 | 401
POST   /auth/logout   (Bearer)                   → 204
GET    /auth/me       (Bearer)                   → 200 {id,mspId,username,email,fullName,role}
```

JWT payload includes `role` claim. Access TTL **15 min**, refresh **7 days**.

### Dashboard (any authenticated)
```
GET /dashboard/summary
  → 200 {clientsReady,totalClients,activeDatasources,totalDatasources,
         recentRunsCount,reportsGenerated,
         failedRuns:[{id,datasourceName,error,startedAt}],
         recentActivity:[{id,status,datasourceName,clientName,type,startedAt,records}]}
```

### Clients (read: any; write: MSP_ADMIN only)
```
GET    /clients
       → 200 [{id,name,description,defaultIdentifierType,defaultIdentifierValue,readiness,
              assignedCount,billingSourceName,identityAnchorName,createdAt}]
POST   /clients   [MSP_ADMIN]
       Body: {name,description,defaultIdentifierType,defaultIdentifierValue}
       → 201 | 409 CLIENT_NAME_TAKEN
GET    /clients/{id}
       → 200 {...client, assignments:[...with identifier override info...]}
PATCH  /clients/{id}   [MSP_ADMIN]
       Body: partial {name?,description?,defaultIdentifierType?,defaultIdentifierValue?}
       → 200
DELETE /clients/{id}   [MSP_ADMIN]                 → 204
```

### Client Source Mapping (read: any; write: MSP_ADMIN only)
```
GET    /clients/{clientId}/assignments
       → 200 [{id,datasourceId,vendor,category,sourceType,scope,state,
              isBillingSource,isIdentityAnchor,
              identifierType,identifierValue,           -- v4: per-source identifier
              effectiveIdentifierType,                  -- v4: computed (override OR default)
              effectiveIdentifierValue,
              status,                                    -- v4: ACTIVE | INACTIVE
              assignedAt,inactivatedAt}]

POST   /clients/{clientId}/assignments   [MSP_ADMIN]
       Body: {datasourceId, identifierType?, identifierValue?}
            -- if identifierType/identifierValue omitted, falls back to client's default
       → 201 | 409 ALREADY_ASSIGNED

PATCH  /clients/{clientId}/assignments/{datasourceId}/identifier   [MSP_ADMIN]   -- v4
       Body: {identifierType,identifierValue}            -- pass empty strings to clear (use defaults)
       → 200

PATCH  /clients/{clientId}/assignments/{datasourceId}/inactivate   [MSP_ADMIN]   -- v4
       → 204 (sets status='INACTIVE', inactivated_at=now())
       NOTE: replaces hard delete; assignment stays for historical reports.

PATCH  /clients/{clientId}/assignments/{datasourceId}/reactivate   [MSP_ADMIN]   -- v4
       → 204

PATCH  /clients/{clientId}/billing-source   [MSP_ADMIN]
       Body: {datasourceId|null}
       → 200 | 400 INVALID_BILLING_SOURCE | 400 ASSIGNMENT_INACTIVE

PATCH  /clients/{clientId}/identity-anchor   [MSP_ADMIN]
       Body: {datasourceId|null}
       → 200 | 400 INVALID_IDENTITY_ANCHOR | 400 ASSIGNMENT_INACTIVE
```

After every assignment change, recompute `clients.readiness` against ACTIVE assignments only.

### Datasources (read: any; activate/inactivate: MSP_ADMIN)
```
GET    /datasources?status=ACTIVE,DEGRADED,INACTIVE...   → list (default excludes INACTIVE)
GET    /datasources/{id}                                  → detail
PATCH  /datasources/{id}/inactivate   [MSP_ADMIN]   -- v4
       → 204 (status='INACTIVE', inactivated_at=now())
       Side effect: all ACTIVE assignments referencing this datasource are also inactivated.
PATCH  /datasources/{id}/reactivate   [MSP_ADMIN]   -- v4
       → 204
```

### Datasource Onboarding Wizard [MSP_ADMIN]
```
POST   /datasource-drafts
       Body: {name,vendor,category,sourceType,scope}
       → 201 {draftId,status:'DRAFT'}

POST   /datasource-drafts/{draftId}/test-connection
       Body: {apiUrl,grantType,apiKey?,apiSecretKey?,accessToken?,bearerToken?,
              clientId?,userId?,tokenUrl?,
              customParameters:[{key,value,location,isSecret}], attemptId}
       → 200 {testRunId,schemaHash,fields:[{name,type,nullable,sampleValues}],
              sampleRows:[{...}, ...max 5 records],          -- v4: tabular preview
              sampleS3Path,cached}

GET    /datasource-drafts/{draftId}/schema-preview
       → 200 {fields,schemaHash,sampleRows,expiresAt}        -- v4: includes sampleRows
       → 410 PREVIEW_EXPIRED

POST   /datasources/activate
       Body: {draftId,
              mapping:{standardSchema,schemaHash,fieldMappings:[...]},
              schedule:{frequency,timeOfDay,timezone,isEnabled}}
       → 202 {datasourceId, status:'ACTIVATING'}
       (poll GET /datasources/{id} every 2 s until status='ACTIVE'|'DEGRADED')
```

### Job Runs (any authenticated)
```
GET /job-runs?limit=50&status=ALL|SUCCESS|FAILED|PARTIAL
    → 200 [{id,status,datasourceName,clientName,jobType,startedAt,endedAt,records,errorMessage}]
```

### Reports (read + generate: any authenticated, including MSP_ANALYST)
```
POST /reports/generate
     Body: {clientId, reportType:'license'|'endpoint', period,
            datasourceIds?:[uuid]}                          -- v4: per-report selection
     -- if datasourceIds omitted/empty → use ALL ACTIVE assignments of matching category
     -- if provided → use only the listed; validate they belong to the client + match category + ACTIVE
     → 202 {reportId, status:'GENERATING'}
     → 400 READINESS_FAILED | 400 INVALID_DATASOURCE_SELECTION

GET  /reports
     → 200 [{id,clientId,clientName,reportType,period,status,generatedAt,rowsCount,
             includedDatasourceIds,includedDatasourceNames}]

GET  /reports/{id}
     → 200 {...report, summaryRows,exceptions,includedSources}

GET  /reports/{id}/download
     → 302 → presigned URL (10-min TTL; backend caches in Redis 4 min)
```

---

## 8. Authentication & Authorization

### JWT + bearer header
Tokens in `Authorization: Bearer <token>`. Access in **Zustand `useAuthStore`** memory only; refresh in `localStorage` via `zustand/middleware/persist`. JWT `role` claim is the single source of truth for authorization.

### Login flow
1. POST `/auth/login` returns `{accessToken,refreshToken,expiresIn,user,mspId}`. `user.role` is `MSP_ADMIN` or `MSP_ANALYST`.
2. Frontend `setAuth({...})` writes both tokens (refresh persisted, access in memory).
3. Server inserts `login_history` row with **SHA-256 hashes only** of both tokens.
4. axios request interceptor adds `Authorization: Bearer <token>`. Response interceptor: on 401 `TOKEN_EXPIRED` → refresh once → retry; on failure → clear store + redirect `/login`.

### Logout flow
Sidebar logout → `LogoutConfirmModal` → POST `/auth/logout` → server marks login_history `LOGGED_OUT` → frontend clears store → `/login`.

### Idle timeout (1 min)
`useIdleTimer` listens for `mousemove,keydown,click,scroll,touchstart` on `window`. On timeout, `useUiStore.idleModalOpen=true`. Continue → `/auth/refresh` → reset; Logout → same as voluntary. Paused while modal open.

### Token refresh
Server hashes refresh token, finds `ACTIVE` row, issues new pair, **updates** existing row's hashes (no insert).

### Role-based authorization (v4)
- Backend: `app/api/deps.py` exposes `require_role('MSP_ADMIN')` FastAPI dependency. Each write endpoint declares it. On violation → 403 `ROLE_FORBIDDEN`.
- Frontend: `<RoleGuard role="MSP_ADMIN">` component conditionally renders children. `useRole()` hook returns current role from auth store. Buttons (Add Client, Add Datasource, Assign, Inactivate, etc.) are wrapped in `<RoleGuard>`. Routes `/datasources/add` and `/client-source-mapping`'s write actions are gated; analyst lands on `/forbidden` if they try to navigate directly.

---

## 9. Datasource Onboarding Wizard

### Step 1 — Identify
Form: `name`, `vendor`, `category` (Licensing | Endpoint | Reconciliation), `sourceType` (API only — File Upload disabled), `scope` (MSP-level | Client-specific). Continue → POST `/datasource-drafts` → store `draftId` in `useWizardStore`.

If `category === 'RECONCILIATION'`: notice "POC: Reconciliation onboarding not implemented." Continue disabled.

### Step 2 — Connect
Fields: `apiUrl`, `grantType` (`client_credentials`|`bearer`|`api_key`); conditional fields per grant type; custom parameters (repeatable: `key`, `value`, `location: header|query|body`, `isSecret`).

**Test Connection:**
1. SPA disables button + spinner; reads `attemptId` from `useWizardStore`.
2. POST `/datasource-drafts/{draftId}/test-connection` with form + `attemptId`.
3. Backend writes credential fields to **Secrets Manager** under `msp-guardian/datasource-draft/{draftId}`; persists `secretArn` + `last_attempt_id` on draft.
4. `idempotencyKey = sha256(draftId + apiUrl + vendor)`. Redis hit returns cached.
5. Lambda `testDatasourceConnection` (LocalStack): reads secret, auths, calls `apiUrl?$top=50`, walks JSON (root path defaults `$.value[*]` or `$.data[*]`), infers schema (`genson`), writes sample to `s3://{S3_BUCKET}/{S3_TMP_PREFIX}/{draftId}/{attemptId}/sample.json`. **Returns `fields`, `sampleRows` (first 5 records), `schemaHash`, `sampleS3Path`.**
6. Backend caches result in Redis under `datasource:test-result:{idempotencyKey}` AND `datasource:schema-preview:{draftId}` (TTL 30 min). Schema-preview cache value includes `sampleRows`.
7. SPA shows green "Connection successful — N rows, M columns".

### Step 3 — Map Fields (v4: with sample preview)
1. SPA GET `/datasource-drafts/{draftId}/schema-preview` → `{fields, schemaHash, sampleRows[]}`.
2. **Render `SampleRowsPreview` component above mapping table** — sticky table showing the 4–5 sample records, with source field names as columns. Horizontal scroll for many columns. Subdued styling (smaller font, muted background) so it's clearly reference data.
3. Below preview: standard fields table for category. Each row: standard field name, required flag, source-column dropdown (from `fields[].name`), transform dropdown.
4. As user picks a source column for a standard field, **highlight that column in the preview table** (border on the column header) so it's obvious which data they're mapping.
5. Required fields must be mapped before Continue is enabled. Inline warning for duplicate source-column on required fields.
6. SPA stores draft mapping in `useWizardStore`.

### Step 4 — Schedule
`frequency` (MANUAL/DAILY/WEEKLY/MONTHLY), `timeOfDay` (HH:MM 24h), `timezone` (default `America/New_York`), `isEnabled`. **No AWS scheduler created.**

### Step 5 — Activate
SPA POST `/datasources/activate`. Returns 202 immediately after the Postgres commit; non-transactional AWS writes happen in a FastAPI `BackgroundTasks` job. SPA polls `GET /datasources/{datasourceId}` every 2 s until `ACTIVE` or `DEGRADED`.

**Phase 1 — Synchronous (Postgres transaction, returns 202):**
1. Validate: schema preview in Redis; `schemaHash` matches; required mappings present; category∈{LICENSING,ENDPOINT} else 501.
2. BEGIN.
3. Insert `datasources` (status=`ACTIVATING`, version=1, `secret_arn`).
4. Insert `datasource_schedules`.
5. Insert `job_runs` (job_type=`ACTIVATION`, status=`RUNNING`, started_at=now()).
6. Mark draft `status='ACTIVATED'`.
7. COMMIT. Return `202 {datasourceId, status:'ACTIVATING'}`.

**Phase 2 — Background:**
1. DynamoDB PutItem mapping document (`pk='DATASOURCE#{datasourceId}'`, `sk='MAPPING#v1'`).
2. Fetch full data file from source API: read secret → re-invoke API (no row limit) → write `data.json` to `s3://{S3_BUCKET}/{S3_LANDING_PREFIX}/msp_id={mspId}/datasource_id={datasourceId}/run_id=activation/data.json`.
3. Ensure Glue DB `msp_guardian_poc` exists.
4. Create Glue Catalog table `{category_lower}_{datasourceId_short}_raw` at landing path. Columns inferred from cached `schemaPreview.fields`. JSON SerDe.
5. Update `datasources` → `status='ACTIVE'`, `landing_path`, `glue_table_name`.
6. Update `job_runs` → `status='SUCCESS'`, `ended_at`, paths.

**On Phase 2 failure:** datasources `status='DEGRADED'`, job_runs `status='FAILED'`, log error. Frontend polling shows error toast.

---

## 10. Standard Schemas, Transforms, Mapping Document

### Licensing standard fields
```json
[
  {"standardField":"user_email","required":true,"dataType":"string"},
  {"standardField":"first_name","required":false,"dataType":"string"},
  {"standardField":"last_name","required":false,"dataType":"string"},
  {"standardField":"license_type","required":true,"dataType":"string_or_array"},
  {"standardField":"is_licensed","required":true,"dataType":"boolean"},
  {"standardField":"department","required":false,"dataType":"string"},
  {"standardField":"record_date","required":true,"dataType":"date"}
]
```

### Endpoint standard fields (demo focus)
```json
[
  {"standardField":"device_hostname","required":true,"dataType":"string"},
  {"standardField":"device_description","required":true,"dataType":"string"},
  {"standardField":"record_date","required":true,"dataType":"date"},
  {"standardField":"client_identifier","required":true,"dataType":"string"},
  {"standardField":"last_seen_at","required":false,"dataType":"timestamp"},
  {"standardField":"serial_number","required":false,"dataType":"string"},
  {"standardField":"device_type","required":false,"dataType":"string"},
  {"standardField":"site_name","required":false,"dataType":"string"}
]
```

### Reconciliation
Placeholder + "POC: not implemented" banner; Continue disabled.

### Transform vocabulary (`app/services/transforms.py`)

| Name | Effect |
|---|---|
| `none` | pass-through |
| `trim` | strip whitespace |
| `lowercase_trim` | lowercase + trim |
| `to_boolean` | yes/true/1/Y → true; no/false/0/N → false; else null |
| `parse_date` | parse common formats → ISO 8601 date |
| `parse_datetime` | parse → ISO 8601 timestamp UTC |
| `split_semicolon` | split string on `;` |
| `split_plus` | split on `+` |

### DynamoDB mapping item (exact)
```json
{
  "pk":"DATASOURCE#<uuid>","sk":"MAPPING#v1",
  "datasourceId":"<uuid>","mspId":"<uuid>",
  "category":"ENDPOINT","standardSchema":"endpoint_device_v1",
  "mappingVersion":1,"status":"ACTIVE","schemaHash":"<sha256 hex>",
  "fields":[
    {"standardField":"device_hostname","sourceField":"hostname","required":true,
     "dataType":"string","transform":"lowercase_trim"}
  ],
  "postProcessing":{"explodeArrays":[],"deduplicateBy":["device_hostname"]},
  "createdAt":"<ISO>","createdBy":"<userId>"
}
```

Licensing → `standardSchema:"license_user_v1"`.

---

## 11. Frontend Specifications

### Tailwind palette
```
bg:#0F1117, surface:#181B23, surface2:#121520, border:#2A2E3B,
text:#E8E9ED, muted:#8B8FA3, dim:#5C6078,
accent:#3B82F6, green:#22C55E, amber:#F59E0B, red:#EF4444,
licensing:#818CF8, endpoint:#34D399, recon:#FB923C
```
Font: `'DM Sans', system-ui, sans-serif`; mono: `'JetBrains Mono'`.

### Routes
```
/login                  (public)
/dashboard              (protected, default)
/clients                (protected — read any)
/clients/:id            (protected — read any)
/datasources            (protected — read any)
/datasources/add        (protected — MSP_ADMIN only; analyst → /forbidden)
/client-source-mapping  (protected — read any; write actions hidden for analyst)
/reports                (protected — read+generate any)
/reports/:id            (protected — read any)
/job-runs               (protected — read any)
/settings               (protected — read-only stub)
/forbidden              (protected — shown when analyst hits an admin-only page)
```

### Zustand stores
```
useAuthStore:
  state: {accessToken,refreshToken,user:{id,email,fullName,role},mspId,isAuthenticated}
  actions: setAuth, clear, updateAccessToken
  middleware: persist (only refreshToken + user; never accessToken)

useWizardStore:
  state: {draftId, attemptId, step,
          identify:{name,vendor,category,sourceType,scope},
          connect:{apiUrl,grantType,secretArn}|null,
          -- Raw credentials (bearerToken, apiKey, apiSecretKey) NEVER stored here. Live only in StepConnect's
          --   local useState; sent to backend on Test Connection. Only secretArn is persisted.
          connectionTested:bool,
          schemaPreview:{fields,schemaHash,sampleRows}|null,    -- v4: includes sampleRows
          mapping:{fieldMappings:[]},
          schedule:{frequency,timeOfDay,timezone,isEnabled}}
  actions: reset, setStep, setIdentify, setConnect, setConnectionTested,
           setSchemaPreview, setMapping, setSchedule
  middleware: persist to sessionStorage

useUiStore:
  state: {idleModalOpen, logoutConfirmOpen, sidebarCollapsed, toast}
  actions: setIdleModalOpen, setLogoutConfirmOpen, toggleSidebar, pushToast, clearToast
  middleware: none
```

### Pages

- **LoginPage** — email + password → 401 inline error → success → `/dashboard`.
- **DashboardPage** — TanStack `/dashboard/summary` once. 4 stat cards, failed-runs alert (if non-empty), 3 quick actions (Generate Report, Add Datasource [admin only], Add Client [admin only]), Recent Activity table.
- **ClientsPage** — list + Add Client (admin only) → `AddClientModal` → POST → list refreshes. Row → `/clients/:id`.
- **ClientDetailPage** — header, details card, readiness checklist, **assignments table with effective identifier per assignment**, "Edit identifier" button per assignment row (admin only) → `SetIdentifierModal`.
- **DatasourcesPage** — list (default ACTIVE+DEGRADED). "Add Datasource" (admin only) → `/datasources/add`. **Per-row "Inactivate" button (admin only)** → `InactivateConfirmModal`.
- **AddDatasourcePage** — admin only. 4-step wizard. Activate → 202 → full-page "Activating…" overlay → poll → ACTIVE: navigate `/datasources` + toast. DEGRADED: error toast + "see Job Runs".
- **ClientSourceMappingPage (v4 layout)** — split pane:
  - Left: scrollable client list (readiness badge + count).
  - Right: header (client name + readiness) + 4 stat cards + **prominent "+ Assign Datasource" CTA at top of right pane (admin only)** opens `AssignDatasourceModal` (datasource picker + identifier override fields). Then search/filter bar; then **Active Assignments** grouped by category showing per-source identifier and management buttons (Make Billing Source, Make Identity Anchor, Edit Identifier, Inactivate); then collapsed-by-default **Inactive Assignments** section. Available datasources accessed via the Assign modal, not as a separate scrollable section.
- **ReportsPage** — generation form: Client → Report Type (license/endpoint) → Period → **DatasourcePickerModal-driven multi-select for `datasourceIds`** (default: all matching-category active assignments selected; user unchecks to exclude) → Readiness check → Generate. Bottom: Recent Reports table showing included datasource names per row.
- **ReportPreviewPage** — header, summary cards, exceptions panel, "Download XLSX".
- **JobRunsPage** — list with status filter chips.
- **SettingsPage** — prototype UI, not wired.
- **ForbiddenPage** — "You don't have access. Contact your MSP admin." + back button.

### State management discipline (recap)
- All server data → TanStack Query hooks in `src/hooks/`. Never axios from a component.
- All client global state → Zustand. No prop drilling >1 level.
- Component-local state → `useState` only for non-shared UI flags.

### Report generation — invokes a real AWS Lambda

Report generation does **not** run inside FastAPI. Delegated to real AWS Lambda (`AWS_REPORT_LAMBDA_NAME`) deployed in the user's existing AWS account.

**Flow:**
1. User picks Client + Report Type + Period + **datasource subset** → SPA POSTs `/reports/generate`.
2. Backend readiness check (client has at least one ACTIVE assigned datasource of matching category, and selected `datasourceIds` are all valid + ACTIVE + match category) → 400 if not.
3. Backend creates `report_runs` row (`status='GENERATING'`, `included_datasource_ids` populated), returns `202 {reportId}`.
4. BackgroundTasks job:
   - For each selected datasource: read DynamoDB mapping doc + LocalStack S3 `data.json` → stage to real-AWS S3 `{AWS_REPORT_S3_BUCKET}/staging/{reportId}/{datasourceId}/data.json`.
   - Build payload (sourceDataS3Uri per source).
   - Invoke real-AWS Lambda via `boto3.client('lambda',...)` with `RequestResponse`, 120 s timeout.
   - Success → update report_runs `READY`, `s3_uri`, `rows_count`, `exceptions_count`. Cache presigned URL in Redis 4-min TTL (URL TTL 10-min).
   - Failure → update `FAILED`, `error_message`.
5. Frontend polls `/reports/:id` every 2 s → on `READY`/`FAILED` navigate `/reports/:id`.
6. Download XLSX → `/reports/:id/download` → 302 to cached presigned URL.

**Lambda payload:**
```json
{
  "reportId":"<uuid>","mspId":"<uuid>","mspName":"MVP MSP",
  "clientId":"<uuid>","clientName":"Acme Corp",
  "reportType":"endpoint","period":"2026-04",
  "outputBucket":"<AWS_REPORT_S3_BUCKET>",
  "outputKeyPrefix":"reports/msp_id=<...>/client_id=<...>/report_type=endpoint/period=2026-04/",
  "sources":[
    {"datasourceId":"<uuid>","vendor":"Datto RMM","category":"ENDPOINT",
     "clientIdentifierForSource":{"type":"COMPANY_NAME_EQUALS","value":"Acme Corp Inc."},
     "mapping":{...full DDB mapping...},
     "sourceDataS3Uri":"s3://<bucket>/staging/<reportId>/<datasourceId>/data.json"}
  ],
  "presignedUrlTtlSeconds":600
}
```
The `clientIdentifierForSource` is the **effective identifier** for that (client, datasource) pair — taken from the assignment override if set, else the client's default. Lambda uses it to filter records.

**Lambda response:** `{status:'READY', reportId, s3Uri, presignedUrl, rowsCount, exceptionsCount, summary:{}, exceptions:[], generatedAt}`. On error: `{status:'FAILED', error:{code,message}}` HTTP 200.

---

## 12. AWS Integration via LocalStack

LocalStack Community in Docker. boto3 with env-driven endpoint URLs.

`infra/localstack/init/01-bootstrap.sh` on startup:
1. S3 bucket `msp-guardian-poc`.
2. Prefix structure (empty `.keep` markers): `tmp/, samples/, landing/, raw/, curated/, quarantine/, reports/, mappings/`.
3. DynamoDB `msp_guardian_mappings` (pk HASH, sk RANGE).
4. Glue DB `msp_guardian_poc`.
5. Package + deploy Lambda `testDatasourceConnection`.
6. Placeholder Secrets Manager secret.

**Two boto3 clients in `app/services/aws_clients.py`:**
```python
def localstack_client(service):
    return boto3.client(service, endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

def real_aws_client(service):
    return boto3.client(service, region_name=settings.AWS_REPORT_REGION,
        aws_access_key_id=settings.AWS_REPORT_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_REPORT_SECRET_ACCESS_KEY)
```

**Service routing:**
| Service | LocalStack | Real AWS |
|---|---|---|
| Test-Connection Lambda | ✓ | – |
| Secrets Manager | ✓ | – |
| S3 (sample, landing, mappings) | ✓ | – |
| DynamoDB (mappings) | ✓ | – |
| Glue Catalog | ✓ | – |
| Report Generator Lambda | – | ✓ |
| Report output S3 + staging | – | ✓ |

---

## 12.5. Report Generator Lambda (real AWS, deployed separately)

`backend/lambdas/report_generator/handler.py`. **Not** deployed by `docker compose up` — deploy once via `deploy.sh`.

**Runtime:** Python 3.12 (AWS Lambda has no 3.14). Reuses `app/services/transforms.py` copied into deployment package by `deploy.sh`.

**Handler responsibilities:**
1. Validate payload shape.
2. For each source: read `sourceDataS3Uri` from S3; **filter records using `clientIdentifierForSource`** (the per-source identifier passed in payload); apply mapping transforms; apply `postProcessing.explodeArrays` and `deduplicateBy`.
3. Merge across sources keyed by Endpoint→`device_hostname` / Licensing→`user_email`.
4. Compute exceptions:
   - Endpoint: device in one source missing protection in another.
   - Licensing: user has license but disabled, licensed in M365 missing in Proofpoint, etc.
5. Render XLSX (openpyxl):
   - Sheet 1 — Summary: counts, period, client, sources included.
   - Sheet 2 — Detail: merged standardized rows.
   - Sheet 3 — Exceptions: one row per finding.
   - Sheet 4 — Audit: mspId, clientId, reportId, generatedAt, source datasource IDs + mapping versions + identifier rule used per source.
6. PUT XLSX to `s3://{outputBucket}/{outputKeyPrefix}{reportId}.xlsx`.
7. Generate presigned GET URL (TTL = `presignedUrlTtlSeconds`).
8. Return response shape from §11.

**Lambda execution-role IAM:** `s3:PutObject + s3:GetObject` on `<bucket>/reports/*`; `s3:GetObject` on `<bucket>/staging/*`; CloudWatch logs.

**Backend invoker IAM:** `lambda:InvokeFunction` on the Lambda ARN; `s3:PutObject + s3:DeleteObject` on `staging/*`; `s3:GetObject` on `reports/*`.

**`deploy.sh`:** zip handler + `pip install --target package -r requirements.txt` + copy transforms.py → `aws lambda update-function-code`.

---

## 13. Error Handling

| Case | HTTP | code |
|---|---|---|
| Invalid login | 401 | INVALID_CREDENTIALS |
| Missing/expired access token | 401 | TOKEN_EXPIRED |
| Invalid refresh token | 401 | INVALID_REFRESH_TOKEN |
| **Role forbidden** | 403 | **ROLE_FORBIDDEN** |
| Vendor API timeout | 504 | UPSTREAM_TIMEOUT |
| Empty vendor response | 400 | EMPTY_RESPONSE |
| Vendor auth failure | 400 | VENDOR_AUTH_FAILED |
| Invalid custom parameter | 400 | INVALID_CUSTOM_PARAMETER |
| Schema preview expired | 410 | PREVIEW_EXPIRED |
| Required mapping missing | 400 | REQUIRED_MAPPING_MISSING |
| schemaHash mismatch | 400 | SCHEMA_HASH_MISMATCH |
| Reconciliation activation | 501 | NOT_IMPLEMENTED |
| Client name conflict | 409 | CLIENT_NAME_TAKEN |
| Duplicate assignment | 409 | ALREADY_ASSIGNED |
| Wrong category for billing | 400 | INVALID_BILLING_SOURCE |
| Wrong category for identity | 400 | INVALID_IDENTITY_ANCHOR |
| **Assignment is inactive** | 400 | **ASSIGNMENT_INACTIVE** |
| **Invalid identifier** | 400 | **INVALID_IDENTIFIER** |
| **Invalid datasource selection (reports)** | 400 | **INVALID_DATASOURCE_SELECTION** |
| Report readiness fail | 400 | READINESS_FAILED |
| Report Lambda timeout | 504 | REPORT_LAMBDA_TIMEOUT |
| Report Lambda error | 502 | REPORT_LAMBDA_ERROR |
| Real AWS creds missing | 500 | AWS_REPORT_CREDENTIALS_MISSING |
| Secrets Manager error | 502 | SECRETS_MANAGER_ERROR |
| S3 error (sync) | 502 | S3_ERROR |
| DynamoDB error (sync) | 502 | DYNAMODB_ERROR |
| Glue error (sync) | 502 | GLUE_ERROR |
| Postgres failure (Phase 1) | 500 | ACTIVATION_FAILED |
| Background activation failure | datasource → DEGRADED | ACTIVATION_BACKGROUND_FAILED |

Global FastAPI exception handler maps `boto3.exceptions.ClientError` → appropriate code.

---

## 14. Seed Data (`backend/app/seed.py`)

Idempotent. Runs on container start after migrations.

**MSP:** `name="MVP MSP"`, `email="ops@mvp.com"`.

**Users (2):**
- `testmsp@mvp.com` / `testmsp@123` — role `MSP_ADMIN`, full_name "Test MSP Admin"
- `analyst@mvp.com` / `analyst@123` — role `MSP_ANALYST`, full_name "Demo Analyst"
Passwords bcrypt-hashed before insert.

**Clients (4):**
- ERES Companies — default identifier `EMAIL_DOMAIN_CONTAINS=erescompanies.com`
- Scoop Ride — `EMAIL_DOMAIN_CONTAINS=scoopride.io`
- Pinnacle Legal — `EMAIL_DOMAIN_CONTAINS=pinnaclelegal.com`
- Harbor View Medical — `EMAIL_DOMAIN_CONTAINS=harborviewmed.org`

**Datasources (8):**
- M365 Production (Licensing, Active)
- Proofpoint Core (Licensing, Active)
- Ironscales (Licensing, Degraded — drives dashboard alert)
- DropSuite (Licensing, Active)
- Datto RMM (Endpoint, Active)
- SentinelOne (Endpoint, Active)
- Autotask Billing (Reconciliation, Active)
- ThreatLocker (Endpoint, Draft)

**Assignments (with v4 per-source identifiers — demonstrates the override pattern):**
- ERES Companies:
  - M365: identifier inherited from default; identity_anchor=true
  - Proofpoint: inherited
  - Ironscales: inherited
  - DropSuite: inherited
  - Datto RMM: **override** `COMPANY_NAME_EQUALS=ERES Companies Inc.`
  - SentinelOne: **override** `TENANT_ID_EQUALS=eres-tnt-001`
  - Autotask Billing: inherited; billing_source=true
- Scoop Ride: M365, Proofpoint, DropSuite, Datto RMM (inherited), Autotask (inherited, billing); identity_anchor=M365
- Pinnacle Legal: M365 (identity_anchor), Datto RMM (override `COMPANY_NAME_EQUALS=Pinnacle Legal LLP`)
- Harbor View Medical: no assignments

**Job runs (7, last 48h):** 1 FAILED for Ironscales + 6 SUCCESS.

**Landing JSON files** seeded to S3 (so reports work from day one):
- `s3://msp-guardian-poc/landing/.../{datto_id}/run_id=seed/data.json` — 5 endpoints across ERES, Scoop, Pinnacle (with their respective per-source identifiers)
- `s3://msp-guardian-poc/landing/.../{sentinelone_id}/run_id=seed/data.json` — 4 endpoints for ERES (1 missing vs Datto → drives a "gap" exception)

`ON CONFLICT DO NOTHING` for Postgres; if-not-exists for S3.

---

## 15. Local Development Setup

### `docker-compose.yml`
```
services:
  postgres:    postgres:16-alpine — env DB=MSP_Guardian, port 5432, vol postgres_data, healthcheck pg_isready
  redis:       redis:7-alpine, port 6379, healthcheck redis-cli ping
  localstack:  localstack/localstack:3.x, port 4566, mounts ./infra/localstack/init/, vol localstack_data
  backend:     build ./backend, depends_on (healthchecked), port 8000
               cmd: alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --reload
  frontend:    build ./frontend, depends_on backend, port 5173
               cmd: npm run dev -- --host
```
Network `msp_net`. Backend waits for healthy postgres+redis+localstack.

### `.env.example`
```
# --- Postgres ---
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=MSP_Guardian
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/MSP_Guardian

# --- Redis ---
REDIS_URL=redis://redis:6379/0

# --- JWT ---
JWT_SECRET=dev-secret-change-me-in-prod
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=7

# --- AWS / LocalStack ---
AWS_ENDPOINT_URL=http://localstack:4566
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# --- S3 buckets and prefixes ---
S3_BUCKET=msp-guardian-poc
S3_TMP_PREFIX=tmp/schema-preview
S3_SAMPLES_PREFIX=samples
S3_LANDING_PREFIX=landing
S3_RAW_PREFIX=raw
S3_CURATED_PREFIX=curated
S3_QUARANTINE_PREFIX=quarantine
S3_REPORTS_PREFIX=reports
S3_MAPPINGS_PREFIX=mappings

# --- DynamoDB / Glue / Secrets / Lambda ---
DYNAMODB_TABLE=msp_guardian_mappings
GLUE_DATABASE=msp_guardian_poc
SECRETS_PREFIX=msp-guardian
LAMBDA_TEST_CONNECTION_NAME=testDatasourceConnection

# --- REAL AWS — Report Generator Lambda ---
AWS_REPORT_REGION=us-east-1
AWS_REPORT_ACCESS_KEY_ID=<replace>
AWS_REPORT_SECRET_ACCESS_KEY=<replace>
AWS_REPORT_LAMBDA_NAME=msp-guardian-report-generator
AWS_REPORT_S3_BUCKET=<replace>
AWS_REPORT_INVOKE_TIMEOUT_SECONDS=120
AWS_REPORT_PRESIGNED_URL_TTL_SECONDS=600

# --- CORS + frontend ---
CORS_ORIGINS=http://localhost:5173
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

All S3 paths in code MUST be built from env vars — never hardcoded.

---

## 16. Tests (minimum)

- `test_auth.py` — login happy/wrong-password, refresh, logout marks login_history.
- `test_roles.py` — admin can write; analyst gets 403 on writes; analyst can generate reports. **(v4)**
- `test_clients.py` — create/dup/list/patch/delete; default identifier persisted.
- `test_assignments.py` — assign with identifier override; assign without override (uses default); set-billing rejects wrong category; **inactivate marks status; reactivate restores; one-billing-source partial index respects status**. **(v4)**
- `test_datasource_activation.py` — full activation; mock vendor API; assert 202 ACTIVATING → ACTIVE polled, DDB item, Glue table, landing data.json.
- `test_soft_delete.py` — inactivate datasource cascades to assignments; historical job_runs/report_runs still readable; new wizard cannot pick INACTIVE datasource. **(v4)**
- `test_report_generation.py` — POST `/reports/generate` with explicit `datasourceIds` selection; assert XLSX in S3; included sources match selection. **(v4 — selection branch added)**

`pytest`, `pytest-asyncio`, `httpx.AsyncClient`. No frontend tests for POC.

---

## 17. README Requirements

Sections:
1. **What this is** — POC of MSP Guardian, what the demo shows.
2. **Prerequisites** (Windows): Docker Desktop, Git, VS Code, AWS CLI v2 (real AWS account), Node 20 (only outside Docker), Python 3.14.3 (only outside Docker).
3. **One-time AWS setup** — S3 bucket; IAM user with `lambda:InvokeFunction` + staging S3 perms; Lambda execution role; create Lambda (Python 3.12, 512 MB, 120 s); deploy via `cd backend/lambdas/report_generator && ./deploy.sh msp-guardian-report-generator us-east-1`.
4. **Quick start (Docker)** — clone → `cp .env.example .env` → edit `AWS_REPORT_*` → `docker compose up --build` → http://localhost:5173 → login.
5. **Outside Docker** — backend `python -m venv .venv && .venv\Scripts\activate && pip install -e . && alembic upgrade head && python -m app.seed && uvicorn app.main:app --reload`. Frontend `npm install && npm run dev`. Postgres/Redis/LocalStack still in Docker.
6. **Demo script (10 minutes click-by-click for the LeafTech meeting):**
   1. Login as admin (`testmsp@mvp.com`).
   2. Dashboard tour — point out failed-run alert (Ironscales).
   3. Add Client → modal → "Acme Corp" / `EMAIL_DOMAIN_CONTAINS=acmecorp.com` → list refreshes.
   4. Add Datasource (Endpoint, Datto RMM Trial, name "Datto — Acme", scope MSP-level) → Step 2 paste credentials → Test Connection → green banner → Step 3 **see 4–5 sample rows preview at top** → map fields → Step 4 Daily 02:00 → Activate → "Activating…" overlay → green ACTIVE.
   5. Open Client Source Mapping → select Acme → click prominent "+ Assign Datasource" → pick the new Datto datasource → **set per-source identifier** `COMPANY_NAME_EQUALS=Acme Corp Inc.` → readiness flips to READY.
   6. Open Reports → Acme → Endpoint Audit → April 2026 → **DatasourcePicker** modal lets you uncheck unwanted sources → Generate (real-AWS Lambda) → preview → Download XLSX.
   7. Logout (confirmation modal). **Log in as `analyst@mvp.com`** → show Datasources/Mapping pages have no write buttons → analyst can still generate reports → logout.
7. **Architecture overview** — short text.
8. **Project structure** — paste tree.
9. **Environment variables** — table from `.env.example`.
10. **Known limitations**:
    - Activation Phase 2 not transactional with Postgres.
    - Refresh token in localStorage.
    - Idle 1 min is demo-only.
    - Reconciliation not implemented.
    - No real scheduled runs.
    - Hybrid AWS topology.
    - Source data staged via S3 — add lifecycle rule on `staging/*` for production.
11. **Production migration path** — replace LocalStack; promote landing direct to real AWS; Step Functions for retries; EventBridge for schedules.
12. **Troubleshooting** — Docker daemon, LocalStack bootstrap, CORS, seed didn't run, schema preview expired, report stuck on Generating, Lambda timeout, presigned 403, staging upload fails, **403 ROLE_FORBIDDEN** (signed in as analyst trying admin action).

Junior-dev runnable on Windows. Code blocks for every command. PowerShell vs bash differences only where they matter.

---

## 18. Acceptance Criteria — Self-check

1. File tree from §5 generated; no placeholder/empty files in critical paths.
2. `docker compose up` boots all services with no manual steps.
3. Migration creates tables in §6 against database literally `MSP_Guardian`.
4. `msps.email`, `users.role` (CHECK MSP_ADMIN|MSP_ANALYST), `client_datasource_assignments.identifier_type/value/status/inactivated_at`, `datasources.inactivated_at/by`, `report_runs.included_datasource_ids` all present.
5. Partial unique indexes on assignments are conditioned on `status='ACTIVE'`.
6. Seed inserts both `testmsp@mvp.com` (MSP_ADMIN) and `analyst@mvp.com` (MSP_ANALYST). MSP has email.
7. `/auth/login` returns valid JWT with `role` claim. `/auth/me` returns role.
8. Backend `require_role('MSP_ADMIN')` dependency rejects analyst with 403 `ROLE_FORBIDDEN`.
9. `testDatasourceConnection` Lambda has real `handler.py`, deployed to LocalStack.
10. Activation executes §9 Phase 1 + Phase 2 in order, for both LICENSING and ENDPOINT.
11. `schema-preview` and `test-connection` responses include `sampleRows` (≤5 records).
12. Step 3 UI renders `SampleRowsPreview` table above mapping table; selected source column highlights in preview.
13. DynamoDB mapping item shape matches §10.
14. Endpoint mapping has all 8 standard fields wired.
15. Clients page real CRUD; Add Client persists + list refreshes.
16. Client Source Mapping page: prominent "+ Assign Datasource" CTA at top of right pane (admin only). Per-source identifier capture works. Inactivate sets status; reactivate restores. Inactive section collapsed by default.
17. Reports page generation form includes `DatasourcePickerModal`. Per-report `datasourceIds` honored end-to-end (audit shows them in `report_runs.included_datasource_ids` and XLSX Audit sheet).
18. Report generation invokes real AWS Lambda via `boto3` with real-AWS credentials. Backend uses two separate `boto3` clients. XLSX in real-AWS S3, presigned URL works.
19. `report_generator/handler.py` complete deployable artifact with `requirements.txt` and `deploy.sh`. Reuses `transforms.py`. Filters records by `clientIdentifierForSource` per source.
20. Zustand stores used for ALL client-side state. No prop drilling >1 level. No React Context for app state.
21. All S3 paths built from env-driven prefixes — none hardcoded.
22. Login + idle (1 min) + logout confirm + role-based UI hiding all work per §8/§11.
23. README junior-dev runnable on Windows; demo script reflects v4 (sample rows, per-source identifier, datasource picker, analyst role).
24. No `console.log`, no `// TODO`, no dummy returns in any auth/activation/report path.
25. Python base image `python:3.14.3-slim` in `backend/Dockerfile`.

---

## 19. Output Format

1. One-paragraph plan (≤80 words).
2. Complete file tree (ASCII).
3. Each file's full content as `### path` + fenced block. No prose between files.
4. Files >200 lines split into logical sub-files.

---

## 20. Constraints — DO NOT

- Cognito. EventBridge schedules.
- Store raw JWTs.
- Store API credentials in Postgres (only `secret_arn`).
- Put transformation logic in Glue Catalog or DynamoDB. Glue describes physical layout; DynamoDB references transforms by name.
- Hardcode S3 prefixes — always pull from env.
- Hard-delete a datasource that has any assignments or job_runs/report_runs. Use inactivate.
- Class components in React. Hooks only.
- `any` in TypeScript except for genuinely unknown JSON.
- `from sqlalchemy.orm import sessionmaker` (sync). Use `async_sessionmaker`.
- `pydantic.BaseSettings` (v1). Use `pydantic_settings.BaseSettings`.
- React Context for app state — Zustand only. Context allowed as thin wrapper for QueryClientProvider/Router only.
- Call axios directly from a component — go through TanStack Query hook in `src/hooks/`.
- Ask follow-up questions. State assumptions in README under "Assumptions made" and proceed.

---

## 21. Assumption Handling

If unclear, write the assumption as a single sentence in the README under "Assumptions made" and proceed. No TODOs. No stubs in critical paths (auth, activation, mapping, report generation).

---

**End of prompt. Begin generating.**
