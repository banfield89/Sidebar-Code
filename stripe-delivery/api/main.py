"""FastAPI application entrypoint — wires routes and startup for the SP2 service."""

from __future__ import annotations

import os
import secrets
import subprocess
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI(
    title="Sidebar Code SP2 API",
    description="Checkout, webhook, and delivery service for sidebarcode.com",
    version="0.1.0",
)


def _resolve_git_sha() -> str:
    """Return the short git sha for the running build.

    Order of resolution:
      1. `GIT_COMMIT` env var (Render injects this on deploy).
      2. `RENDER_GIT_COMMIT` env var (Render's native name).
      3. Fall back to `git rev-parse --short HEAD` for local dev.
      4. Return 'unknown' if none of the above work.
    """
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
    """Return the deployment environment name."""
    return os.getenv("SIDEBARCODE_ENV", "development")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe consumed by Render's healthCheckPath."""
    return {
        "status": "ok",
        "version": _resolve_git_sha(),
        "env": _resolve_env(),
    }


@app.post("/api/checkout")
def create_checkout() -> JSONResponse:
    """Stub — wired in Session 4. Returns 501 until then."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={"detail": "checkout not yet implemented (Session 4)"},
    )


@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> JSONResponse:
    """Stub — wired in Session 4. Returns 501 until then."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={"detail": "session read not yet implemented (Session 4)"},
    )


@app.post("/api/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Stub — wired in Session 5. Returns 501 until then."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={"detail": "webhook not yet implemented (Session 5)"},
    )


# Admin dashboard basic auth.
# Fails closed if env vars are unset (parked default from Session 1).
_basic_auth = HTTPBasic()


def _require_admin(
    credentials: Annotated[HTTPBasicCredentials, Depends(_basic_auth)],
) -> str:
    expected_user = os.getenv("ADMIN_USER")
    expected_password = os.getenv("ADMIN_PASSWORD")
    if not expected_user or not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin dashboard not configured",
        )
    user_ok = secrets.compare_digest(credentials.username, expected_user)
    pass_ok = secrets.compare_digest(credentials.password, expected_password)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/admin/dashboard")
def admin_dashboard(
    user: Annotated[str, Depends(_require_admin)],
) -> dict[str, str]:
    """Stub — wired in Session 8. Returns a placeholder for now."""
    return {"status": "ok", "user": user, "detail": "dashboard stub (Session 8)"}
