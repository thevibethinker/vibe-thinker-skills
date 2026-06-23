#!/usr/bin/env python3
"""
Sender API (Night 1)

Goal: Minimal, reliable mechanism to "send" emails without external deps.
Default provider writes outbound messages to ZoATS/outbox/ as .eml-like files
so founders can review and manually send (or wire real providers later).

Usage:
  python workers/sender/main.py --job <job> --candidate <id> --type <clarification|rejection|custom> [--subject S] [--body PATH.md] [--dry-run]

Providers:
- file (default): write to outbox/<timestamp>_<job>_<candidate>_<type>.eml
- (future) gmail: send via Gmail API

Inputs (examples expected to exist):
- jobs/<job>/candidates/<id>/outputs/clarification_email.md (for type=clarification)
- jobs/<job>/candidates/<id>/outputs/rejection_email.md (for type=rejection)

Outputs:
- outbox/<timestamp>_<job>_<candidate>_<type>.eml

Quality:
- Logging, --dry-run, error handling, verification
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "settings.json"
OUTBOX = ROOT / "outbox"

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_body(job: str, candidate: str, mtype: str, explicit_body: Path | None) -> str:
    if explicit_body and explicit_body.exists():
        return explicit_body.read_text()
    default_map = {
        "clarification": ROOT / "jobs" / job / "candidates" / candidate / "outputs" / "clarification_email.md",
        "rejection": ROOT / "jobs" / job / "candidates" / candidate / "outputs" / "rejection_email.md",
    }
    path = default_map.get(mtype)
    if not path or not path.exists():
        raise FileNotFoundError(f"Email body not found for type={mtype}. Looked for: {path}")
    return path.read_text()


def build_eml(from_name: str, from_email: str, to_email: str, subject: str, body_md: str) -> str:
    ts = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    headers = [
        f"From: {from_name} <{from_email}>",
        f"To: {to_email}",
        f"Date: {ts}",
        f"Subject: {subject}",
        "MIME-Version: 1.0",
        "Content-Type: text/markdown; charset=utf-8",
    ]
    return "\n".join(headers) + "\n\n" + body_md


def save_eml(job: str, candidate: str, mtype: str, eml: str) -> Path:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    fname = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}_{job}_{candidate}_{mtype}.eml"
    path = OUTBOX / fname
    path.write_text(eml)
    return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--job", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--type", required=True, choices=["clarification", "rejection", "custom"])
    p.add_argument("--to", required=True, help="Recipient email address")
    p.add_argument("--subject", default=None)
    p.add_argument("--body", type=Path)
    p.add_argument("--from-name", default="ZoATS")
    p.add_argument("--from-email", default="noreply@example.com")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    try:
        body_md = load_body(args.job, args.candidate, args.type, args.body)
        subject = args.subject or {
            "clarification": "Quick clarification before next step",
            "rejection": "Thank you for applying",
            "custom": "Message from ZoATS",
        }[args.type]
        eml = build_eml(args["from-name"] if hasattr(args, "from-name") else args.from_name,
                        args["from-email"] if hasattr(args, "from-email") else args.from_email,
                        args.to, subject, body_md)
        if args.dry_run:
            logger.info("[DRY RUN] Would create EML:\n" + eml[:400] + ("..." if len(eml) > 400 else ""))
            return 0
        path = save_eml(args.job, args.candidate, args.type, eml)
        logger.info(f"✓ Written: {path}")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
