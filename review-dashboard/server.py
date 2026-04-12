"""
Kyle Review Dashboard - Backend Server
Scans the Product Catalog folder, reads YAML frontmatter from .md files,
and provides API endpoints for approve/revision actions.
"""

import os
import re
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import frontmatter
import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CATALOG_ROOT = Path(
    os.environ.get(
        "CATALOG_ROOT",
        r"C:\Users\banfi\Projects\Sidebar Code\Side Bar Code\Product Catalog",
    )
)

NOTIFICATION_LOG = Path(__file__).parent / "notifications.log"

app = FastAPI(title="Kyle Review Dashboard")
logger = logging.getLogger("review-dashboard")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ApproveRequest(BaseModel):
    file_path: str  # relative to CATALOG_ROOT


class RevisionRequest(BaseModel):
    file_path: str
    notes: str


class FileInfo(BaseModel):
    relative_path: str
    file_name: str
    tier: str
    category: str
    review_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    revision_notes: Optional[str] = None
    flagged: bool = False
    flagged_reason: Optional[str] = None
    last_modified: str
    title: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Map folder segments to human-readable tier names
TIER_NAMES = {
    "01_parser_trial": "Parser Trial ($197)",
    "02_full_litigation_suite": "Full Litigation Suite ($2,997)",
    "01_foundation": "Foundation Consulting ($5K-$7.5K)",
    "02_implementation": "Implementation Consulting ($10K-$15K)",
    "03_modernization": "Modernization Consulting ($25K-$40K)",
    "01_single_workflow": "Single Workflow ($5K)",
    "02_multi_agent": "Multi-Agent System ($10K)",
    "03_practice_area": "Practice Area Suite ($15K-$25K)",
}


def classify_category(rel_path: str) -> str:
    """Derive category from folder path."""
    lower = rel_path.lower()
    if "_sales_packet" in lower:
        return "sales_packet"
    if "_customer_deliverables" in lower:
        return "deliverable"
    if "intake_and_contracting" in lower or "engagement_letter" in lower:
        return "legal_instrument"
    if "_internal" in lower:
        return "internal"
    return "other"


def derive_tier(rel_path: str) -> str:
    """Extract human-readable tier name from relative path."""
    parts = Path(rel_path).parts
    for part in parts:
        if part in TIER_NAMES:
            return TIER_NAMES[part]
    return "General"


def parse_md_file(full_path: Path, rel_path: str) -> Optional[FileInfo]:
    """Read a .md file and extract frontmatter into a FileInfo."""
    try:
        post = frontmatter.load(str(full_path))
    except Exception:
        return None

    meta = post.metadata
    if not meta:
        return None

    stat = full_path.stat()
    last_mod = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M"
    )

    return FileInfo(
        relative_path=rel_path.replace("\\", "/"),
        file_name=full_path.name,
        tier=derive_tier(rel_path),
        category=classify_category(rel_path),
        review_status=str(meta.get("review_status", "draft")),
        reviewed_by=meta.get("reviewed_by"),
        reviewed_at=str(meta["reviewed_at"]) if meta.get("reviewed_at") else None,
        revision_notes=meta.get("revision_notes"),
        flagged=bool(meta.get("flagged", False)),
        flagged_reason=meta.get("flagged_reason"),
        last_modified=last_mod,
        title=meta.get("title", full_path.stem.replace("_", " ").title()),
    )


def scan_catalog() -> list[FileInfo]:
    """Walk the catalog root and collect all .md files with frontmatter."""
    results = []
    for root, _dirs, files in os.walk(CATALOG_ROOT):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            full = Path(root) / fname
            rel = str(full.relative_to(CATALOG_ROOT))
            info = parse_md_file(full, rel)
            if info:
                results.append(info)
    return results


def update_frontmatter(rel_path: str, updates: dict) -> None:
    """Modify YAML frontmatter fields in a file on disk."""
    full_path = CATALOG_ROOT / rel_path.replace("/", os.sep)
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")

    post = frontmatter.load(str(full_path))
    for key, value in updates.items():
        post.metadata[key] = value

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))


def log_notification(file_path: str, reason: str) -> None:
    """Append a flagged-item notification to the log file."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{ts}] FLAGGED: {file_path} | Reason: {reason} | Notify: kyle@sidebarcode.com\n"
    with open(NOTIFICATION_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info("Notification logged: %s - %s", file_path, reason)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/files")
def list_files(
    tier: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
) -> list[FileInfo]:
    """Return all catalog files, optionally filtered."""
    items = scan_catalog()
    if tier:
        items = [i for i in items if tier.lower() in i.tier.lower()]
    if category:
        items = [i for i in items if i.category == category]
    return items


@app.post("/api/approve")
def approve_file(req: ApproveRequest) -> dict:
    """Mark a file as kyle_approved."""
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    update_frontmatter(
        req.file_path,
        {
            "review_status": "kyle_approved",
            "reviewed_by": "kyle",
            "reviewed_at": today,
        },
    )
    return {"status": "approved", "file": req.file_path}


@app.post("/api/revision")
def request_revision(req: RevisionRequest) -> dict:
    """Mark a file as revision_requested with notes."""
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    update_frontmatter(
        req.file_path,
        {
            "review_status": "revision_requested",
            "reviewed_by": "kyle",
            "reviewed_at": today,
            "revision_notes": req.notes,
        },
    )
    return {"status": "revision_requested", "file": req.file_path}


@app.post("/api/flag")
def flag_file(req: ApproveRequest) -> dict:
    """Log a notification for a flagged file (called on scan if new flags found)."""
    items = scan_catalog()
    for item in items:
        if item.relative_path == req.file_path and item.flagged:
            log_notification(item.relative_path, item.flagged_reason or "UNKNOWN")
            return {"status": "notification_logged", "file": req.file_path}
    raise HTTPException(status_code=404, detail="File not found or not flagged")


@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serve the single-page dashboard HTML."""
    html_path = Path(__file__).parent / "dashboard.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5190)
