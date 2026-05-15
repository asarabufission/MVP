# MSP Guardian POC — Project Memory (v7.1)

## Source of truth

The full specification lives in **`SPEC.md`** at the repo root. **Always read the relevant section of SPEC.md before starting a phase.** Do not work from memory of the spec.

## Project in one paragraph

Multi-tenant POC for MSPs (LeafTech). Admin logs in (Remember Me) → dashboard → adds Client → adds Endpoint datasource via a **4-step blueprint-driven wizard** (Step 1: pick client + connector blueprint → Step 2: blueprint-rendered credential form + Test Connection → Step 3: real sample data preview + pre-filled default mappings + optional params → Step 4: Schedule & Activate, auto-creates client assignment) → activates → views assignment in Client Detail → generates Endpoint Audit report → downloads XLSX. Two roles (MSP_ADMIN write, MSP_ANALYST read+report). Hybrid AWS — LocalStack for everything except the report Lambda which runs in real AWS. **Client Source Mapping page removed** — assignment management is in Client Detail (`/clients/:id`).

## What changed v4 → v7.1

| Area | V4 | V7.1 |
|------|-----|------|
| Datasource wizard Step 1 | Identify (freeform vendor/category/scope) | Client & Template (client dropdown + blueprint selector) |
| Datasource wizard Step 2 | Generic auth-type dropdown + generic fields | Blueprint-driven credential fields from `credentialSchema` |
| Wizard Step 3 | Generic sample rows | Real API sample data; blueprint default mappings pre-filled; Additional Parameters section |
| Client Source Mapping | Dedicated page + nav item | **Removed** — assignments live in Client Detail |
| Navigation | 7 items (includes Mapping) | 6 items (no Mapping) |
| Connector blueprints | None (freeform) | DynamoDB `connector_registry` — 8 blueprints |
| Notifications | None | Toast system + NotificationBell in header |
| Confirmation dialogs | Minimal | Full `ConfirmModal` for all destructive actions |
| Login | No Remember Me | Remember Me checkbox (extends refresh TTL to 30 days) |
| Datasources list | Category + State filters | + Client filter dropdown |
| Settings | Name + role display | Name + Email + Timezone + Change Password |
| Auto-assignment | Manual via Mapping page | Auto-created on activation with clientId |

## Phase pointers (which SPEC.md sections to read per phase)

| Phase | Read these sections | Output |
|---|---|---|
| 1 — Backend skeleton + DB + seed + docker + LocalStack | §3, §4, §5, §6, §7, §16, §17, §13 | `docker compose up` boots clean; connector_registry seeded with 8 blueprints |
| 2 — Auth + roles + login_history + idle + Remember Me | §8 (auth), §9, §12 (auth flow), §15 (errors), §18 (test_auth, test_roles) | Admin and analyst can log in; rememberMe extends TTL; admin endpoints reject analyst with 403 |
| 3 — Connectors API + Wizard backend (blueprint-driven drafts, test-connection Lambda, schema preview, activation Phase 1+2, auto-assignment) | §8 (connectors, wizard), §10, §11, §13, §18 (test_connectors, test_datasource_activation) | Full blueprint-driven wizard end-to-end via API; activation produces DDB+Glue+S3 artifacts + auto-assignment |
| 4 — Clients + Assignment APIs (per-source identifier, soft delete) | §6, §8 (clients, assignments), §15, §18 (test_clients, test_assignments, test_soft_delete) | Per-source identifier override + inactivate/reactivate working |
| 5 — Frontend skeleton + LoginPage (Remember Me) + RoleGuard + AppShell + Toast system + ConfirmModal | §4 (state mgmt), §12 (palette, routes, stores, notifications, modals), §9 | Login works; protected routes; role-aware sidebar; toast fires; confirm modal works |
| 6 — Frontend pages: Dashboard, Clients, ClientDetail (assignment management), Datasources (client filter), JobRuns, Settings | §12 | All read screens render; admin sees write buttons, analyst does not; no /client-source-mapping route |
| 7 — Wizard frontend (Steps 1-4: ClientTemplate, Authentication, MapFields with SampleRowsPreview + AdditionalParams, ScheduleActivate) | §10, §12 (AddDatasourcePage) | Activate UI shows overlay + polling → success/degraded toast; auto-assignment visible in ClientDetail |
| 8 — Reports backend + frontend + real AWS Lambda | §8 (reports), §12 (report flow), §14, §15, §18 (test_report_generation) | Generate → real AWS Lambda → XLSX download works end to end |
| 9 — README + polish | §19, §20 (acceptance), §21 (constraints) | All 26 acceptance items pass |

## Hard conventions (never violate)

- **Python 3.14.3**, FastAPI 0.115+ async, SQLAlchemy 2.x async + asyncpg, Pydantic v2, Alembic async.
- **Postgres database name is exactly `MSP_Guardian`** (case-sensitive, with underscore).
- **Frontend:** Vite 5 + React 18 + TypeScript strict + Tailwind + TanStack Query v5 + **Zustand 5** + React Hook Form + Zod.
- **State discipline:** server data through TanStack Query hooks in `src/hooks/`; client state through Zustand. Never call axios from a component. Raw credentials NEVER in useWizardStore.
- **AWS hybrid:** LocalStack for everything except report generation. Report Lambda runs in real AWS.
- **All S3 paths from env vars** — never hardcoded.
- **Soft delete only.** Datasources and assignments use `status='INACTIVE'`.
- **No /client-source-mapping route** — removed in v7.1. Client Detail page handles assignments.
- **Wizard Step 2 credential fields come from blueprint `credentialSchema`** — no generic auth-type dropdown.
- **Auto-assignment on activation** — when `clientId` is present in datasource draft, activation auto-creates `client_datasource_assignments` row.
- **Toast notifications** for all key events. **ConfirmModal** for all destructive actions.
- **Two roles only:** `MSP_ADMIN` and `MSP_ANALYST`. Backend `require_role('MSP_ADMIN')` on all writes.
- **Idle timeout 1 minute** (intentional for demo).
- **Two DynamoDB tables:** `msp_guardian_mappings` (field mappings) and `connector_registry` (blueprints).

## Working agreement

- Use **plan mode** (Shift+Tab twice) before any change touching > 3 files.
- **Run code after every phase** — `docker compose up`, `pytest`, exercise the UI.
- **Commit after each successful phase** with descriptive message.
- `/clear` between phases to keep context fresh.
- When unsure, **re-read the relevant SPEC.md section**. Do not invent.
- For each phase, ask Claude to **read only the listed SPEC.md sections** and propose a plan before generating code.

## Phase tracker

- [ ] Day 0 — Setup
- [ ] Phase 1 — Backend skeleton + Connector registry seeding
- [ ] Phase 2 — Auth + roles + Remember Me
- [ ] Phase 3 — Connectors API + Blueprint-driven wizard backend
- [ ] Phase 4 — Clients + Assignments
- [ ] Phase 5 — Frontend skeleton + Toast + ConfirmModal
- [ ] Phase 6 — Frontend pages (no mapping page; ClientDetail has assignments)
- [ ] Phase 7 — Blueprint-driven wizard frontend
- [ ] Phase 8 — Reports + real AWS Lambda
- [ ] Phase 9 — README + polish

## Lessons learned

(Append discovered facts here as the build progresses — library quirks, env-specific issues, debugging tips.)

## Key file locations

- Connector blueprint schemas: `connector_registry_schemas.json` (outputs folder — seed to DynamoDB)
- Pipeline config schema: `pipeline_config_schema.json` (outputs folder — reference for ETL engineer)
- Microsoft 365 connector v2: `Microsoft_Licensing_connector_v2.json` (outputs folder — includes foreach/licenseDetails)
- Master guide: `MSP_Guardian_Master_Guide.txt` (outputs folder)
