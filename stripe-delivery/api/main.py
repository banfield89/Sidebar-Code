"""FastAPI application entrypoint — wires routes and startup for the SP2 service."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi import FastAPI

from api.admin import router as admin_router
from api.checkout import router as checkout_router
from api.webhook import router as webhook_router

app = FastAPI(
    title="Sidebar Code SP2 API",
    description="Checkout, webhook, and delivery service for sidebarcode.com",
    version="0.1.0",
)
app.include_router(checkout_router)
app.include_router(webhook_router)
app.include_router(admin_router)


def _resolve_git_sha() -> str:
    """Return the short git sha for the running build."""
    for var in ("GIT_COMMIT", "RENDER_GIT_COMMIT"):
        value = os.getenv(var)
        if value:
            return value[:7]
    try:
        repo_root = Path(__file__).resolve().parent.parent.parent
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def _resolve_env() -> str:
    return os.getenv("SIDEBARCODE_ENV", "development")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe consumed by Render's healthCheckPath."""
    return {
        "status": "ok",
        "version": _resolve_git_sha(),
        "env": _resolve_env(),
    }
