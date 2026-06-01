"""CLI entry point for local testing.

Usage:
    python run.py <source_id> [--client-id CID] [--dry-run] [--no-land]

Credentials are read from the env var <SOURCE_ID>_CREDENTIALS as a JSON object,
e.g. AUTOTASK_V1_CREDENTIALS='{"AUTOTASK_USERNAME": "...", ...}'.
Real runs require AWS credentials (for S3 landing) on the default boto3 chain.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from orchestrator import run_connector


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a manifest-driven connector.")
    parser.add_argument("source_id", help="Manifest source_id, e.g. autotask_v1")
    parser.add_argument("--client-id", default=None, help="Client id for landing path")
    parser.add_argument("--dry-run", action="store_true", help="Foreach first 3 items; skip landing")
    parser.add_argument("--no-land", action="store_true", help="Run steps but do not write to S3")
    args = parser.parse_args(argv)

    env_key = f"{args.source_id.upper()}_CREDENTIALS"
    raw = os.environ.get(env_key)
    if not raw:
        print(f"Set {env_key} to a JSON object of credentials.", file=sys.stderr)
        return 2
    credentials = json.loads(raw)

    outputs = run_connector(
        args.source_id,
        credentials,
        client_id=args.client_id,
        dry_run=args.dry_run,
        land_results=False if args.no_land else None,
    )
    for step_id, rows in outputs.items():
        print(f"{step_id}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
