#!/usr/bin/env python3
"""Calendar pattern analysis for calendar-intelligence."""

import argparse
import json
import sys
import yaml
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- helpers ---


def latest_scan_date() -> str | None:
    if not DATA_DIR.exists():
        return None
    files = sorted(DATA_DIR.glob("scan_*.json"))
    if not files:
        return None
    return files[-1].stem.replace("scan_", "")


def load_scan(date_str: str) -> dict:
    path = DATA_DIR / f"scan_{date_str}.json"
    if not path.exists():
        print(f"Error: scan file not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: malformed JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def load_pattern_library() -> dict:
    path = ASSETS_DIR / "pattern_library.yaml"
    if not path.exists():
        print(f"Error: pattern library not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"Error: malformed YAML in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def load_config() -> dict:
    default = {"preferences": {"work_hours": {"start": "09:00", "end": "18:00"}, "work_days": [1, 2, 3, 4, 5]}}
    path = DATA_DIR / "config.yaml"
    if not path.exists():
        return default
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else default
    except yaml.YAMLError as e:
        print(f"Warning: malformed config YAML in {path}: {e}. Using defaults.", file=sys.stderr)
        return default


def parse_dt(iso_str: str | None) -> datetime | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b else default


def round2(val: float) -> float:
    return round(val, 2)


# --- analysis engines ---


def group_events_by_date(events: list[dict]) -> dict[str, list[dict]]:
    by_date: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        start = parse_dt(e.get("start"))
        if start is None:
            continue
        if e.get("is_all_day"):
            continue
        by_date[start.strftime("%Y-%m-%d")].append(e)
    for day_events in by_date.values():
        day_events.sort(key=lambda ev: ev.get("start", ""))
    return dict(by_date)


def calc_meeting_density(events_by_date: dict[str, list[dict]], work_days: list[int]) -> dict:
    daily_hours: dict[str, float] = {}
    for day_str, day_events in events_by_date.items():
        total_min = sum(e.get("duration_minutes", 0) for e in day_events)
        daily_hours[day_str] = total_min / 60.0

    if not daily_hours:
        return {
            "daily_avg_hours": 0.0,
            "weekly_total_hours": 0.0,
            "busiest_day": None,
            "lightest_day": None,
        }

    total_days = len(daily_hours)
    total_hours = sum(daily_hours.values())
    daily_avg = round2(safe_div(total_hours, total_days))

    num_weeks = max(total_days / 7.0, 1.0)
    weekly_total = round2(total_hours / num_weeks)

    busiest = max(daily_hours, key=daily_hours.get)
    lightest = min(daily_hours, key=daily_hours.get)

    return {
        "daily_avg_hours": daily_avg,
        "weekly_total_hours": weekly_total,
        "busiest_day": busiest,
        "lightest_day": lightest,
    }


def calc_buffer_gaps(events_by_date: dict[str, list[dict]]) -> dict:
    back_to_back = 0
    short_gaps = 0
    all_gaps: list[float] = []

    for day_events in events_by_date.values():
        timed = []
        for e in day_events:
            s = parse_dt(e.get("start"))
            en = parse_dt(e.get("end"))
            if s and en:
                timed.append((s, en))
        timed.sort(key=lambda x: x[0])

        for i in range(1, len(timed)):
            prev_end = timed[i - 1][1]
            curr_start = timed[i][0]
            gap_min = (curr_start - prev_end).total_seconds() / 60.0
            if gap_min <= 0:
                back_to_back += 1
                all_gaps.append(0.0)
            elif gap_min < 15:
                short_gaps += 1
                all_gaps.append(gap_min)
            else:
                all_gaps.append(gap_min)

    avg_gap = round2(safe_div(sum(all_gaps), len(all_gaps))) if all_gaps else 0.0
    num_days = len(events_by_date) or 1
    num_weeks = max(num_days / 7.0, 1.0)
    b2b_per_week = round2(back_to_back / num_weeks)

    return {
        "back_to_back_count": back_to_back,
        "back_to_back_per_week": b2b_per_week,
        "avg_gap_minutes": avg_gap,
        "short_gap_count": short_gaps,
    }


def calc_recurring_load(events: list[dict], events_by_date: dict[str, list[dict]]) -> dict:
    non_allday = [e for e in events if not e.get("is_all_day")]
    recurring = [e for e in non_allday if e.get("is_recurring")]
    recurring_count = len(recurring)
    recurring_min = sum(e.get("duration_minutes", 0) for e in recurring)
    total_min = sum(e.get("duration_minutes", 0) for e in non_allday)

    num_days = len(events_by_date) or 1
    num_weeks = max(num_days / 7.0, 1.0)
    recurring_hours_weekly = round2(recurring_min / 60.0 / num_weeks)
    pct = round2(safe_div(recurring_min, total_min) * 100)

    return {
        "recurring_count": recurring_count,
        "recurring_hours_weekly": recurring_hours_weekly,
        "recurring_pct_of_total": pct,
    }


def calc_collaborator_frequency(events: list[dict]) -> dict:
    attendee_stats: dict[str, dict] = {}

    non_allday = [e for e in events if not e.get("is_all_day")]
    for e in non_allday:
        dur = e.get("duration_minutes", 0)
        for att in e.get("attendees", []):
            email = att.get("email", "")
            if not email:
                continue
            if email not in attendee_stats:
                attendee_stats[email] = {
                    "email": email,
                    "name": att.get("name", ""),
                    "meeting_count": 0,
                    "total_hours": 0.0,
                }
            attendee_stats[email]["meeting_count"] += 1
            attendee_stats[email]["total_hours"] += dur / 60.0
            if att.get("name") and not attendee_stats[email]["name"]:
                attendee_stats[email]["name"] = att["name"]

    ranked = sorted(attendee_stats.values(), key=lambda x: x["meeting_count"], reverse=True)
    for entry in ranked:
        entry["total_hours"] = round2(entry["total_hours"])
    top_10 = ranked[:10]

    return {
        "top_10_attendees": top_10,
        "unique_attendee_count": len(attendee_stats),
    }


def calc_time_clustering(events_by_date: dict[str, list[dict]]) -> dict:
    hourly: dict[str, int] = {f"{h:02d}:00": 0 for h in range(24)}
    day_dist: dict[str, int] = {d: 0 for d in DAY_NAMES}
    morning = 0
    afternoon = 0

    for day_str, day_events in events_by_date.items():
        for e in day_events:
            start = parse_dt(e.get("start"))
            if not start:
                continue
            hour_key = f"{start.hour:02d}:00"
            hourly[hour_key] = hourly.get(hour_key, 0) + 1

            weekday = start.weekday()
            day_name = DAY_NAMES[weekday]
            day_dist[day_name] = day_dist.get(day_name, 0) + 1

            if start.hour < 12:
                morning += 1
            else:
                afternoon += 1

    total = morning + afternoon
    morning_pct = round2(safe_div(morning, total) * 100)
    afternoon_pct = round2(100 - morning_pct) if total else 0.0

    return {
        "hourly_heatmap": hourly,
        "day_distribution": day_dist,
        "morning_vs_afternoon_pct": {"morning": morning_pct, "afternoon": afternoon_pct},
    }


def calc_deep_work_windows(
    events_by_date: dict[str, list[dict]],
    work_hours_start: str,
    work_hours_end: str,
    work_days: list[int],
) -> dict:
    wh_start = datetime.strptime(work_hours_start, "%H:%M").time()
    wh_end = datetime.strptime(work_hours_end, "%H:%M").time()

    longest_blocks: dict[str, float] = {}
    blocks_over_2h: dict[str, int] = {}

    for day_str, day_events in events_by_date.items():
        try:
            day_date = datetime.strptime(day_str, "%Y-%m-%d")
        except ValueError:
            continue

        if day_date.isoweekday() not in work_days:
            continue

        day_start = datetime.combine(day_date.date(), wh_start)
        day_end = datetime.combine(day_date.date(), wh_end)

        if day_events and day_events[0].get("start"):
            first_event_tz = parse_dt(day_events[0]["start"])
            if first_event_tz and first_event_tz.tzinfo:
                tz = first_event_tz.tzinfo
                day_start = day_start.replace(tzinfo=tz)
                day_end = day_end.replace(tzinfo=tz)

        intervals = []
        for e in day_events:
            s = parse_dt(e.get("start"))
            en = parse_dt(e.get("end"))
            if s and en:
                intervals.append((s, en))
        intervals.sort(key=lambda x: x[0])

        free_blocks: list[float] = []
        cursor = day_start
        for s, en in intervals:
            if s > cursor:
                gap_hours = (s - cursor).total_seconds() / 3600.0
                if gap_hours > 0:
                    free_blocks.append(gap_hours)
            if en > cursor:
                cursor = en
        if day_end > cursor:
            final_gap = (day_end - cursor).total_seconds() / 3600.0
            if final_gap > 0:
                free_blocks.append(final_gap)

        iso_week = day_date.strftime("%Y-W%W")
        if free_blocks:
            longest_blocks[day_str] = max(free_blocks)
        else:
            longest_blocks[day_str] = 0.0

        big = sum(1 for b in free_blocks if b >= 2.0)
        blocks_over_2h[iso_week] = blocks_over_2h.get(iso_week, 0) + big

    if longest_blocks:
        avg_longest = round2(sum(longest_blocks.values()) / len(longest_blocks))
    else:
        avg_longest = 0.0

    if blocks_over_2h:
        avg_blocks_2h_per_week = round2(sum(blocks_over_2h.values()) / len(blocks_over_2h))
    else:
        avg_blocks_2h_per_week = 0.0

    day_focus_scores: dict[int, list[float]] = defaultdict(list)
    for day_str, block_hours in longest_blocks.items():
        try:
            wd = datetime.strptime(day_str, "%Y-%m-%d").isoweekday()
            day_focus_scores[wd].append(block_hours)
        except ValueError:
            pass

    best_day = None
    best_avg = 0.0
    for wd, scores in day_focus_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        if avg > best_avg:
            best_avg = avg
            best_day = DAY_NAMES[wd - 1]

    return {
        "avg_longest_block_hours": avg_longest,
        "blocks_over_2h_per_week": avg_blocks_2h_per_week,
        "best_day_for_focus": best_day,
    }


def calc_context_switching(events_by_date: dict[str, list[dict]]) -> dict:
    daily_switches: list[int] = []

    for day_events in events_by_date.values():
        timed = []
        for e in day_events:
            s = parse_dt(e.get("start"))
            if s:
                attendee_set = frozenset(
                    email for a in e.get("attendees", [])
                    if (email := a.get("email", ""))
                )
                timed.append((s, attendee_set, e.get("summary", "")))
        timed.sort(key=lambda x: x[0])

        switches = 0
        for i in range(1, len(timed)):
            prev_attendees = timed[i - 1][1]
            curr_attendees = timed[i][1]
            if prev_attendees and curr_attendees:
                overlap = len(prev_attendees & curr_attendees)
                union = len(prev_attendees | curr_attendees)
                similarity = safe_div(overlap, union)
                if similarity < 0.5:
                    switches += 1
            else:
                switches += 1
        daily_switches.append(switches)

    avg_switches = round2(safe_div(sum(daily_switches), len(daily_switches))) if daily_switches else 0.0
    max_switches = max(daily_switches) if daily_switches else 0

    return {
        "avg_switches_per_day": avg_switches,
        "max_switches_in_a_day": max_switches,
    }


def calc_meeting_length_distribution(events: list[dict]) -> dict:
    non_allday = [e for e in events if not e.get("is_all_day")]
    durations = [e.get("duration_minutes", 0) for e in non_allday]
    durations = [d for d in durations if d > 0]

    if not durations:
        return {
            "distribution": {},
            "avg_duration_minutes": 0.0,
            "pct_over_60min": 0.0,
        }

    buckets = {"15min": 0, "30min": 0, "45min": 0, "60min": 0, "90min+": 0}
    for d in durations:
        if d <= 15:
            buckets["15min"] += 1
        elif d <= 30:
            buckets["30min"] += 1
        elif d <= 45:
            buckets["45min"] += 1
        elif d <= 60:
            buckets["60min"] += 1
        else:
            buckets["90min+"] += 1

    avg_dur = round2(sum(durations) / len(durations))
    over_60 = sum(1 for d in durations if d > 60)
    pct_over_60 = round2(safe_div(over_60, len(durations)) * 100)

    return {
        "distribution": buckets,
        "avg_duration_minutes": avg_dur,
        "pct_over_60min": pct_over_60,
    }


# --- threshold classification ---


def classify_meeting_density(metrics: dict, pattern_def: dict) -> str:
    avg = metrics["daily_avg_hours"]
    thresholds = pattern_def.get("thresholds", {})
    if avg <= thresholds.get("light", {}).get("max_daily_avg", 2.0):
        return "light"
    if avg <= thresholds.get("moderate", {}).get("max_daily_avg", 4.0):
        return "moderate"
    if avg <= thresholds.get("heavy", {}).get("max_daily_avg", 6.0):
        return "heavy"
    return "overloaded"


def classify_buffer_gaps(metrics: dict, pattern_def: dict) -> str:
    avg_gap = metrics["avg_gap_minutes"]
    b2b_pw = metrics.get("back_to_back_per_week", metrics.get("back_to_back_count", 0))
    if avg_gap < 10:
        return "critical"
    if b2b_pw > 3:
        return "warning"
    return "healthy"


def classify_recurring_load(metrics: dict, pattern_def: dict) -> str:
    pct = metrics["recurring_pct_of_total"]
    thresholds = pattern_def.get("thresholds", {})
    if pct <= thresholds.get("low", {}).get("max_pct", 30):
        return "low"
    if pct <= thresholds.get("moderate", {}).get("max_pct", 60):
        return "moderate"
    return "high"


def classify_deep_work(metrics: dict, pattern_def: dict) -> str:
    blocks = metrics["blocks_over_2h_per_week"]
    thresholds = pattern_def.get("thresholds", {})
    if blocks >= thresholds.get("healthy", {}).get("min_blocks_2h", 5):
        return "healthy"
    if blocks >= thresholds.get("constrained", {}).get("min_blocks_2h", 2):
        return "constrained"
    return "starved"


def classify_context_switching(metrics: dict, pattern_def: dict) -> str:
    avg = metrics["avg_switches_per_day"]
    thresholds = pattern_def.get("thresholds", {})
    if avg <= thresholds.get("low", {}).get("max_avg", 2):
        return "low"
    if avg <= thresholds.get("moderate", {}).get("max_avg", 4):
        return "moderate"
    return "high"


def get_threshold_label(pattern_def: dict, level: str) -> str:
    thresholds = pattern_def.get("thresholds", {})
    entry = thresholds.get(level, {})
    return entry.get("label", level)


def classify_all(all_metrics: dict, patterns_by_id: dict) -> dict[str, str]:
    levels: dict[str, str] = {}
    levels["meeting-density"] = classify_meeting_density(
        all_metrics["meeting-density"], patterns_by_id.get("meeting-density", {})
    )
    levels["buffer-gaps"] = classify_buffer_gaps(
        all_metrics["buffer-gaps"], patterns_by_id.get("buffer-gaps", {})
    )
    levels["recurring-load"] = classify_recurring_load(
        all_metrics["recurring-load"], patterns_by_id.get("recurring-load", {})
    )
    levels["collaborator-frequency"] = "info"
    levels["time-clustering"] = "info"
    levels["deep-work-windows"] = classify_deep_work(
        all_metrics["deep-work-windows"], patterns_by_id.get("deep-work-windows", {})
    )
    levels["context-switching"] = classify_context_switching(
        all_metrics["context-switching"], patterns_by_id.get("context-switching", {})
    )
    levels["meeting-length-distribution"] = "info"
    return levels


# --- report generation ---


def generate_insight(pattern_id: str, metrics: dict, level: str, pattern_def: dict) -> str:
    lines: list[str] = []

    if pattern_id == "meeting-density":
        lines.append(f"You average **{metrics['daily_avg_hours']}h** of meetings per day "
                      f"and **{metrics['weekly_total_hours']}h** per week.")
        if metrics["busiest_day"]:
            lines.append(f"Busiest day: {metrics['busiest_day']}. Lightest: {metrics['lightest_day']}.")
        if level in ("heavy", "overloaded"):
            lines.append("Consider declining lower-priority meetings or batching them into fewer days.")

    elif pattern_id == "buffer-gaps":
        lines.append(f"**{metrics['back_to_back_count']}** back-to-back meetings detected. "
                      f"Average gap between meetings: **{metrics['avg_gap_minutes']} min**.")
        if metrics["short_gap_count"]:
            lines.append(f"{metrics['short_gap_count']} gaps are under 15 minutes — barely enough for a break.")
        if level == "critical":
            lines.append("Your transition time is critically low. Add 5–10 min buffers between meetings.")

    elif pattern_id == "recurring-load":
        lines.append(f"**{metrics['recurring_count']}** recurring events consume "
                      f"**{metrics['recurring_hours_weekly']}h/week** "
                      f"({metrics['recurring_pct_of_total']}% of total meeting time).")
        if level == "high":
            lines.append("A large share of your calendar is locked by recurring commitments. "
                          "Audit which ones still deliver value.")

    elif pattern_id == "collaborator-frequency":
        top = metrics.get("top_10_attendees", [])
        lines.append(f"**{metrics['unique_attendee_count']}** unique attendees across scanned events.")
        if top:
            lines.append("Top collaborators:")
            for a in top[:5]:
                name = a.get("name") or a.get("email", "?")
                lines.append(f"  - {name}: {a['meeting_count']} meetings ({a['total_hours']}h)")

    elif pattern_id == "time-clustering":
        dist = metrics.get("day_distribution", {})
        ma = metrics.get("morning_vs_afternoon_pct", {})
        busiest_day = max(dist, key=dist.get) if dist else "N/A"
        lightest_day = min(dist, key=dist.get) if dist else "N/A"
        lines.append(f"Meetings cluster on **{busiest_day}** and thin out on **{lightest_day}**.")
        lines.append(f"Morning vs afternoon split: {ma.get('morning', 0)}% / {ma.get('afternoon', 0)}%.")
        heatmap = metrics.get("hourly_heatmap", {})
        peak_hours = sorted(heatmap, key=heatmap.get, reverse=True)[:3]
        if peak_hours:
            lines.append(f"Peak hours: {', '.join(peak_hours)}.")

    elif pattern_id == "deep-work-windows":
        lines.append(f"Average longest uninterrupted block: **{metrics['avg_longest_block_hours']}h**.")
        lines.append(f"Blocks ≥ 2h per week: **{metrics['blocks_over_2h_per_week']}**.")
        if metrics["best_day_for_focus"]:
            lines.append(f"Best day for focus work: **{metrics['best_day_for_focus']}**.")
        if level == "starved":
            lines.append("You have virtually no 2-hour focus blocks. Protect at least one per day.")
        elif level == "constrained":
            lines.append("Focus time exists but is limited. Try to batch meetings on fewer days.")

    elif pattern_id == "context-switching":
        lines.append(f"Average context switches per day: **{metrics['avg_switches_per_day']}**.")
        lines.append(f"Worst day: **{metrics['max_switches_in_a_day']}** switches.")
        if level == "high":
            lines.append("Constant topic and people shifts drain cognitive energy. "
                          "Group related meetings together where possible.")

    elif pattern_id == "meeting-length-distribution":
        dist = metrics.get("distribution", {})
        lines.append(f"Average meeting duration: **{metrics['avg_duration_minutes']} min**. "
                      f"Meetings over 60 min: **{metrics['pct_over_60min']}%**.")
        if dist:
            parts = [f"{k}: {v}" for k, v in dist.items() if v > 0]
            lines.append(f"Distribution: {', '.join(parts)}.")
        if metrics.get("pct_over_60min", 0) > 30:
            lines.append("A significant share of meetings run long. "
                          "Default to 25 or 50 min and require agendas for longer slots.")

    for ins in pattern_def.get("insights", []):
        lines.append(f"💡 {ins}")

    return "\n".join(lines)


def build_report(
    scan_date: str,
    all_metrics: dict,
    levels: dict[str, str],
    patterns_by_id: dict,
    scan_data: dict,
) -> str:
    frontmatter_metrics = {}
    for pid, m in all_metrics.items():
        serializable = {}
        for k, v in m.items():
            serializable[k] = v
        frontmatter_metrics[pid] = serializable

    fm = {
        "created": scan_date,
        "last_edited": scan_date,
        "version": "1.0",
        "provenance": "calendar-intelligence/analyze.py",
        "scan_date": scan_date,
        "total_events": scan_data.get("total_events", 0),
        "window": scan_data.get("window", {}),
        "thresholds": levels,
        "metrics": frontmatter_metrics,
    }

    lines: list[str] = []
    lines.append("---")
    lines.append(yaml.dump(fm, default_flow_style=False, sort_keys=False).rstrip())
    lines.append("---")
    lines.append("")
    lines.append(f"# Calendar Intelligence Report — {scan_date}")
    lines.append("")
    lines.append(f"**Scan window:** {scan_data.get('window', {}).get('start', '?')} → "
                  f"{scan_data.get('window', {}).get('end', '?')}  ")
    lines.append(f"**Total events:** {scan_data.get('total_events', 0)}  ")
    lines.append(f"**Calendars:** {', '.join(scan_data.get('calendars_scanned') or [])}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Threshold Summary")
    lines.append("")
    lines.append("| Pattern | Level |")
    lines.append("|---------|-------|")
    for pid, level in levels.items():
        pdef = patterns_by_id.get(pid, {})
        label = get_threshold_label(pdef, level) if level not in ("info", "warning", "critical", "healthy") else level
        lines.append(f"| {pdef.get('name', pid)} | {label} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    for pid in all_metrics:
        pdef = patterns_by_id.get(pid, {})
        level = levels.get(pid, "info")
        lines.append(f"## {pdef.get('name', pid)}")
        lines.append("")
        label = get_threshold_label(pdef, level) if level not in ("info", "warning", "critical", "healthy") else level
        lines.append(f"**Level:** {label}")
        lines.append("")
        insight = generate_insight(pid, all_metrics[pid], level, pdef)
        lines.append(insight)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# --- subcommands ---


def run_analysis(scan_data: dict, config: dict) -> tuple[dict, dict[str, str], dict]:
    lib = load_pattern_library()
    patterns_by_id = {p["id"]: p for p in lib.get("patterns", [])}

    events = scan_data.get("events", [])
    events_by_date = group_events_by_date(events)

    prefs = config.get("preferences") or {}
    wh = prefs.get("work_hours") or {}
    work_start = wh.get("start") or "09:00"
    work_end = wh.get("end") or "18:00"
    work_days = prefs.get("work_days") or [1, 2, 3, 4, 5]

    all_metrics: dict[str, dict] = {}
    all_metrics["meeting-density"] = calc_meeting_density(events_by_date, work_days)
    all_metrics["buffer-gaps"] = calc_buffer_gaps(events_by_date)
    all_metrics["recurring-load"] = calc_recurring_load(events, events_by_date)
    all_metrics["collaborator-frequency"] = calc_collaborator_frequency(events)
    all_metrics["time-clustering"] = calc_time_clustering(events_by_date)
    all_metrics["deep-work-windows"] = calc_deep_work_windows(
        events_by_date, work_start, work_end, work_days
    )
    all_metrics["context-switching"] = calc_context_switching(events_by_date)
    all_metrics["meeting-length-distribution"] = calc_meeting_length_distribution(events)

    levels = classify_all(all_metrics, patterns_by_id)

    return all_metrics, levels, patterns_by_id


def cmd_run(args: argparse.Namespace) -> None:
    date_str = args.date or latest_scan_date()
    if not date_str:
        print("No scan files found. Run scan.py ingest first.", file=sys.stderr)
        sys.exit(1)

    scan_data = load_scan(date_str)
    config = load_config()
    all_metrics, levels, patterns_by_id = run_analysis(scan_data, config)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = DATA_DIR / f"analysis_{date_str}.md"

    report = build_report(date_str, all_metrics, levels, patterns_by_id, scan_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report)

    print(f"Analysis complete for {date_str}")
    print(f"  Report: {output_path}")
    print(f"  Events analyzed: {scan_data.get('total_events', 0)}")
    print()
    print("Threshold summary:")
    for pid, level in levels.items():
        label = get_threshold_label(patterns_by_id.get(pid, {}), level) if level not in ("info", "warning", "critical", "healthy") else level
        print(f"  {patterns_by_id.get(pid, {}).get('name', pid)}: {label}")


def cmd_quick(args: argparse.Namespace) -> None:
    date_str = args.date or latest_scan_date()
    if not date_str:
        print("No scan files found. Run scan.py ingest first.", file=sys.stderr)
        sys.exit(1)

    scan_data = load_scan(date_str)
    config = load_config()
    all_metrics, levels, patterns_by_id = run_analysis(scan_data, config)

    print(f"Quick analysis — {date_str} ({scan_data.get('total_events', 0)} events)")
    print()
    for pid, level in levels.items():
        pdef = patterns_by_id.get(pid, {})
        label = get_threshold_label(pdef, level) if level not in ("info", "warning", "critical", "healthy") else level
        print(f"  {pdef.get('name', pid):.<40s} {label}")


# --- main ---


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="analyze.py",
        description="Calendar pattern analysis and reporting.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run full pattern analysis and generate report.")
    p_run.add_argument("--date", default=None, help="Scan date (YYYY-MM-DD). Default: latest scan.")
    p_run.add_argument("--output", default=None, help="Output file path. Default: data/analysis_YYYY-MM-DD.md")

    p_quick = sub.add_parser("quick", help="Quick threshold summary (no full report).")
    p_quick.add_argument("--date", default=None, help="Scan date (YYYY-MM-DD). Default: latest scan.")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "quick":
        cmd_quick(args)


if __name__ == "__main__":
    main()
