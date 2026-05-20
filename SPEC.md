# MSP Guardian POC — Code Generation Prompt (v7.1)

> **How to use:** paste this entire document into any frontier AI coding tool (Claude, ChatGPT, Cursor, Copilot Chat, Cline, etc.). It is self-contained. Do not split it across messages unless your tool's context limit forces a split — in that case break at section boundaries, not mid-section.
>
> **What changed in v7.1** (from v4): Client Source Mapping page removed — client selection moved to wizard Step 1; datasource wizard now template/blueprint-driven (pre-configured SPECS replacing freeform Identify step); authentication fields driven by connector blueprint instead of generic auth-type dropdown; notification toast system and confirmation modals added; login Remember Me checkbox; datasource list client-filter; Settings page enhanced with email + timezone.

---

## 1. Role

You are a **senior full-stack engineer** specializing in React + Python FastAPI + AWS. You write production-quality POC code: typed, tested, runnable in Docker on day one, with no TODOs in critical paths. You are pragmatic — this is a POC for a client demo, not a production system. You favor working code over perfect code, but you do not cut corners on security primitives (password hashing, secret handling, SQL injection prevention) or on state-management discipline.

---

## 2. Goal

Build a working end-to-end POC of **"MSP Guardian"** — a multi-tenant platform for Managed Service Providers (MSPs) like LeafTech to onboard third-party SaaS APIs as data sources via a blueprint-driven wizard, assign them to clients with per-source identifiers, and produce audit reports. The POC must demo the following live to a client:

1. MSP Admin logs in with seeded credentials (Remember Me option persists session).
2. MSP Admin lands on a dashboard showing seeded clients, datasources, and recent job runs.
3. MSP Admin **adds a new client** in real time (form → Postgres row → list refresh).
4. MSP Admin adds a new **Endpoint** datasource via a 4-step **blueprint-driven** wizard:
   - **Step 1 — Client & Template:** select target client from dropdown, select a connector blueprint (e.g. "Datto RMM"), optionally override the display name.
   - **Step 2 — Authentication:** blueprint pre-populates credential fields (e.g. API URL, API Key, Secret); user enters values → **Test Connection** → real Lambda call → returns record count + column count + time taken.
   - **Step 3 — Map Fields:** sample data preview (real API rows) above the mapping table; default mappings pre-filled from blueprint; optional additional parameters section.
   - **Step 4 — Schedule & Activate:** frequency/time (stored only — no actual scheduler); Activate button.
5. MSP Admin clicks **Activate** → backend writes mapping to DynamoDB, fetches the full data file from the source API, saves to landing S3, registers a Glue Catalog table.
6. MSP Admin opens **Client Detail** for the newly created client, views assigned datasources, sees identity anchor and billing source flags.
7. MSP Admin opens **Reports**, generates an **Endpoint Audit** report for that client, **selects which datasources to include** in the report → backend reads landing JSON, applies the DynamoDB mapping, renders an XLSX, returns presigned URL.
8. **Demonstrate role separation:** log out, log in as `analyst@mvp.com` → sidebar Datasources page has no Add/Inactivate buttons; analyst can still generate reports.
9. MSP Admin can log out via a confirmation modal; idle timeout (1 minute, demo-tuned) prompts continue/logout.

**This POC is not for scale, not for multi-region, not for production hardening.** It is for a 15-minute demo that hits every screen.

---

## 3. Scope — What's IN, What's OUT

**IN scope (must fully work end-to-end):**
- Login + JWT auth + Remember Me + login history + protected routes + logout confirmation + idle timeout (1 min)
- **Two roles: `MSP_ADMIN` (write) and `MSP_ANALYST` (read + report-generate only)** with backend role guards and frontend button-hiding
- Dashboard with `/dashboard/summary` API + seeded data; toast/notification system; confirmation modals
- **Clients module — real-time CRUD** (list, add, view detail with assignments + identifiers). Must match prototype behavior.
- **Datasource Onboarding Wizard — blueprint-driven, for both `Licensing` AND `Endpoint` categories**, end-to-end (Steps 1 → 4 + Activate). Endpoint category is the demo focus.
  - Step 1 selects client + connector blueprint (SPECS loaded from DynamoDB `connector_registry`)
  - Step 2 renders credential fields from blueprint; Test Connection invokes Lambda
  - Step 3 shows real sample data preview above mapping table; blueprint pre-fills default mappings; optional parameters section
  - Step 4 Schedule & Activate stores schedule metadata; polls until ACTIVE
- **Soft-delete (inactivation) for datasources** — historical reports keep working
- **Connector blueprint registry** seeded to DynamoDB `connector_registry` (8 blueprints: M365, Proofpoint, Ironscales, DropSuite, Datto RMM, SentinelOne, Autotask, Custom)
- **Report Generation — real**, for both `license` and `endpoint` report types. User picks specific datasources to include per report run. Must read landing JSON from S3, apply the DynamoDB mapping, output XLSX to S3 (real AWS), return presigned URL.
- LocalStack for AWS service emulation (S3, Secrets Manager, Lambda, DynamoDB, Glue Catalog)
- Docker Compose for full local stack
- Idempotent seed script with realistic data (including 2 users — admin + analyst)
- README with Windows + Docker + VS Code instructions

**OUT of scope (stub or skip):**
- **Reconciliation category** — wizard accepts it via a "Custom" blueprint but Steps 3+ show "POC: Reconciliation not implemented yet." Activation returns 501.
- **Client Source Mapping as a dedicated page** — removed. Assignment management lives in Client Detail view and wizard Step 1.
- Real scheduled ingestion (no EventBridge, no cron triggers — schedule metadata is stored, never executed).
- Multi-MSP isolation enforcement (single MSP only — `mspId` taken from JWT but not heavily validated cross-tenant).
- Cognito (custom JWT instead).
- HTTPS / TLS (HTTP localhost only).
- Job Runs page advanced filtering (basic status filter only).
- Settings page persistence (renders prototype UI, no backend wiring except timezone display).
- File-upload datasource type (API only — CSV Upload blueprint shows "not implemented" stub).
- Anomaly detection (post-MVP).
- Training manual generation (PRD / README mention only).

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
| DynamoDB mappings table | `msp_guardian_mappings` |
| DynamoDB blueprints table | `connector_registry` |
| Glue database | `msp_guardian_poc` |
| Container runtime | Docker + Docker Compose v2 |
| Idle timeout | 1 minute (demo-tuned — intentional, do not change) |

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
│   │   ├── schemas/{auth, dashboard, client, datasource, connector, mapping, report, common}.py
│   │   ├── api/
│   │   │   ├── deps.py                  # auth dependency, db dep, role guard
│   │   │   └── v1/{auth, dashboard, clients, client_assignments,
│   │   │            connectors, datasource_drafts, datasources,
│   │   │            job_runs, reports}.py
│   │   ├── services/
│   │   │   ├── auth_service.py, login_history_service.py, dashboard_service.py
│   │   │   ├── client_service.py, client_assignment_service.py
│   │   │   ├── secrets_service.py, redis_service.py, schema_inference.py
│   │   │   ├── lambda_service.py, s3_landing_service.py, glue_catalog_service.py
│   │   │   ├── connector_service.py, mapping_service.py, transforms.py, report_service.py
│   │   │   └── aws_clients.py
│   │   └── seed.py
│   ├── lambdas/
│   │   ├── test_datasource_connection/{handler.py, requirements.txt}
│   │   └── report_generator/{handler.py, requirements.txt, deploy.sh, README.md}
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py, test_roles.py
│       ├── test_clients.py, test_assignments.py
│       ├── test_connectors.py
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
│       │   ├── useConnectors.ts, useSchemaPreview.ts, useReports.ts
│       │   └── useRole.ts
│       ├── components/
│       │   ├── layout/{Sidebar.tsx, AppShell.tsx, NotificationBell.tsx}
│       │   ├── modals/
│       │   │   ├── IdleSessionModal.tsx, LogoutConfirmModal.tsx
│       │   │   ├── AddClientModal.tsx, AssignDatasourceModal.tsx
│       │   │   ├── SetIdentifierModal.tsx, InactivateConfirmModal.tsx
│       │   │   ├── ChangeAnchorModal.tsx, DatasourcePickerModal.tsx
│       │   │   └── ConfirmModal.tsx
│       │   ├── notifications/Toast.tsx, ToastContainer.tsx
│       │   ├── ProtectedRoute.tsx, RoleGuard.tsx
│       │   ├── ui/{Button, Input, Select, Card, Table, Badge, EmptyState, Spinner}.tsx
│       │   └── wizard/
│       │       ├── WizardStepper.tsx
│       │       ├── StepClientTemplate.tsx      ← v7.1 (was StepIdentify)
│       │       ├── StepAuthentication.tsx       ← v7.1 (was StepConnect)
│       │       ├── StepMapFields.tsx, SampleRowsPreview.tsx
│       │       └── StepScheduleActivate.tsx     ← v7.1
│       ├── pages/
│       │   ├── LoginPage.tsx, DashboardPage.tsx
│       │   ├── ClientsPage.tsx, ClientDetailPage.tsx
│       │   ├── DatasourcesPage.tsx, AddDatasourcePage.tsx
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
        CHECK (role IN ('MSP_ADMIN','MSP_ANALYST'))
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
  default_identifier_type VARCHAR(60) NOT NULL
  default_identifier_value VARCHAR(160) NOT NULL
  readiness VARCHAR(20) NOT NULL DEFAULT 'NEEDS_SETUP'
  s3_base_path VARCHAR(500) NULL                    -- v7.1 gap: slugified S3 prefix set on first draft; never updated on name change
  created_at, updated_at
  UNIQUE(msp_id, name)

datasource_drafts
  id UUID PK
  msp_id UUID FK, created_by UUID FK -> users.id
  client_id UUID FK -> clients.id NULL              -- v7.1: target client selected in Step 1
  blueprint_id VARCHAR(80) NULL                     -- v7.1: connector_registry source_id
  name VARCHAR(160) NOT NULL                        -- vendor name (e.g. "Datto RMM")
  display_name VARCHAR(200) NULL                    -- v7.1 gap: user-facing label e.g. "DattoRMM/Acme Corp"
  vendor VARCHAR(160) NOT NULL
  category VARCHAR(40) NOT NULL CHECK (category IN ('LICENSING','ENDPOINT','RECONCILIATION'))
  source_type VARCHAR(40) NOT NULL CHECK (source_type IN ('API','FILE_UPLOAD'))
  scope VARCHAR(40) NOT NULL CHECK (scope IN ('MSP_LEVEL','CLIENT_SPECIFIC'))
  secret_arn VARCHAR(400) NULL
  last_attempt_id UUID NULL                         -- attemptId from last test-connection call
  current_step SMALLINT NOT NULL DEFAULT 1
        CHECK (current_step BETWEEN 1 AND 4)        -- v7.1 gap: resume wizard at correct step
  schema_hash CHAR(64) NULL                         -- v7.1 gap: SHA-256 from test-connection; Postgres fallback when Redis expires
  sample_s3_path TEXT NULL                          -- v7.1 gap: S3 key of sample.json written by Lambda
  draft_payload JSONB NULL                          -- v7.1 gap: spare store for vendor details + selection cache snapshot
  status VARCHAR(40) NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT','ACTIVATED','ABANDONED'))  -- v7.1 gap: CHECK was missing
  created_at, updated_at

datasources
  id UUID PK
  msp_id UUID FK
  draft_id UUID FK NULL
  client_id UUID FK -> clients.id NULL              -- v7.1: client from wizard Step 1
  blueprint_id VARCHAR(80) NULL                     -- v7.1: connector_registry source_id
  name VARCHAR(160) NOT NULL
  vendor VARCHAR(160) NOT NULL
  category VARCHAR(40) NOT NULL
  source_type VARCHAR(40) NOT NULL
  scope VARCHAR(40) NOT NULL
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','ACTIVATING','DRAFT','DEGRADED','DISABLED','INACTIVE'))
  active_mapping_version INT NOT NULL DEFAULT 1
  secret_arn VARCHAR(400) NOT NULL                  -- updated to permanent path after Phase 3 rename
  schema_hash CHAR(64) NULL                         -- v7.1 gap: activation-time schema hash for drift detection
  glue_table_name VARCHAR(200) NULL
  landing_path VARCHAR(500) NULL
  last_run_at TIMESTAMPTZ NULL
  inactivated_at TIMESTAMPTZ NULL
  inactivated_by UUID FK -> users.id NULL
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
  is_billing_source BOOLEAN NOT NULL DEFAULT FALSE
  is_identity_anchor BOOLEAN NOT NULL DEFAULT FALSE
  identifier_type VARCHAR(60) NULL
  identifier_value VARCHAR(160) NULL
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','INACTIVE'))
  inactivated_at TIMESTAMPTZ NULL
  inactivated_by UUID FK -> users.id NULL
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT now()
  assigned_by UUID FK -> users.id
  UNIQUE(client_id, datasource_id)
  -- Partial unique indexes:
  --   CREATE UNIQUE INDEX ux_client_billing_source
  --     ON client_datasource_assignments(client_id) WHERE is_billing_source = TRUE AND status = 'ACTIVE'
  --   CREATE UNIQUE INDEX ux_client_identity_anchor
  --     ON client_datasource_assignments(client_id) WHERE is_identity_anchor = TRUE AND status = 'ACTIVE'

job_runs
  id UUID PK
  msp_id FK, datasource_id FK NULL, client_id FK NULL
  draft_id UUID FK -> datasource_drafts.id NULL     -- v7.1 gap: set for TEST_CONNECTION jobs (no datasource yet)
  job_type VARCHAR(40) NOT NULL        -- TEST_CONNECTION, ACTIVATION, SCHEDULED, MANUAL, REPORT_GENERATION
  status VARCHAR(20) NOT NULL          -- SUCCESS, FAILED, PARTIAL, RUNNING
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
  report_type VARCHAR(40) NOT NULL     -- 'license' | 'endpoint'
  period VARCHAR(20) NOT NULL          -- 'YYYY-MM'
  status VARCHAR(20) NOT NULL DEFAULT 'PENDING'  -- PENDING, GENERATING, READY, FAILED
  s3_uri VARCHAR(500) NULL
  rows_count INT NULL
  exceptions_count INT NULL
  included_datasource_ids UUID[] NOT NULL DEFAULT '{}'
  generated_at TIMESTAMPTZ NULL
  generated_by FK -> users.id
  error_message TEXT NULL
  created_at
```

Indexes: `users(email)`, `login_history(user_id, status)`, `datasources(msp_id, status)`, `datasources(client_id)`, `job_runs(msp_id, started_at DESC)`, `job_runs(draft_id) WHERE draft_id IS NOT NULL`, `client_datasource_assignments(client_id, status)`, `client_datasource_assignments(datasource_id, status)`, `datasource_drafts(msp_id, blueprint_id, status) WHERE status='DRAFT'`.

> **v7.1 schema changes** (connector flow gaps — see migration `V002__connector_flow_gaps.sql`):
> Added to `clients`: `s3_base_path`.
> Added to `datasource_drafts`: `display_name`, `current_step`, `schema_hash`, `sample_s3_path`, `draft_payload`; status CHECK constraint added.
> Added to `datasources`: `schema_hash`.
> Added to `job_runs`: `draft_id` FK.

---

## 7. DynamoDB Tables

### `connector_registry` — Connector Blueprint Registry

PK = `source_id` (String). Written once by engineering; read by UI to render wizard Step 1 blueprints.

```json
{
  "source_id": "datto_rmm",
  "display_name": "Datto RMM",
  "category": "ENDPOINT",
  "scope_default": "CLIENT_SPECIFIC",
  "auth_type": "token_chain",
  "description": "Datto Remote Monitoring and Management...",
  "credential_schema": [
    { "key": "api_url", "label": "API Base URL", "type": "url", "required": true,
      "default": "https://zinfandel-api.centrastage.net" },
    { "key": "api_key", "label": "API Key", "type": "secret", "required": true },
    { "key": "api_secret_key", "label": "API Secret Key", "type": "secret", "required": true }
  ],
  "auth_steps": [...],
  "schema_fields": [...],
  "default_field_mappings": { "device_hostname": "hostname", "device_type": "$.deviceType.type" }
}
```

Seeded blueprints: `microsoft_365`, `proofpoint`, `ironscales`, `dropsuite`, `datto_rmm`, `sentinelone`, `autotask_billing`, `custom`.

### `msp_guardian_mappings` — Field Mapping Documents

PK = `pk` (String, value: `DATASOURCE#<uuid>`), SK = `sk` (String, value: `MAPPING#v1`). Written on datasource activation.

---

## 8. API Contracts

All endpoints under `/api/v1`. Frontend-facing JSON `camelCase`. Errors `{ "detail": "...", "code": "..." }`.

### Auth (no role guard)
```
POST   /auth/login    {username, password, rememberMe?:boolean}
       → 200 { accessToken, refreshToken, expiresIn, user, mspId }
       → 401 INVALID_CREDENTIALS
       -- rememberMe=true → refresh token TTL extended to 30 days; default 7 days
POST   /auth/refresh  {refreshToken}             → 200 | 401
POST   /auth/logout   (Bearer)                   → 204
GET    /auth/me       (Bearer)                   → 200 {id,mspId,username,email,fullName,role}
```

JWT payload includes `role` claim. Access TTL **15 min**; refresh **7 days** (or 30 days with rememberMe).

### Dashboard (any authenticated)
```
GET /dashboard/summary
  → 200 {clientsReady,totalClients,activeDatasources,totalDatasources,
         recentRunsCount,reportsGenerated,
         failedRuns:[{id,datasourceName,error,startedAt}],
         recentActivity:[{id,status,datasourceName,clientName,type,startedAt,records}]}
```

### Connectors / Blueprints (any authenticated) — v7.1
```
GET    /connectors
       → 200 [{sourceId,displayName,category,scopeDefault,authType,description,
               credentialSchema:[{key,label,type,required,default?,hint?}]}]
       -- Reads from DynamoDB connector_registry; Redis cache 300s

GET    /connectors/{sourceId}
       → 200 {full blueprint including auth_steps, schema_fields, default_field_mappings}
       → 404 CONNECTOR_NOT_FOUND
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
       → 200 {...client, assignments:[{datasourceId,vendor,category,scope,status,
              isBillingSource,isIdentityAnchor,identifierType,identifierValue,
              effectiveIdentifierType,effectiveIdentifierValue,assignedAt,inactivatedAt}]}
PATCH  /clients/{id}   [MSP_ADMIN]
       → 200
DELETE /clients/{id}   [MSP_ADMIN]
       → 204
```

### Client Datasource Assignments (read: any; write: MSP_ADMIN only)
```
GET    /clients/{clientId}/assignments                → 200 [list]
POST   /clients/{clientId}/assignments   [MSP_ADMIN]
       Body: {datasourceId, identifierType?, identifierValue?}
       → 201 | 409 ALREADY_ASSIGNED
PATCH  /clients/{clientId}/assignments/{datasourceId}/identifier   [MSP_ADMIN]
       Body: {identifierType,identifierValue}
       → 200
PATCH  /clients/{clientId}/assignments/{datasourceId}/inactivate   [MSP_ADMIN]
       → 204
PATCH  /clients/{clientId}/assignments/{datasourceId}/reactivate   [MSP_ADMIN]
       → 204
PATCH  /clients/{clientId}/billing-source   [MSP_ADMIN]
       Body: {datasourceId|null}
       → 200 | 400 INVALID_BILLING_SOURCE | 400 ASSIGNMENT_INACTIVE
PATCH  /clients/{clientId}/identity-anchor   [MSP_ADMIN]
       Body: {datasourceId|null}
       → 200 | 400 INVALID_IDENTITY_ANCHOR | 400 ASSIGNMENT_INACTIVE
```

### Datasources (read: any; activate/inactivate: MSP_ADMIN)
```
GET    /datasources?status=ACTIVE,DEGRADED,INACTIVE&clientId={uuid}
       → list (default excludes INACTIVE; clientId filters by assigned client — v7.1)
GET    /datasources/{id}                                  → detail
PATCH  /datasources/{id}/inactivate   [MSP_ADMIN]
       → 204 (status='INACTIVE', cascades to ACTIVE assignments)
PATCH  /datasources/{id}/reactivate   [MSP_ADMIN]
       → 204
```

### Datasource Onboarding Wizard [MSP_ADMIN] — v7.1

```
POST   /datasource-drafts
       Body: {clientId, blueprintId, name?,
              -- from blueprint: category, sourceType, scope auto-resolved}
       → 201 {draftId, status:'DRAFT', blueprintDetails:{credentialSchema, defaultFieldMappings}}

POST   /datasource-drafts/{draftId}/test-connection
       Body: {credentials:{[key]:value}, attemptId}
       -- credentials keys match blueprint's credentialSchema[].key
       → 200 {testRunId,schemaHash,fields:[{name,type,nullable,sampleValues}],
              sampleRows:[{...}, ...max 5 records],
              recordCount, columnCount, connectionTimeMs,
              sampleS3Path,cached}

GET    /datasource-drafts/{draftId}/schema-preview
       → 200 {fields,schemaHash,sampleRows,recordCount,columnCount,expiresAt}
       → 410 PREVIEW_EXPIRED

POST   /datasources/activate
       Body: {draftId,
              mapping:{standardSchema,schemaHash,fieldMappings:[...],additionalParams:[...]},
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
            datasourceIds?:[uuid]}
     → 202 {reportId, status:'GENERATING'}
     → 400 READINESS_FAILED | 400 INVALID_DATASOURCE_SELECTION

GET  /reports
     → 200 [{id,clientId,clientName,reportType,period,status,generatedAt,rowsCount,
             includedDatasourceIds,includedDatasourceNames}]

GET  /reports/{id}
     → 200 {...report, summaryRows,exceptions,includedSources}

GET  /reports/{id}/download
     → 302 → presigned URL (10-min TTL; cached in Redis 4 min)
```

---

## 9. Authentication & Authorization

### JWT + bearer header
Tokens in `Authorization: Bearer <token>`. Access in **Zustand `useAuthStore`** memory only; refresh in `localStorage` via `zustand/middleware/persist`. JWT `role` claim is the single source of truth for authorization.

### Login flow (v7.1)
1. POST `/auth/login` with `{username, password, rememberMe}`. Returns `{accessToken,refreshToken,expiresIn,user,mspId}`.
2. `rememberMe=true` → refresh token TTL extended to 30 days. Frontend persists `rememberMe` flag in localStorage.
3. Server inserts `login_history` row with **SHA-256 hashes only** of both tokens.
4. axios request interceptor adds `Authorization: Bearer <token>`. Response interceptor: on 401 `TOKEN_EXPIRED` → refresh once → retry; on failure → clear store + redirect `/login`.

### Logout flow
Sidebar logout → `LogoutConfirmModal` ("Sign out?" + "Are you sure you want to sign out?" + "Sign Out" button) → POST `/auth/logout` → server marks login_history `LOGGED_OUT` → frontend clears store + pushes success toast → `/login`.

### Idle timeout (1 min)
`useIdleTimer` listens for `mousemove,keydown,click,scroll,touchstart` on `window`. On timeout, `useUiStore.idleModalOpen=true`. Continue → `/auth/refresh` → reset; Logout → same as voluntary. Paused while modal open.

### Role-based authorization
- Backend: `app/api/deps.py` exposes `require_role('MSP_ADMIN')` FastAPI dependency. On violation → 403 `ROLE_FORBIDDEN`.
- Frontend: `<RoleGuard role="MSP_ADMIN">` conditionally renders children. `useRole()` hook from auth store. Write buttons wrapped in `<RoleGuard>`. `/datasources/add` gated; analyst → `/forbidden`.

---

## 10. Datasource Onboarding Wizard (v7.1 Blueprint-Driven)

### Step 1 — Client & Template

**Fields:**
- `clientId` (required) — dropdown of all active clients. **Sets context for the entire datasource.**
- `blueprintId` (required) — dropdown populated from `GET /connectors`. Shows: display name + description summary (e.g., "3 credential fields, default license mappings"). Options include pre-configured blueprints (Microsoft 365, Proofpoint, Ironscales, DropSuite, Datto RMM, SentinelOne, Autotask Billing) plus "CSV Upload" (stub) and "Custom / Unlisted Source".
- `displayName` (optional) — pre-filled from blueprint `display_name`; user may override.

**Continue → POST `/datasource-drafts`** → stores `{clientId, blueprintId, resolvedName}` in wizard store and receives `blueprintDetails` (credentialSchema, defaultFieldMappings) back from backend.

Blueprint auto-resolves: `category`, `sourceType`, `scope` (no user input for these).

If `blueprintId === 'custom'`: notice "Custom connector — you will need to define all credential fields manually." Continue enabled; Steps 2-3 show free-form fields.
If `blueprintId === 'csv_upload'`: notice "POC: CSV Upload not implemented." Continue disabled.

### Step 2 — Authentication

**Dynamic credential form:** Backend returns `blueprintDetails.credentialSchema` (array of `{key, label, type, required, default, hint}`). Frontend renders fields generically:
- `type: "url"` → `<input type="url">` with default value pre-filled
- `type: "text"` → `<input type="text">`
- `type: "secret"` → `<input type="password">` with show/hide toggle
- `type: "file"` → file upload (stub for `.pem` etc.)

**Test Connection:**
1. SPA disables button + spinner.
2. POST `/datasource-drafts/{draftId}/test-connection` with `{credentials: {[key]: value}, attemptId}`.
3. Backend writes credential values to **Secrets Manager** under `msp-guardian/datasource-draft/{draftId}`; persists `secretArn` on draft.
4. `idempotencyKey = sha256(draftId + JSON.stringify(credentials))`. Redis hit returns cached result.
5. Lambda `testDatasourceConnection` (LocalStack): reads secret, executes blueprint `auth_steps`, calls vendor API, infers schema (`genson`), writes sample to `s3://{S3_BUCKET}/{S3_TMP_PREFIX}/{draftId}/{attemptId}/sample.json`. Returns `fields`, `sampleRows` (first 5), `schemaHash`, `recordCount`, `columnCount`, `connectionTimeMs`.
6. Backend caches in Redis `datasource:schema-preview:{draftId}` TTL 30 min.
7. SPA shows green card: "**{vendorName} connected.** {tenantInfo if applicable}. **{recordCount} records, {columnCount} columns** (detected in {connectionTimeMs}ms)".

**Credential values NEVER stored in useWizardStore** — live only in StepAuthentication local `useState`; only `secretArn` is persisted.

### Step 3 — Map Fields

1. SPA `GET /datasource-drafts/{draftId}/schema-preview` → `{fields, schemaHash, sampleRows[], recordCount, columnCount}`.
2. **Render `SampleRowsPreview`** above mapping table — sticky table showing up to 5 sample records (real API data). Horizontal scroll for wide schemas. Subdued styling (smaller font, muted background).
3. **Default mappings pre-filled from blueprint** `default_field_mappings` (blueprint's `schema_fields[].key` → raw API field path). User may override any dropdown.
4. Below preview: standard fields table for category. Columns: Standard Field | Source Column dropdown | Status icon (✓/required/optional).
5. As user picks a source column, **highlight that column header** in the preview table.
6. **Additional Parameters (optional)** section below mapping table — collapsible; allows adding `{key, value}` pairs for vendor-specific config (passed through to Lambda).
7. For MSP-level blueprints: red box "**Client Identifier Column ***" — user must pick which source column identifies the client.
8. For CLIENT_SPECIFIC blueprints: green box "Client-specific source — data isolation handled via dedicated credentials. No client identifier column needed."
9. Required fields must be mapped before Continue is enabled.

### Step 4 — Schedule & Activate

`frequency` (MANUAL/DAILY/WEEKLY/MONTHLY), `timeOfDay` (HH:MM 24h), `timezone` (default `America/New_York`), `isEnabled`.

**Activation summary card** shown above the form: Client: {clientName}, Blueprint: {displayName}, Category: {category}, Records detected: {recordCount}, Fields mapped: {mappedCount}.

**Activate → POST `/datasources/activate`** → 202 → full-page "Activating…" overlay with spinner → poll `GET /datasources/{id}` every 2 s → ACTIVE: navigate `/datasources` + success toast "**{displayName}** connected for **{clientName}**." + auto-create assignment linking datasource to client. DEGRADED: error toast + "See Job Runs".

**Auto-assignment on activation:** When a datasource is activated with a `clientId`, backend automatically creates a `client_datasource_assignments` row (status=ACTIVE) for that client–datasource pair. No manual assignment step needed.

**Phase 1 — Synchronous (Postgres transaction, returns 202):**
1. Validate: schema preview in Redis; `schemaHash` matches; required mappings present; category∈{LICENSING,ENDPOINT} else 501.
2. BEGIN.
3. Insert `datasources` (status=`ACTIVATING`, `client_id`, `blueprint_id`, `secret_arn`).
4. Insert `datasource_schedules`.
5. Insert `client_datasource_assignments` (if `client_id` present, status=ACTIVE).
6. Insert `job_runs` (job_type=`ACTIVATION`, status=`RUNNING`, started_at=now()).
7. Mark draft `status='ACTIVATED'`.
8. COMMIT. Return `202 {datasourceId, status:'ACTIVATING'}`.

**Phase 2 — Background (same as v4):**
1. DynamoDB PutItem mapping document.
2. Fetch full data + write to S3 landing zone.
3. Ensure Glue DB exists; create Glue Catalog table.
4. Update `datasources` → `status='ACTIVE'`, `landing_path`, `glue_table_name`.
5. Update `job_runs` → `status='SUCCESS'`.

**On Phase 2 failure:** datasources `status='DEGRADED'`, job_runs `status='FAILED'`.

---

## 11. Standard Schemas, Transforms, Mapping Document

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
  "datasourceId":"<uuid>","mspId":"<uuid>","clientId":"<uuid>",
  "blueprintId":"datto_rmm",
  "category":"ENDPOINT","standardSchema":"endpoint_device_v1",
  "mappingVersion":1,"status":"ACTIVE","schemaHash":"<sha256 hex>",
  "fields":[
    {"standardField":"device_hostname","sourceField":"hostname","required":true,
     "dataType":"string","transform":"lowercase_trim"}
  ],
  "additionalParams":[],
  "postProcessing":{"explodeArrays":[],"deduplicateBy":["device_hostname"]},
  "createdAt":"<ISO>","createdBy":"<userId>"
}
```

---

## 12. Frontend Specifications

### Tailwind palette
```
bg:#0F1117, surface:#181B23, surface2:#121520, border:#2A2E3B,
text:#E8E9ED, muted:#8B8FA3, dim:#5C6078,
accent:#3B82F6, green:#22C55E, amber:#F59E0B, red:#EF4444,
licensing:#818CF8, endpoint:#34D399, recon:#FB923C
```
Font: `'DM Sans', system-ui, sans-serif`; mono: `'JetBrains Mono'`.

### Routes (v7.1)
```
/login                  (public)
/dashboard              (protected, default)
/clients                (protected — read any)
/clients/:id            (protected — read any)
/datasources            (protected — read any)
/datasources/add        (protected — MSP_ADMIN only; analyst → /forbidden)
/reports                (protected — read+generate any)
/reports/:id            (protected — read any)
/job-runs               (protected — read any)
/settings               (protected — read-only stub)
/forbidden              (protected)
```

Note: `/client-source-mapping` **removed** in v7.1. Assignment management lives in `/clients/:id` (Client Detail page).

### Notification & Toast System (v7.1 NEW)

`useUiStore` manages a toast queue. `ToastContainer` renders fixed bottom-right. Toasts: `{id, type:'success'|'error'|'info'|'warning', message, duration:4000}`. Auto-dismiss after `duration`ms.

**Trigger toast messages on:**
- Datasource saved as draft → info "Datasource saved as draft"
- Test Connection success → (inline card, not toast)
- Activation complete → success "{displayName} connected for {clientName}"
- Datasource inactivated → success "Datasource deactivated"
- Client added → success "Client {name} created"
- Assignment inactivated → success "Assignment removed"
- Billing/anchor changed → success "{type} updated"
- Report queued → info "Report queued — you'll be notified when ready"
- Retry job → success "Retry successful" | error "Retry failed"
- Logout → (redirect, no toast)

**NotificationBell** in AppShell header — shows count of recent notifications (from toast history stored in `useUiStore`). Clicking opens a dropdown of last 10 notifications.

### Confirmation Modals (v7.1 NEW)

Generic `ConfirmModal` with `{title, message, confirmLabel, cancelLabel, variant:'danger'|'default', onConfirm, onCancel}`.

Required confirmation modals:
- **Deactivate datasource:** "Deactivate datasource?" / "Scheduled runs will stop. Historical data retained. You can reactivate later." / "Deactivate" (red)
- **Change billing source:** "Change billing source?" / "This affects future reports. Historical reports won't change." / "Set as Billing Source"
- **Change identity anchor:** "Change identity anchor?" / "This affects how clients are matched in reports." / "Set as Identity Anchor"
- **Sign out:** "Sign out?" / "Are you sure you want to sign out?" / "Sign Out" (red)
- **Inactivate assignment:** "Remove assignment?" / "Datasource will be unlinked from this client. Historical reports retain the link." / "Remove"

### Zustand stores (v7.1)
```
useAuthStore:
  state: {accessToken,refreshToken,user:{id,email,fullName,role},mspId,isAuthenticated,rememberMe}
  actions: setAuth, clear, updateAccessToken, setRememberMe
  middleware: persist (refreshToken + user + rememberMe; never accessToken)

useWizardStore:
  state: {draftId, attemptId, step,
          clientTemplate:{clientId,clientName,blueprintId,blueprintDisplayName,displayName,
                          credentialSchema,defaultFieldMappings,category,sourceType,scope},
          connectionResult:{secretArn,recordCount,columnCount,connectionTimeMs}|null,
          connectionTested:bool,
          schemaPreview:{fields,schemaHash,sampleRows,recordCount,columnCount}|null,
          mapping:{fieldMappings:[],additionalParams:[]},
          schedule:{frequency,timeOfDay,timezone,isEnabled}}
  actions: reset, setStep, setClientTemplate, setConnectionResult, setConnectionTested,
           setSchemaPreview, setMapping, setSchedule
  middleware: persist to sessionStorage
  -- Raw credential values NEVER stored here. Live only in StepAuthentication local useState.

useUiStore:
  state: {idleModalOpen, logoutConfirmOpen, sidebarCollapsed,
          toasts:[{id,type,message,duration}],
          notificationHistory:[{id,type,message,timestamp}],
          confirmModal:{open,title,message,confirmLabel,variant,onConfirm}|null}
  actions: setIdleModalOpen, setLogoutConfirmOpen, toggleSidebar,
           pushToast, dismissToast, clearToasts,
           openConfirm, closeConfirm
  middleware: none
```

### Pages (v7.1)

- **LoginPage** — email + password + Remember Me checkbox → 401 inline error → success → `/dashboard`. Footer: "Hosted by Fission Labs — Powered by AWS Cognito" (display only).
- **DashboardPage** — TanStack `/dashboard/summary` once. 4 stat cards, failed-runs alert (if non-empty), 3 quick actions (Generate Report, Add Datasource [admin], Add Client [admin]), Recent Activity table. Real-time data timestamp.
- **ClientsPage** — list + filter (Show All / Needs Setup) + Add Client (admin) → `AddClientModal` → POST → list refreshes → success toast. Row → `/clients/:id`.
- **ClientDetailPage** — header (client name, readiness badge), Details card (description, default identifier, billing source, identity anchor), Readiness Checklist (4 checks), Assigned Datasources table (per-assignment identifier, Make Billing Source, Make Identity Anchor, Edit Identifier, Remove buttons — admin only). **This page replaces the old Client Source Mapping page for assignment management.**
- **DatasourcesPage** — list (default ACTIVE+DEGRADED). **Client filter dropdown** (all or specific client — v7.1). Category/State filters. "Add Datasource" (admin) → `/datasources/add`. Per-row "Inactivate" button (admin) → `InactivateConfirmModal` (ConfirmModal variant danger). Status badge: Active (green), Degraded (amber), Inactive (muted), Draft (dim).
- **AddDatasourcePage** — admin only. 4-step blueprint-driven wizard. Step indicators: "Client & Template", "Authentication", "Map Fields", "Schedule & Activate". Activate → 202 → overlay → poll → ACTIVE: navigate `/datasources` + success toast. DEGRADED: error toast + "see Job Runs".
- **ReportsPage** — generation form: Client → Report Type → Period → `DatasourcePickerModal` (multi-select) → Generate (real-AWS Lambda) → poll → preview/download. Bottom: Recent Reports table with included datasource names.
- **ReportPreviewPage** — header, summary cards, exceptions panel, "Download XLSX".
- **JobRunsPage** — list with status filter chips. Per-row Retry button on FAILED runs.
- **SettingsPage** — Profile section (Name field, Email field, Timezone dropdown — IST, EST, UTC, etc.), Preferences section (Notifications toggle, Change Password form: Current / New / Confirm). No backend wiring except display.
- **ForbiddenPage** — "You don't have access. Contact your MSP admin." + back button.

---

## 13. AWS Integration via LocalStack

LocalStack Community in Docker. boto3 with env-driven endpoint URLs.

`infra/localstack/init/01-bootstrap.sh` on startup:
1. S3 bucket `msp-guardian-poc`.
2. Prefix structure: `tmp/, samples/, landing/, raw/, curated/, quarantine/, reports/, mappings/`.
3. DynamoDB `msp_guardian_mappings` (pk HASH, sk RANGE).
4. DynamoDB `connector_registry` (source_id HASH) → seed all 8 blueprints from JSON.
5. Glue DB `msp_guardian_poc`.
6. Package + deploy Lambda `testDatasourceConnection`.
7. Placeholder Secrets Manager secret.

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

| Service | LocalStack | Real AWS |
|---|---|---|
| Test-Connection Lambda | ✓ | – |
| Secrets Manager | ✓ | – |
| S3 (sample, landing, mappings) | ✓ | – |
| DynamoDB (mappings + connector_registry) | ✓ | – |
| Glue Catalog | ✓ | – |
| Report Generator Lambda | – | ✓ |
| Report output S3 + staging | – | ✓ |

---

## 14. Report Generator Lambda (real AWS)

`backend/lambdas/report_generator/handler.py`. Deploy once via `deploy.sh`. Python 3.12.

**Handler responsibilities:**
1. Validate payload.
2. For each source: read `sourceDataS3Uri`; filter by `clientIdentifierForSource`; apply mapping transforms; apply `postProcessing`.
3. Merge across sources (Endpoint → `device_hostname`; Licensing → `user_email`).
4. Compute exceptions (gap analysis per category).
5. Render XLSX (openpyxl): Sheet 1 Summary, Sheet 2 Detail, Sheet 3 Exceptions, Sheet 4 Audit.
6. PUT XLSX to `s3://{outputBucket}/{outputKeyPrefix}{reportId}.xlsx`.
7. Generate presigned GET URL and return.

---

## 15. Error Handling

| Case | HTTP | code |
|---|---|---|
| Invalid login | 401 | INVALID_CREDENTIALS |
| Missing/expired access token | 401 | TOKEN_EXPIRED |
| Invalid refresh token | 401 | INVALID_REFRESH_TOKEN |
| Role forbidden | 403 | ROLE_FORBIDDEN |
| Connector not found | 404 | CONNECTOR_NOT_FOUND |
| Vendor API timeout | 504 | UPSTREAM_TIMEOUT |
| Empty vendor response | 400 | EMPTY_RESPONSE |
| Vendor auth failure | 400 | VENDOR_AUTH_FAILED |
| Schema preview expired | 410 | PREVIEW_EXPIRED |
| Required mapping missing | 400 | REQUIRED_MAPPING_MISSING |
| schemaHash mismatch | 400 | SCHEMA_HASH_MISMATCH |
| Reconciliation / CSV activation | 501 | NOT_IMPLEMENTED |
| Client name conflict | 409 | CLIENT_NAME_TAKEN |
| Duplicate assignment | 409 | ALREADY_ASSIGNED |
| Wrong category for billing | 400 | INVALID_BILLING_SOURCE |
| Assignment inactive | 400 | ASSIGNMENT_INACTIVE |
| Invalid datasource selection (reports) | 400 | INVALID_DATASOURCE_SELECTION |
| Report readiness fail | 400 | READINESS_FAILED |
| Report Lambda timeout | 504 | REPORT_LAMBDA_TIMEOUT |
| Report Lambda error | 502 | REPORT_LAMBDA_ERROR |
| Secrets Manager error | 502 | SECRETS_MANAGER_ERROR |
| S3 error | 502 | S3_ERROR |
| DynamoDB error | 502 | DYNAMODB_ERROR |
| Glue error | 502 | GLUE_ERROR |
| Postgres failure (Phase 1) | 500 | ACTIVATION_FAILED |
| Background activation failure | datasource → DEGRADED | – |

---

## 16. Seed Data (`backend/app/seed.py`)

Idempotent. Runs on container start after migrations.

**MSP:** `name="MVP MSP"`, `email="ops@mvp.com"`.

**Users (2):**
- `testmsp@mvp.com` / `testmsp@123` — role `MSP_ADMIN`, full_name "Test MSP Admin"
- `analyst@mvp.com` / `analyst@123` — role `MSP_ANALYST`, full_name "Demo Analyst"

**Clients (4):**
- ERES Companies — `EMAIL_DOMAIN_CONTAINS=erescompanies.com`
- Scoop Ride — `EMAIL_DOMAIN_CONTAINS=scoopride.io`
- Pinnacle Legal — `EMAIL_DOMAIN_CONTAINS=pinnaclelegal.com`
- Harbor View Medical — `EMAIL_DOMAIN_CONTAINS=harborviewmed.org`

**Connector Blueprints (8) — seeded to DynamoDB `connector_registry`:**
- `microsoft_365` (Licensing, CLIENT_SPECIFIC, certificate auth)
- `proofpoint` (Licensing, CLIENT_SPECIFIC, bearer auth)
- `ironscales` (Licensing, CLIENT_SPECIFIC, api_key auth)
- `dropsuite` (Licensing, CLIENT_SPECIFIC, api_key auth)
- `datto_rmm` (Endpoint, CLIENT_SPECIFIC, token_chain auth)
- `sentinelone` (Endpoint, CLIENT_SPECIFIC, api_key auth)
- `autotask_billing` (Reconciliation, MSP_LEVEL, basic auth)
- `custom` (configurable, free-form fields)

**Datasources (8):**
- M365 Production (Licensing, Active, client_id=ERES, blueprint=microsoft_365)
- Proofpoint Core (Licensing, Active, client_id=ERES, blueprint=proofpoint)
- Ironscales (Licensing, Degraded — drives dashboard alert)
- DropSuite (Licensing, Active)
- Datto RMM (Endpoint, Active, client_id=ERES, blueprint=datto_rmm)
- SentinelOne (Endpoint, Active)
- Autotask Billing (Reconciliation, Active)
- ThreatLocker (Endpoint, Draft)

**Assignments (with per-source identifiers):** — same as v4, auto-created on activation.

**Job runs (7, last 48h):** 1 FAILED for Ironscales + 6 SUCCESS.

**Landing JSON files seeded to S3** (so reports work from day one).

---

## 17. Local Development Setup

### `docker-compose.yml`
```
services:
  postgres:    postgres:16-alpine — env DB=MSP_Guardian, port 5432
  redis:       redis:7-alpine, port 6379
  localstack:  localstack/localstack:3.x, port 4566
  backend:     build ./backend, port 8000
               cmd: alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --reload
  frontend:    build ./frontend, port 5173
               cmd: npm run dev -- --host
```

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
REFRESH_TOKEN_REMEMBER_ME_TTL_DAYS=30

# --- AWS / LocalStack ---
AWS_ENDPOINT_URL=http://localstack:4566
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# --- S3 ---
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
DYNAMODB_CONNECTOR_REGISTRY_TABLE=connector_registry
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

---

## 18. Tests (minimum)

- `test_auth.py` — login happy/wrong-password, rememberMe flag extends TTL, refresh, logout.
- `test_roles.py` — admin can write; analyst gets 403 on writes; analyst can generate reports.
- `test_clients.py` — create/dup/list/patch/delete; default identifier persisted.
- `test_connectors.py` — GET /connectors returns all 8 blueprints; GET /connectors/{id} returns credentialSchema.
- `test_assignments.py` — assign with identifier override; auto-assign on activation; inactivate/reactivate; one-billing-source index.
- `test_datasource_activation.py` — full blueprint-driven activation: POST /datasource-drafts with clientId+blueprintId, test-connection, activate → 202 ACTIVATING → ACTIVE polled, DDB item, Glue table, landing data.json, auto-assignment created.
- `test_soft_delete.py` — inactivate datasource cascades to assignments; historical report_runs still readable.
- `test_report_generation.py` — POST /reports/generate with explicit datasourceIds; XLSX in S3; included sources match selection.

---

## 19. README Requirements

1. **What this is** — POC of MSP Guardian, what the demo shows.
2. **Prerequisites** (Windows): Docker Desktop, Git, VS Code, AWS CLI v2, Node 20, Python 3.14.3.
3. **One-time AWS setup** — S3 bucket; IAM; Lambda; deploy via `deploy.sh`.
4. **Quick start (Docker)** — clone → `cp .env.example .env` → edit `AWS_REPORT_*` → `docker compose up --build` → http://localhost:5173 → login.
5. **Outside Docker** — backend venv + pip + alembic + uvicorn. Frontend npm install + dev. Postgres/Redis/LocalStack still in Docker.
6. **Demo script (10 minutes):**
   1. Login as admin (Remember Me checked).
   2. Dashboard — point out failed-run alert (Ironscales).
   3. Add Client → "Acme Corp".
   4. Add Datasource → Step 1: pick "Acme Corp", pick "Datto RMM" blueprint → Step 2: paste credentials → Test Connection → green card (record count + columns) → Step 3: sample rows preview, default mappings pre-filled, add optional param → Step 4: Daily 02:00 → Activate → overlay → ACTIVE toast.
   5. Open Clients → Acme Corp detail → assignment auto-created → set identity anchor.
   6. Reports → Acme → Endpoint → April 2026 → DatasourcePicker → Generate → preview → Download XLSX.
   7. Logout (confirmation modal). Login as analyst → no write buttons → analyst can generate reports.
7. **Architecture overview**.
8. **Project structure** tree.
9. **Environment variables** table.
10. **Known limitations**.
11. **Production migration path**.
12. **Troubleshooting**.

---

## 20. Acceptance Criteria — Self-check

1. File tree from §5 generated; no placeholder/empty files in critical paths.
2. `docker compose up` boots all services with no manual steps.
3. Migration creates tables in §6 against database literally `MSP_Guardian`; `datasource_drafts.client_id` and `datasource_drafts.blueprint_id` columns present.
4. DynamoDB `connector_registry` seeded with 8 blueprints on LocalStack bootstrap.
5. Seed inserts both `testmsp@mvp.com` (MSP_ADMIN) and `analyst@mvp.com` (MSP_ANALYST).
6. `/auth/login` with `rememberMe=true` returns refresh token with 30-day TTL.
7. `GET /connectors` returns array of blueprints with `credentialSchema` rendered per blueprint.
8. Wizard Step 1 renders client dropdown + blueprint dropdown populated from API.
9. Wizard Step 2 renders ONLY the credential fields defined in blueprint `credentialSchema` (not a generic auth-type dropdown).
10. Test Connection response includes `recordCount`, `columnCount`, `connectionTimeMs`; UI shows these.
11. Wizard Step 3 renders `SampleRowsPreview` above mapping table; blueprint default mappings pre-filled; Additional Parameters section present.
12. Activation auto-creates `client_datasource_assignments` row for the selected client.
13. Datasources list has a working client filter dropdown.
14. `/client-source-mapping` route does NOT exist. Assignment management is in `/clients/:id`.
15. Toast notifications fire on: activation complete, datasource inactivated, client added, report queued.
16. All confirmation dialogs use generic `ConfirmModal` component with correct title/message/label text.
17. Login page has "Remember Me" checkbox wired to `rememberMe` flag in auth store.
18. Settings page renders Name, Email, Timezone fields; Preferences section with Notifications toggle + Change Password form.
19. DynamoDB mapping item includes `clientId` and `blueprintId` fields.
20. Backend `require_role('MSP_ADMIN')` dependency rejects analyst with 403.
21. Reports page generation form includes `DatasourcePickerModal`; per-report `datasourceIds` honored end-to-end.
22. Report generation invokes real AWS Lambda; XLSX in real-AWS S3; presigned URL works.
23. `report_generator/handler.py` complete deployable artifact with `requirements.txt` and `deploy.sh`.
24. All S3 paths built from env-driven prefixes — none hardcoded.
25. No `console.log`, no `// TODO`, no dummy returns in auth/activation/report paths.
26. Python base image `python:3.14.3-slim` in `backend/Dockerfile`.

---

## 21. Constraints — DO NOT

- Cognito. EventBridge schedules. Store raw JWTs.
- Store API credentials in Postgres (only `secret_arn`).
- Store raw credential values in `useWizardStore`.
- Hard-delete a datasource with assignments or job_runs. Use inactivate.
- Hardcode S3 prefixes — always pull from env.
- Render a `/client-source-mapping` route — this page is removed.
- Use a generic auth-type dropdown in Step 2 — always render fields from blueprint `credentialSchema`.
- Class components in React. Hooks only.
- `any` in TypeScript except for genuinely unknown JSON.
- `from sqlalchemy.orm import sessionmaker` (sync). Use `async_sessionmaker`.
- `pydantic.BaseSettings` (v1). Use `pydantic_settings.BaseSettings`.
- React Context for app state — Zustand only.
- Call axios directly from a component — go through TanStack Query hook in `src/hooks/`.
- Ask follow-up questions. State assumptions in README and proceed.

---

## 22. Assumption Handling

If unclear, write the assumption as a single sentence in the README under "Assumptions made" and proceed. No TODOs. No stubs in critical paths.

---

**End of prompt. Begin generating.**
