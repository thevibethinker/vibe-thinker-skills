#!/usr/bin/env python3
"""Calendar scan data ingestion and management for calendar-intelligence."""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def parse_datetime(dt_obj: dict) -> datetime | None:
    if not dt_obj or not isinstance(dt_obj, dict):
        return None
    try:
        if "dateTime" in dt_obj:
            raw = dt_obj["dateTime"]
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            return datetime.fromisoformat(raw)
        if "date" in dt_obj:
            return datetime.fromisoformat(dt_obj["date"])
    except (ValueError, TypeError):
        return None
    return None


def duration_minutes(start: datetime | None, end: datetime | None) -> int:
    if start is None or end is None:
        return 0
    start_aware = start.tzinfo is not None and start.utcoffset() is not None
    end_aware = end.tzinfo is not None and end.utcoffset() is not None
    if start_aware != end_aware:
        if start_aware:
            end = end.replace(tzinfo=timezone.utc)
        else:
            start = start.replace(tzinfo=timezone.utc)
    delta = end - start
    return max(int(delta.total_seconds() / 60), 0)


def normalize_event(raw_event: dict, calendar_id: str) -> dict:
    start_obj = raw_event.get("start") or {}
    end_obj = raw_event.get("end") or {}
    start_dt = parse_datetime(start_obj)
    end_dt = parse_datetime(end_obj)

    is_all_day = "date" in start_obj and "dateTime" not in start_obj

    attendees = []
    for att in raw_event.get("attendees") or []:
        attendees.append({
            "email": att.get("email", ""),
            "name": att.get("displayName", ""),
            "response": att.get("responseStatus", "needsAction"),
        })

    recurring_event_id = raw_event.get("recurringEventId")

    return {
        "id": raw_event.get("id", ""),
        "summary": raw_event.get("summary", "(No title)"),
        "start": start_dt.isoformat() if start_dt else None,
        "end": end_dt.isoformat() if end_dt else None,
        "duration_minutes": duration_minutes(start_dt, end_dt),
        "attendees": attendees,
        "is_recurring": recurring_event_id is not None,
        "recurring_event_id": recurring_event_id,
        "calendar_id": calendar_id,
        "location": raw_event.get("location", ""),
        "description": raw_event.get("description", ""),
        "status": raw_event.get("status", "confirmed"),
        "is_all_day": is_all_day,
    }


def scan_path_for_date(date_str: str) -> Path:
    return DATA_DIR / f"scan_{date_str}.json"


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_scan(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: could not read scan file {path}: {exc}", file=sys.stderr)
        return {}
    if not isinstance(data, dict):
        print(f"Warning: scan file {path} is not a JSON object, ignoring.", file=sys.stderr)
        return {}
    return data


def list_scan_files() -> list[Path]:
    if not DATA_DIR.exists():
        return []
    files = sorted(DATA_DIR.glob("scan_*.json"))
    return files


def latest_scan_date() -> str | None:
    files = list_scan_files()
    if not files:
        return None
    name = files[-1].stem
    return name.replace("scan_", "")


def compute_window(events: list[dict]) -> dict:
    starts = []
    for e in events:
        if e.get("start"):
            try:
                starts.append(datetime.fromisoformat(e["start"]).date().isoformat())
            except (ValueError, TypeError):
                pass
    if not starts:
        return {"start": "", "end": ""}
    starts.sort()
    return {"start": starts[0], "end": starts[-1]}


# --- SUBCOMMANDS ---


def cmd_ingest(args: argparse.Namespace) -> None:
    raw_path = Path(args.raw)
    if not raw_path.exists():
        print(f"Error: raw file not found: {raw_path}", file=sys.stderr)
        sys.exit(1)

    with open(raw_path, "r", encoding="utf-8") as f:
        try:
            raw_data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid JSON in {raw_path}: {exc}", file=sys.stderr)
            sys.exit(1)

    items = raw_data.get("items", [])
    if not items:
        print("Warning: no events found in raw data (empty 'items' array).")

    calendar_id = args.calendar_id
    normalized = [normalize_event(evt, calendar_id) for evt in items]

    date_str = today_str()
    scan_file = scan_path_for_date(date_str)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = load_scan(scan_file)

    if existing:
        existing_events: list[dict] = existing.get("events", [])
        merged_events = [e for e in existing_events if e.get("calendar_id") != calendar_id]
        merged_events.extend(normalized)
        calendars_scanned = list(set(existing.get("calendars_scanned", []) + [calendar_id]))
    else:
        merged_events = normalized
        calendars_scanned = [calendar_id]

    window = compute_window(merged_events)

    scan_data = {
        "scan_date": date_str,
        "window": window,
        "events": merged_events,
        "total_events": len(merged_events),
        "calendars_scanned": calendars_scanned,
    }

    with open(scan_file, "w", encoding="utf-8") as f:
        json.dump(scan_data, f, indent=2, ensure_ascii=False)

    event_starts = []
    for e in normalized:
        if e.get("start"):
            try:
                event_starts.append(datetime.fromisoformat(e["start"]).date().isoformat())
            except (ValueError, TypeError):
                pass
    if event_starts:
        event_starts.sort()
        range_str = f"{event_starts[0]} to {event_starts[-1]}"
    else:
        range_str = "N/A"

    print(f"Ingested {len(normalized)} events from calendar '{calendar_id}'")
    print(f"  Date range: {range_str}")
    print(f"  Scan file:  {scan_file}")
    print(f"  Total events in scan: {scan_data['total_events']}")
    print(f"  Calendars scanned:    {', '.join(calendars_scanned)}")


def cmd_summary(args: argparse.Namespace) -> None:
    if args.date:
        date_str = args.date
    else:
        date_str = latest_scan_date()
        if not date_str:
            print("No scan files found.", file=sys.stderr)
            sys.exit(1)

    scan_file = scan_path_for_date(date_str)
    if not scan_file.exists():
        print(f"Error: scan file not found: {scan_file}", file=sys.stderr)
        sys.exit(1)

    data = load_scan(scan_file)
    events = data.get("events", [])

    day_counts: Counter[str] = Counter()
    for e in events:
        if e.get("start"):
            try:
                day = datetime.fromisoformat(e["start"]).strftime("%Y-%m-%d (%A)")
                day_counts[day] += 1
            except (ValueError, TypeError):
                pass

    top_5 = day_counts.most_common(5)

    print(f"Scan: {date_str}")
    print(f"  Window:     {data.get('window', {}).get('start', '?')} → {data.get('window', {}).get('end', '?')}")
    print(f"  Total events: {data.get('total_events', len(events))}")
    print(f"  Calendars:    {', '.join(data.get('calendars_scanned', []))}")
    print()
    print("  Top 5 busiest days:")
    for day, count in top_5:
        print(f"    {day}: {count} events")
    if not top_5:
        print("    (no event data)")


def cmd_cleanup(args: argparse.Namespace) -> None:
    files = list_scan_files()
    keep = 4
    if len(files) <= keep:
        print(f"Nothing to clean up ({len(files)} scan file(s), keeping last {keep}).")
        return

    to_remove = files[:-keep]
    for f in to_remove:
        f.unlink()
        print(f"  Removed: {f.name}")

    print(f"Cleanup complete. Removed {len(to_remove)} file(s), kept {keep}.")


# --- MAIN ---


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scan.py",
        description="Calendar scan data ingestion and management.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest raw calendar API response into scan format.")
    p_ingest.add_argument("--raw", required=True, help="Path to raw JSON file (Google Calendar list-events response).")
    p_ingest.add_argument("--calendar-id", required=True, help="Calendar ID these events belong to.")

    p_summary = sub.add_parser("summary", help="Show summary of scan data.")
    p_summary.add_argument("--date", default=None, help="Scan date (YYYY-MM-DD). Default: latest scan.")

    sub.add_parser("cleanup", help="Remove old scan files (keep last 4).")

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "summary":
        cmd_summary(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)


if __name__ == "__main__":
    main()
