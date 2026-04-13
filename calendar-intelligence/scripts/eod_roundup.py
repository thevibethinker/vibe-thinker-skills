#!/usr/bin/env python3
"""EOD Roundup — compiles the evening digest from pre-fetched data.

Subcommands:
  compile       Build the markdown digest from events + intel files
  cache-check   Check attendee LinkedIn cache freshness
  cache-update  Update a single attendee in the cache
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import OrderedDict

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_ROOT, "data")
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")
CACHE_FILE = os.path.join(DATA_DIR, "attendee_cache.json")
CACHE_TTL_DAYS = 7


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load_json(path: str) -> dict | list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def _write_json(path: str, data: dict | list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_cache(cache: dict) -> None:
    _write_json(CACHE_FILE, cache)


def _parse_iso(s: str) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _format_time(iso_str: str) -> str:
    if iso_str is None or not isinstance(iso_str, str) or not iso_str.strip():
        return "(no time)"
    dt = _parse_iso(iso_str)
    if dt is None:
        return iso_str
    return dt.strftime("%I:%M %p").lstrip("0")


def _format_time_range(start: str, end: str) -> str:
    return f"{_format_time(start)} – {_format_time(end)}"


def _minutes_between(start: str, end: str) -> int | None:
    s = _parse_iso(start)
    e = _parse_iso(end)
    if s and e:
        return int((e - s).total_seconds() / 60)
    return None


def _collect_unique_attendees(events: list[dict]) -> dict[str, dict]:
    attendees: dict[str, dict] = {}
    for evt in events:
        for a in evt.get("attendees", []) or []:
            email = (a.get("email") or "").lower().strip()
            if not email:
                continue
            if email not in attendees:
                attendees[email] = {
                    "email": email,
                    "name": a.get("name") or email.split("@")[0],
                    "meetings": [],
                }
            attendees[email]["meetings"].append(evt.get("summary") or "(untitled)")
    return attendees


def _detect_flags(events: list[dict]) -> list[str]:
    flags = []
    sorted_events = sorted(events, key=lambda e: e.get("start") or "")

    for i in range(1, len(sorted_events)):
        prev_end = _parse_iso(sorted_events[i - 1].get("end") or "")
        curr_start = _parse_iso(sorted_events[i].get("start") or "")
        if prev_end and curr_start:
            gap = (curr_start - prev_end).total_seconds() / 60
            if gap < 5:
                flags.append(
                    f"⚠️ Back-to-back: **{sorted_events[i-1].get('summary') or '?'}** → "
                    f"**{sorted_events[i].get('summary') or '?'}** (gap: {int(gap)} min)"
                )

    for evt in events:
        desc = (evt.get("description") or "").strip()
        if not desc:
            flags.append(
                f"📝 No agenda/description: **{evt.get('summary') or '(untitled)'}**"
            )

    all_attendee_emails: set[str] = set()
    cache = _load_cache()
    for evt in events:
        for a in evt.get("attendees", []) or []:
            email = (a.get("email") or "").lower().strip()
            if email and email not in cache and email not in all_attendee_emails:
                name = a.get("name") or email
                flags.append(
                    f"👤 First-time attendee: **{name}** ({email}) in "
                    f"**{evt.get('summary') or '(untitled)'}**"
                )
            if email:
                all_attendee_emails.add(email)

    return flags


def _build_schedule_section(events: list[dict]) -> str:
    if not events:
        return "No events scheduled for tomorrow.\n"

    sorted_events = sorted(events, key=lambda e: e.get("start") or "")
    lines = []
    for evt in sorted_events:
        time_str = _format_time_range(evt.get("start") or "", evt.get("end") or "")
        duration = evt.get("duration_minutes")
        if duration is None:
            duration = _minutes_between(evt.get("start") or "", evt.get("end") or "")
        dur_str = f" ({duration} min)" if duration else ""
        location = evt.get("location") or ""
        loc_str = f" · {location}" if location else ""

        lines.append(f"| {time_str} | **{evt.get('summary') or '(untitled)'}**{dur_str}{loc_str} |")

    header = "| Time | Event |\n|------|-------|\n"
    return header + "\n".join(lines) + "\n"


def _build_attendee_intel_section(
    attendees: dict[str, dict],
    email_intel: dict,
    linkedin_intel: dict,
) -> str:
    if not attendees:
        return "No external attendees found.\n"

    email_data = email_intel.get("attendees", {}) if isinstance(email_intel, dict) else {}
    profile_data = linkedin_intel.get("profiles", {}) if isinstance(linkedin_intel, dict) else {}
    sections = []

    for email, info in sorted(attendees.items()):
        parts = [f"### {info['name']} ({email})"]

        profile = profile_data.get(email, {})
        if profile:
            headline = profile.get("headline") or ""
            location = profile.get("location") or ""
            if headline:
                parts.append(f"**{headline}**" + (f" · {location}" if location else ""))
            summary = profile.get("summary") or ""
            if summary:
                parts.append(f"> {summary[:200]}{'…' if len(summary) > 200 else ''}")
            experience = profile.get("experience") or []
            if experience:
                exp_lines = []
                for exp in experience[:3]:
                    dur = f" ({exp['duration']})" if exp.get("duration") else ""
                    exp_lines.append(f"  - {exp.get('title') or '?'} at {exp.get('company') or '?'}{dur}")
                parts.append("**Recent Experience:**\n" + "\n".join(exp_lines))

        edata = email_data.get(email, {})
        threads = edata.get("recent_threads") or []
        last_contact = edata.get("last_contact") or ""
        thread_count = edata.get("thread_count", 0)

        if threads:
            parts.append(f"**Email Activity** ({thread_count} threads, last contact: {last_contact}):")
            for t in threads[:5]:
                direction_icon = "📥" if t.get("direction") == "inbound" else "📤"
                snippet = t.get("snippet") or ""
                snippet_str = f" — _{snippet[:80]}{'…' if len(snippet) > 80 else ''}_" if snippet else ""
                parts.append(
                    f"  - {direction_icon} **{t.get('subject') or '(no subject)'}** "
                    f"({t.get('date') or '?'}){snippet_str}"
                )
        elif last_contact:
            parts.append(f"**Email Activity:** Last contact {last_contact} ({thread_count} threads)")
        else:
            parts.append("**Email Activity:** No recent email history")

        meeting_list = ", ".join(info["meetings"])
        parts.append(f"**In meetings:** {meeting_list}")

        sections.append("\n".join(parts))

    return "\n\n---\n\n".join(sections) + "\n"


def _build_meeting_prep_section(
    events: list[dict],
    email_intel: dict,
    linkedin_intel: dict,
) -> str:
    if not events:
        return "No meetings to prepare for.\n"

    sorted_events = sorted(events, key=lambda e: e.get("start") or "")
    email_data = email_intel.get("attendees", {}) if isinstance(email_intel, dict) else {}
    profile_data = linkedin_intel.get("profiles", {}) if isinstance(linkedin_intel, dict) else {}
    cache = _load_cache()
    sections = []

    for i, evt in enumerate(sorted_events):
        time_str = _format_time_range(evt.get("start") or "", evt.get("end") or "")
        parts = [f"### {evt.get('summary') or '(untitled)'} ({time_str})"]

        description = (evt.get("description") or "").strip()
        if description:
            trimmed = description[:300] + ("…" if len(description) > 300 else "")
            parts.append(f"**Agenda:** {trimmed}")
        else:
            parts.append("**Agenda:** ⚠️ No description provided")

        location = evt.get("location") or ""
        if location:
            parts.append(f"**Location:** {location}")

        event_attendees = evt.get("attendees", []) or []
        if event_attendees:
            att_parts = []
            for a in event_attendees:
                email = (a.get("email") or "").lower().strip()
                name = a.get("name") or email or "(unknown)"
                response = a.get("response") or "unknown"
                response_icon = {"accepted": "✅", "declined": "❌", "tentative": "❓"}.get(
                    response, "⬜"
                )
                profile = profile_data.get(email, {}) if email else {}
                headline = profile.get("headline") or ""
                title_str = f" — {headline}" if headline else ""
                att_parts.append(f"  - {response_icon} {name}{title_str}")
            parts.append("**Attendees:**\n" + "\n".join(att_parts))

        context_snippets = []
        for a in event_attendees:
            email = (a.get("email") or "").lower().strip()
            if not email:
                continue
            edata = email_data.get(email, {})
            threads = edata.get("recent_threads") or []
            if threads:
                subj = threads[0].get("subject") or ""
                context_snippets.append(
                    f"Recent thread with {a.get('name') or email}: \"{subj}\""
                )
        if context_snippets:
            parts.append("**Email Context:**\n" + "\n".join(f"  - {s}" for s in context_snippets))

        meeting_flags = []
        if not description:
            meeting_flags.append("No agenda")
        new_attendees = [
            a.get("name") or (a.get("email") or "(unknown)")
            for a in event_attendees
            if (a.get("email") or "").lower().strip() not in cache
        ]
        if new_attendees:
            meeting_flags.append(f"New attendee(s): {', '.join(new_attendees)}")
        if i > 0:
            prev_end = _parse_iso(sorted_events[i - 1].get("end") or "")
            curr_start = _parse_iso(evt.get("start") or "")
            if prev_end and curr_start:
                gap = (curr_start - prev_end).total_seconds() / 60
                if gap < 5:
                    meeting_flags.append(
                        f"Back-to-back with {sorted_events[i-1].get('summary') or '?'}"
                    )

        if meeting_flags:
            parts.append("**Flags:** " + " · ".join(f"⚠️ {f}" for f in meeting_flags))

        sections.append("\n".join(parts))

    return "\n\n---\n\n".join(sections) + "\n"


def cmd_compile(args: argparse.Namespace) -> None:
    if not os.path.exists(args.events):
        print(f"Error: Events file not found: {args.events}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.email_intel):
        print(f"Error: Email intel file not found: {args.email_intel}", file=sys.stderr)
        sys.exit(1)

    events = _load_json(args.events)
    if isinstance(events, dict):
        if "events" in events:
            events = events["events"]
        elif "items" in events:
            events = events["items"]
    if not isinstance(events, list):
        print("Error: Events file must contain a JSON array, {\"events\": [...]}, or {\"items\": [...]}", file=sys.stderr)
        sys.exit(1)

    email_intel = _load_json(args.email_intel)
    if not isinstance(email_intel, dict):
        print("Error: Email intel file must contain a JSON object (dict), got " + type(email_intel).__name__, file=sys.stderr)
        sys.exit(1)

    linkedin_intel: dict = {}
    if args.linkedin_intel and os.path.exists(args.linkedin_intel):
        linkedin_intel = _load_json(args.linkedin_intel)
        if not isinstance(linkedin_intel, dict):
            print("Warning: LinkedIn intel file is not a JSON object, ignoring", file=sys.stderr)
            linkedin_intel = {}

    output_path = args.output
    if output_path is None:
        today = datetime.now().strftime("%Y-%m-%d")
        output_path = os.path.join(DATA_DIR, f"roundup_{today}.md")

    attendees = _collect_unique_attendees(events)
    flags = _detect_flags(events)

    sorted_for_label = sorted(events, key=lambda e: e.get("start") or "")
    tomorrow_label = "Tomorrow"
    if sorted_for_label:
        first_start = _parse_iso(sorted_for_label[0].get("start") or "")
        if first_start:
            tomorrow_label = first_start.strftime("%A, %B %-d, %Y")

    lines = [
        "---",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
        f"version: 1.0",
        f"provenance: calendar-intelligence/eod-roundup",
        "---",
        "",
        f"# EOD Roundup — {tomorrow_label}",
        "",
        f"*Compiled {datetime.now().strftime('%Y-%m-%d %I:%M %p')} · "
        f"{len(events)} event(s) · {len(attendees)} unique attendee(s)*",
        "",
    ]

    lines.append("## 📅 Schedule Overview\n")
    lines.append(_build_schedule_section(events))
    lines.append("")

    if attendees:
        lines.append("## 👥 Attendee Intel\n")
        lines.append(_build_attendee_intel_section(attendees, email_intel, linkedin_intel))
        lines.append("")

    lines.append("## 📋 Meeting Prep\n")
    lines.append(_build_meeting_prep_section(events, email_intel, linkedin_intel))
    lines.append("")

    if flags:
        lines.append("## 🚩 Flags & Alerts\n")
        for flag in flags:
            lines.append(f"- {flag}")
        lines.append("")

    digest = "\n".join(lines)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(digest)

    print(digest)
    print(f"\n--- Digest written to {output_path} ---", file=sys.stderr)


def cmd_cache_check(args: argparse.Namespace) -> None:
    emails = [e.strip().lower() for e in args.attendees.split(",") if e.strip()]
    if not emails:
        print("Error: No emails provided", file=sys.stderr)
        sys.exit(1)

    cache = _load_cache()
    now = _now_utc()
    needs_refresh: list[str] = []

    print(f"Attendee Cache Check ({len(emails)} emails)")
    print("=" * 60)

    for email in emails:
        entry = cache.get(email)
        if entry is None:
            print(f"  {email}: NOT CACHED")
            needs_refresh.append(email)
            continue

        cached_at_str = entry.get("cached_at", "")
        cached_at = _parse_iso(cached_at_str)
        if cached_at is None:
            print(f"  {email}: CACHED (invalid timestamp — treating as expired)")
            needs_refresh.append(email)
            continue

        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)

        age = now - cached_at
        age_days = age.total_seconds() / 86400
        expired = age_days > CACHE_TTL_DAYS

        name = entry.get("name", "")
        name_str = f" [{name}]" if name else ""

        status = "EXPIRED" if expired else "FRESH"
        print(f"  {email}{name_str}: {status} (age: {age_days:.1f} days, cached: {cached_at_str})")

        if expired:
            needs_refresh.append(email)

    print()
    if needs_refresh:
        print(f"Needs refresh ({len(needs_refresh)}):")
        for email in needs_refresh:
            print(f"  - {email}")
    else:
        print("All entries are fresh.")


def cmd_cache_update(args: argparse.Namespace) -> None:
    email = args.email.strip().lower()
    if not email:
        print("Error: --email is required", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.profile_json):
        print(f"Error: Profile file not found: {args.profile_json}", file=sys.stderr)
        sys.exit(1)

    profile = _load_json(args.profile_json)
    cache = _load_cache()

    profile["cached_at"] = _now_utc().isoformat()

    cache[email] = profile
    _write_cache(cache)

    name = profile.get("name", email)
    print(f"Cache updated: {name} ({email})")
    print(f"  cached_at: {profile['cached_at']}")
    print(f"  cache size: {len(cache)} entries")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="eod_roundup.py",
        description="EOD Roundup — compile evening digest from pre-fetched calendar + intel data",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_compile = subparsers.add_parser(
        "compile",
        help="Build the markdown digest from events + intel files",
    )
    p_compile.add_argument(
        "--events",
        required=True,
        help="Path to tomorrow's events JSON (array or {events: [...]})",
    )
    p_compile.add_argument(
        "--email-intel",
        required=True,
        help="Path to email intel JSON (keyed by attendee email)",
    )
    p_compile.add_argument(
        "--linkedin-intel",
        default=None,
        help="Path to LinkedIn intel JSON (optional, keyed by attendee email)",
    )
    p_compile.add_argument(
        "--output",
        default=None,
        help="Output path for digest markdown (default: data/roundup_YYYY-MM-DD.md)",
    )
    p_compile.set_defaults(func=cmd_compile)

    p_check = subparsers.add_parser(
        "cache-check",
        help="Check attendee LinkedIn cache freshness",
    )
    p_check.add_argument(
        "--attendees",
        required=True,
        help="Comma-separated attendee emails to check",
    )
    p_check.set_defaults(func=cmd_cache_check)

    p_update = subparsers.add_parser(
        "cache-update",
        help="Update a single attendee in the LinkedIn cache",
    )
    p_update.add_argument(
        "--email",
        required=True,
        help="Attendee email address",
    )
    p_update.add_argument(
        "--profile-json",
        required=True,
        help="Path to JSON file with the LinkedIn profile data",
    )
    p_update.set_defaults(func=cmd_cache_update)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
