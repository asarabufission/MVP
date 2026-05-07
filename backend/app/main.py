from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    auth,
    client_assignments,
    clients,
    dashboard,
    datasource_drafts,
    datasources,
    job_runs,
    reports,
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="MSP Guardian POC", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


api_prefix = "/api/v1"
app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["auth"])
app.include_router(dashboard.router, prefix=f"{api_prefix}/dashboard", tags=["dashboard"])
app.include_router(clients.router, prefix=f"{api_prefix}/clients", tags=["clients"])
app.include_router(
    client_assignments.router,
    prefix=f"{api_prefix}/client-assignments",
    tags=["client-assignments"],
)
app.include_router(
    datasource_drafts.router,
    prefix=f"{api_prefix}/datasource-drafts",
    tags=["datasource-drafts"],
)
app.include_router(datasources.router, prefix=f"{api_prefix}/datasources", tags=["datasources"])
app.include_router(job_runs.router, prefix=f"{api_prefix}/job-runs", tags=["job-runs"])
app.include_router(reports.router, prefix=f"{api_prefix}/reports", tags=["reports"])
