# MSP Guardian POC — Project Memory

## Source of truth

The full specification lives in **`SPEC.md`** at the repo root. **Always read the relevant section of SPEC.md before starting a phase.** Do not work from memory of the spec.

## Project in one paragraph

Multi-tenant POC for MSPs (LeafTech). Admin logs in → dashboard → adds Client → adds Endpoint datasource via 4-step wizard with sample data preview → activates → assigns datasource to client with per-source identifier → generates Endpoint Audit report → downloads XLSX. Two roles (MSP_ADMIN write, MSP_ANALYST read+report). Hybrid AWS — LocalStack for everything except the report Lambda which runs in real AWS.

## Phase pointers (which SPEC.md sections to read per phase)

| Phase | Read these sections | Output |
|---|---|---|
| 1 — Backend skeleton + DB + seed + docker + LocalStack | §3, §4, §5, §6, §14, §15, §12 | `docker compose up` boots clean, schema migrated, both users seeded |
| 2 — Auth + roles + login_history + idle | §7 (auth), §8, §11 (auth flow), §13 (errors), §16 (test_auth, test_roles) | Admin and analyst can log in; admin endpoints reject analyst with 403 |
| 3 — Wizard backend (drafts, test-connection Lambda, schema preview with sample rows, activation Phase 1+2) | §7 (wizard), §9, §10, §12, §13, §16 (test_datasource_activation) | Wizard end-to-end via API; activation produces DDB+Glue+S3 artifacts |
| 4 — Clients + Client Source Mapping APIs (per-source identifier, soft delete) | §6, §7 (clients, mapping), §13, §16 (test_clients, test_assignments, test_soft_delete) | Per-source identifier override + inactivate/reactivate working |
| 5 — Frontend skeleton + LoginPage + RoleGuard + AppShell | §4 (state mgmt), §11 (palette, routes, stores), §8 | Login works; protected routes; role-aware sidebar |
| 6 — Frontend pages: Dashboard, Clients, ClientDetail, Datasources, ClientSourceMapping (v4 layout) | §11 | All read screens render; admin sees write buttons, analyst does not |
| 7 — Wizard frontend (Steps 1–4 with SampleRowsPreview) | §9, §11 (AddDatasourcePage), §10 | Activate UI shows overlay + polling → success/degraded toast |
| 8 — Reports backend + frontend + real AWS Lambda | §7 (reports), §11 (report flow), §12.5, §13, §16 (test_report_generation) | Generate → real AWS Lambda → XLSX download works end to end |
| 9 — README + polish | §17, §18 (acceptance), §20 (constraints) | Junior-dev runnable on Windows; all 25 acceptance items pass |

## Hard conventions (never violate)

- **Python 3.14.3**, FastAPI 0.115+ async, SQLAlchemy 2.x async + asyncpg, Pydantic v2, Alembic async.
- **Postgres database name is exactly `MSP_Guardian`** (case-sensitive, with underscore).
- **Frontend:** Vite 5 + React 18 + TypeScript strict + Tailwind + TanStack Query v5 + **Zustand 5** (NOT React Context for app state) + React Hook Form + Zod.
- **State discipline:** server data through TanStack Query hooks in `src/hooks/`; client state through Zustand stores `useAuthStore` / `useWizardStore` / `useUiStore`. Never call axios from a component.
- **AWS hybrid:** LocalStack for everything except report generation. Report Lambda runs in real AWS. Two separate `boto3` clients in `aws_clients.py`.
- **All S3 paths from env vars** (`S3_BUCKET`, `S3_LANDING_PREFIX`, etc.) — never hardcoded.
- **Soft delete only.** Datasources and assignments use `status='INACTIVE'`. Hard delete is forbidden.
- **Per-source client identifier** lives on `client_datasource_assignments`, not on `clients`. Clients have a `default_identifier_*` fallback.
- **Two roles only:** `MSP_ADMIN` and `MSP_ANALYST`. Backend uses `require_role('MSP_ADMIN')` dependency on writes.
- **Idle timeout 1 minute** (intentional for demo).

## Working agreement

- Use **plan mode** (Shift+Tab twice) before any change touching > 3 files.
- **Run code after every phase** — `docker compose up`, `pytest`, exercise the UI.
- **Commit after each successful phase** with descriptive message.
- `/clear` between phases to keep context fresh.
- When unsure, **re-read the relevant SPEC.md section**. Do not invent.
- For each phase, ask Claude to **read only the listed SPEC.md sections** (table above) and propose a plan before generating code.

## Phase tracker

- [ ] Day 0 — Setup
- [ ] Phase 1 — Backend skeleton
- [ ] Phase 2 — Auth + roles
- [ ] Phase 3 — Wizard backend
- [ ] Phase 4 — Clients + assignments
- [ ] Phase 5 — Frontend skeleton
- [ ] Phase 6 — Frontend pages
- [ ] Phase 7 — Wizard frontend
- [ ] Phase 8 — Reports + real AWS Lambda
- [ ] Phase 9 — README + polish

## Lessons learned

(Append discovered facts here as the build progresses — library quirks, env-specific issues, debugging tips.)
