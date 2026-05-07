# MSP Guardian POC

Phase 1 scaffold. See `SPEC.md` for the full specification.

## Quickstart

### Local development (LocalStack)

```
make local
```

Brings up `postgres`, `redis`, `localstack`, `backend` (with `--reload`), and `frontend`. Uses `.env.local` and stub AWS credentials for LocalStack-emulated services.

- Backend: http://localhost:8000 (`/health`, `/docs`)
- Frontend: http://localhost:5173
- LocalStack: http://localhost:4566

If you also need to invoke the real-AWS Report Generator Lambda from your laptop, run `aws sso login --profile msp-dev` once per workday. The local override mounts `~/.aws/` into the backend container so boto3's default credential chain finds the SSO cache and refreshes automatically.

### EC2 deployment (Instance Role)

```
make ec2
```

Brings up the same stack **without LocalStack**, using `.env.ec2`. AWS credentials come from the attached EC2 Instance Role via IMDSv2 — no keys in env, no rotation work. Boto3 refreshes them transparently.

The instance role must have these permissions:
- `s3:*` on the report bucket and `msp-guardian-poc`
- `dynamodb:*` on `msp_guardian_mappings`
- `glue:*` on the `msp_guardian_poc` database
- `secretsmanager:GetSecretValue` on `msp-guardian/*`
- `lambda:InvokeFunction` on `msp-guardian-report-generator`

### Other targets

```
make stop          # docker compose down
make logs          # tail backend logs
make reset-local   # docker compose down -v, then make local
```

## Why two `.env` files?

`.env.local` and `.env.ec2` are committed (no real secrets in either). The `Makefile` selects which one Docker Compose reads via `--env-file`, so there's no stateful `.env` to clobber when switching modes. Replace `<set-on-instance>` placeholders in `.env.ec2` during deploy.
