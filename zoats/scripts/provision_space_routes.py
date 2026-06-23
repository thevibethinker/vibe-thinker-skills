#!/usr/bin/env python3
"""Provision ZoATS zo.space routes via Zo API.

Reads route source files from space-routes/ and deploys them.

Usage:
    python3 scripts/provision_space_routes.py              # deploy all routes
    python3 scripts/provision_space_routes.py --dry-run    # preview
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lib.paths import ZOATS_HOME

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SPACE_ROUTES_DIR = ZOATS_HOME / "space-routes"
MANIFEST_PATH = SPACE_ROUTES_DIR / "manifest.json"
ZO_ASK_TIMEOUT_SECONDS = int(os.environ.get("ZOATS_ZO_ASK_TIMEOUT_SECONDS", "240"))
ZO_ASK_MAX_ATTEMPTS = int(os.environ.get("ZOATS_ZO_ASK_MAX_ATTEMPTS", "2"))


def load_manifest():
    if not MANIFEST_PATH.exists():
        logger.error(f"Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)
    return json.loads(MANIFEST_PATH.read_text())


def get_zo_api_base():
    """Resolve Zo API base URL."""
    return os.environ.get("ZO_API_BASE", "https://api.zo.computer")


def get_zo_api_key():
    key = os.environ.get("ZO_API_KEY", "") or os.environ.get("ZO_CLIENT_IDENTITY_TOKEN", "")
    if not key:
        logger.error("ZO_API_KEY not set. Set it in your environment to deploy routes.")
        logger.error("  export ZO_API_KEY=zo_sk_...")
        sys.exit(1)
    return key


def get_model_name() -> str:
    return os.environ.get("ZOATS_PROVISION_MODEL", "openai:gpt-5.2-2025-12-11")


def build_auth_header(token: str) -> str:
    if token.lower().startswith("bearer "):
        return token
    if token.startswith("zo_"):
        return f"Bearer {token}"
    return token


def deploy_route(api_base: str, api_key: str, path: str, route_type: str, code: str, public: bool) -> dict:
    """Deploy a single route via Zo API."""
    import urllib.request
    import urllib.error

    url = f"{api_base}/v1/space/routes"
    payload = json.dumps({
        "path": path,
        "route_type": route_type,
        "code": code,
        "public": public,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": build_auth_header(api_key),
            "Content-Type": "application/json",
        },
        method="PUT",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
            return {"success": True, "status": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"success": False, "status": e.code, "error": body}
    except Exception as e:
        return {"success": False, "error": str(e)}


def deploy_route_via_zo_ask(api_base: str, api_key: str, path: str, route_type: str, code: str, public: bool) -> dict:
    """Fallback deploy using the documented /zo/ask API."""
    import urllib.request
    import urllib.error

    url = f"{api_base}/zo/ask"
    output_format = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "path": {"type": "string"},
            "message": {"type": "string"},
        },
        "required": ["success", "path", "message"],
    }

    public_clause = (
        f'Set public to {"true" if public else "false"}.'
        if route_type == "page"
        else "API routes are always public."
    )
    prompt = (
        "Create or update exactly one zo.space route using the update_space_route tool.\n"
        f"Path: {path}\n"
        f"Route type: {route_type}\n"
        f"{public_clause}\n"
        "Use the code below exactly as provided. Do not modify it. Do not make any other changes.\n\n"
        f"```tsx\n{code}\n```\n\n"
        'After the tool call, respond with JSON matching the required schema with success=true if the route synced.'
    )
    payload = json.dumps({
        "input": prompt,
        "model_name": get_model_name(),
        "output_format": output_format,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": build_auth_header(api_key),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    last_error = None
    for attempt in range(1, ZO_ASK_MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=ZO_ASK_TIMEOUT_SECONDS) as resp:
                body = json.loads(resp.read().decode())
                output = body.get("output", {})
                return {
                    "success": bool(output.get("success")),
                    "status": resp.status,
                    "body": output,
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            return {"success": False, "status": e.code, "error": body}
        except Exception as e:
            last_error = str(e)
            logger.warning(f"    /zo/ask deploy attempt {attempt}/{ZO_ASK_MAX_ATTEMPTS} failed for {path}: {last_error}")
            if attempt < ZO_ASK_MAX_ATTEMPTS:
                time.sleep(2)

    return {"success": False, "error": last_error or "unknown /zo/ask error"}


def delete_route(api_base: str, api_key: str, path: str) -> dict:
    """Delete a single route via Zo API."""
    import urllib.request
    import urllib.error

    url = f"{api_base}/v1/space/routes"
    payload = json.dumps({"path": path}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": build_auth_header(api_key),
            "Content-Type": "application/json",
        },
        method="DELETE",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
            return {"success": True, "status": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"success": False, "status": e.code, "error": body}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_route_via_zo_ask(api_base: str, api_key: str, path: str) -> dict:
    """Fallback delete using the documented /zo/ask API."""
    import urllib.request
    import urllib.error

    url = f"{api_base}/zo/ask"
    output_format = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "path": {"type": "string"},
            "message": {"type": "string"},
        },
        "required": ["success", "path", "message"],
    }
    prompt = (
        "Delete exactly one zo.space route using the delete_space_route tool.\n"
        f"Path: {path}\n"
        "Do not delete anything else.\n\n"
        'After the tool call, respond with JSON matching the required schema with success=true if the route was removed.'
    )
    payload = json.dumps({
        "input": prompt,
        "model_name": get_model_name(),
        "output_format": output_format,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": build_auth_header(api_key),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    last_error = None
    for attempt in range(1, ZO_ASK_MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=ZO_ASK_TIMEOUT_SECONDS) as resp:
                body = json.loads(resp.read().decode())
                output = body.get("output", {})
                return {
                    "success": bool(output.get("success")),
                    "status": resp.status,
                    "body": output,
                }
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            return {"success": False, "status": e.code, "error": body}
        except Exception as e:
            last_error = str(e)
            logger.warning(f"    /zo/ask delete attempt {attempt}/{ZO_ASK_MAX_ATTEMPTS} failed for {path}: {last_error}")
            if attempt < ZO_ASK_MAX_ATTEMPTS:
                time.sleep(2)

    return {"success": False, "error": last_error or "unknown /zo/ask error"}


def provision(dry_run: bool = False):
    manifest = load_manifest()
    logger.info(f"[provision] {len(manifest)} routes in manifest")

    if not dry_run:
        api_key = get_zo_api_key()
        api_base = get_zo_api_base()

    results = []
    for entry in manifest:
        src_file = SPACE_ROUTES_DIR / entry["file"]
        route_path = entry["path"]
        route_type = entry["type"]
        public = entry.get("public", True)

        if not src_file.exists():
            logger.error(f"  Source file missing: {src_file}")
            results.append({"path": route_path, "status": "error", "reason": "file_missing"})
            continue

        code = src_file.read_text()
        logger.info(f"  {route_path} ({route_type}) ← {entry['file']} ({len(code)} chars)")

        if dry_run:
            results.append({"path": route_path, "status": "dry_run"})
            continue

        result = deploy_route(api_base, api_key, route_path, route_type, code, public)
        if not result.get("success") and result.get("status") == 404:
            logger.warning(f"    Direct route API unavailable for {route_path}; retrying via /zo/ask")
            result = deploy_route_via_zo_ask(api_base, api_key, route_path, route_type, code, public)
        results.append({"path": route_path, **result})

        if result["success"]:
            logger.info(f"    Deployed: {route_path}")
        else:
            logger.error(f"    Failed: {route_path} — {result.get('error', 'unknown')}")

        time.sleep(1)  # rate limit

    # Summary
    ok = sum(1 for r in results if r.get("success") or r.get("status") == "dry_run")
    fail = len(results) - ok
    logger.info(f"[provision] Done: {ok} succeeded, {fail} failed")
    return results


def unprovision(dry_run: bool = False):
    manifest = load_manifest()
    logger.info(f"[unprovision] {len(manifest)} routes to remove")

    if not dry_run:
        api_key = get_zo_api_key()
        api_base = get_zo_api_base()

    results = []
    for entry in manifest:
        route_path = entry["path"]
        logger.info(f"  Removing: {route_path}")

        if dry_run:
            results.append({"path": route_path, "status": "dry_run"})
            continue

        result = delete_route(api_base, api_key, route_path)
        if not result.get("success") and result.get("status") == 404:
            logger.warning(f"    Direct route API unavailable for {route_path}; retrying delete via /zo/ask")
            result = delete_route_via_zo_ask(api_base, api_key, route_path)
        results.append({"path": route_path, **result})

        if result["success"]:
            logger.info(f"    Removed: {route_path}")
        else:
            logger.error(f"    Failed: {route_path} — {result.get('error', 'unknown')}")

        time.sleep(1)

    ok = sum(1 for r in results if r.get("success") or r.get("status") == "dry_run")
    fail = len(results) - ok
    logger.info(f"[unprovision] Done: {ok} removed, {fail} failed")
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="ZoATS zo.space Route Provisioner")
    ap.add_argument("--dry-run", action="store_true", help="Preview without deploying")
    ap.add_argument("--remove", action="store_true", help="Remove all ZoATS routes")

    args = ap.parse_args()

    if args.remove:
        results = unprovision(dry_run=args.dry_run)
    else:
        results = provision(dry_run=args.dry_run)

    print(json.dumps(results, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
