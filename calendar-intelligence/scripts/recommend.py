#!/usr/bin/env python3
"""Recommend — generate and manage automation recommendations.

Subcommands:
  generate   Produce recommendations from analysis + templates
  list       Show current recommendations
  activate   Output create_agent parameters for a recommendation
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

import yaml

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_ROOT, "data")
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")
CONFIG_PATH = os.path.join(DATA_DIR, "config.yaml")
TEMPLATES_PATH = os.path.join(ASSETS_DIR, "automation_templates.yaml")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_yaml(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _find_latest_file(pattern: str) -> str | None:
    matches = sorted(glob.glob(pattern))
    return matches[-1] if matches else None


def _extract_frontmatter(md_path: str) -> dict:
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("\r\n", "\n").replace("\r", "\n")

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _extract_analysis_metrics(md_path: str) -> dict:
    frontmatter = _extract_frontmatter(md_path)
    metrics = frontmatter.get("metrics", {})

    if not metrics:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        metrics = _parse_metrics_from_body(content)

    return metrics


def _parse_metrics_from_body(content: str) -> dict:
    metrics: dict = {}

    m = re.search(r"daily[_ ]avg(?:erage)?[_ ]hours?[:\s]+(\d+\.?\d*)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("meeting-density", {})["daily_avg_hours"] = float(m.group(1))

    m = re.search(r"weekly[_ ]total[_ ]hours?[:\s]+(\d+\.?\d*)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("meeting-density", {})["weekly_total_hours"] = float(m.group(1))

    m = re.search(r"back[_ ]to[_ ]back[_ ]count[:\s]+(\d+)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("buffer-gaps", {})["back_to_back_count"] = int(m.group(1))

    m = re.search(r"avg[_ ]gap[_ ]minutes?[:\s]+(\d+\.?\d*)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("buffer-gaps", {})["avg_gap_minutes"] = float(m.group(1))

    m = re.search(r"recurring[_ ]pct[_ ]of[_ ]total[:\s]+(\d+\.?\d*)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("recurring-load", {})["recurring_pct_of_total"] = float(m.group(1))

    m = re.search(r"blocks[_ ]over[_ ]2h[_ ]per[_ ]week[:\s]+(\d+)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("deep-work-windows", {})["blocks_over_2h_per_week"] = int(m.group(1))

    m = re.search(r"avg[_ ]switches[_ ]per[_ ]day[:\s]+(\d+\.?\d*)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("context-switching", {})["avg_switches_per_day"] = float(m.group(1))

    m = re.search(r"avg[_ ]duration[_ ]minutes?[:\s]+(\d+\.?\d*)", content, re.IGNORECASE)
    if m:
        metrics.setdefault("meeting-length-distribution", {})["avg_duration_minutes"] = float(m.group(1))

    return metrics


def _load_pattern_thresholds() -> dict:
    lib_path = os.path.join(ASSETS_DIR, "pattern_library.yaml")
    if not os.path.exists(lib_path):
        return {}
    lib = _load_yaml(lib_path)
    result: dict = {}
    for pattern in lib.get("patterns", []):
        pid = pattern.get("id", "")
        thresholds = pattern.get("thresholds", {})
        flags = pattern.get("flags", [])
        result[pid] = {"thresholds": thresholds, "flags": flags}
    return result


def _classify_threshold(pattern_id: str, metrics: dict, patterns: dict) -> str | None:
    pdata = patterns.get(pattern_id, {})
    thresholds = pdata.get("thresholds", {})
    if not thresholds:
        return None

    pattern_metrics = metrics.get(pattern_id, {})
    if not pattern_metrics:
        return None

    if pattern_id == "meeting-density":
        val = pattern_metrics.get("daily_avg_hours")
        if val is None:
            return None
        for level in ("light", "moderate", "heavy", "overloaded"):
            t = thresholds.get(level, {})
            if val <= t.get("max_daily_avg", float("inf")):
                return level
        return "overloaded"

    if pattern_id == "recurring-load":
        val = pattern_metrics.get("recurring_pct_of_total")
        if val is None:
            return None
        for level in ("low", "moderate", "high"):
            t = thresholds.get(level, {})
            if val <= t.get("max_pct", float("inf")):
                return level
        return "high"

    if pattern_id == "deep-work-windows":
        val = pattern_metrics.get("blocks_over_2h_per_week")
        if val is None:
            return None
        best = "starved"
        for level in ("starved", "constrained", "healthy"):
            t = thresholds.get(level, {})
            if val >= t.get("min_blocks_2h", 0):
                best = level
        return best

    if pattern_id == "context-switching":
        val = pattern_metrics.get("avg_switches_per_day")
        if val is None:
            return None
        for level in ("low", "moderate", "high"):
            t = thresholds.get(level, {})
            if val <= t.get("max_avg", float("inf")):
                return level
        return "high"

    return None


def _check_trigger_condition(condition: str, pattern_id: str, metrics: dict, patterns: dict) -> bool:
    pattern_metrics = metrics.get(pattern_id, {})
    pdata = patterns.get(pattern_id, {})

    cond = condition.strip()

    threshold_match = re.match(r"threshold\s*(>=|<=|>|<|==)\s*(\w+)", cond)
    if threshold_match:
        op = threshold_match.group(1)
        target_level = threshold_match.group(2)
        current_level = _classify_threshold(pattern_id, metrics, patterns)
        if current_level is None:
            return False

        thresholds = pdata.get("thresholds", {})
        level_order = list(thresholds.keys())
        if not level_order:
            return False

        try:
            current_idx = level_order.index(current_level)
            target_idx = level_order.index(target_level)
        except ValueError:
            return False

        if op == ">=":
            return current_idx >= target_idx
        if op == "<=":
            return current_idx <= target_idx
        if op == ">":
            return current_idx > target_idx
        if op == "<":
            return current_idx < target_idx
        if op == "==":
            return current_idx == target_idx
        return False

    metric_match = re.match(r"(\w+)\s*(>=|<=|>|<|==)\s*(\d+\.?\d*)", cond.split(" per ")[0].strip())
    if metric_match:
        metric_name = metric_match.group(1)
        op = metric_match.group(2)
        value = float(metric_match.group(3))
        actual = pattern_metrics.get(metric_name)
        if actual is None:
            return False
        actual = float(actual)
        if op == ">=":
            return actual >= value
        if op == "<=":
            return actual <= value
        if op == ">":
            return actual > value
        if op == "<":
            return actual < value
        if op == "==":
            return actual == value

    if cond:
        print(f"Warning: Unrecognized trigger condition format: {cond!r}", file=sys.stderr)
    return False


def _resolve_rrule(template: dict, config: dict) -> str:
    schedule = template.get("schedule", {})
    rrule_template = schedule.get("rrule_template", "")
    default_time = schedule.get("default_time", "21:00")

    tz = config.get("preferences", {}).get("timezone", "America/New_York")
    eod_time = config.get("preferences", {}).get("eod_time", default_time)

    use_time = eod_time if template.get("id") == "eod-roundup" else default_time

    try:
        parts = use_time.split(":")
        hour, minute = parts[0], parts[1]
    except (IndexError, ValueError):
        try:
            parts = default_time.split(":")
            hour, minute = parts[0], parts[1]
        except (IndexError, ValueError):
            hour, minute = "00", "00"

    now = _now_utc()
    dtstart = now.strftime(f"%Y%m%dT{hour}{minute}00")

    resolved = rrule_template.replace("{{DTSTART}}", dtstart)
    return resolved


def _resolve_delivery(template: dict, config: dict) -> str:
    delivery = template.get("delivery", "email")
    prefs = config.get("preferences", {})
    return delivery.replace("{{preferences.delivery_method}}", prefs.get("delivery_method", "email"))


def _resolve_instruction(template: dict) -> str:
    return template.get("instruction", "").strip()


def cmd_generate(args: argparse.Namespace) -> None:
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config not found at {CONFIG_PATH}. Run install first.", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(TEMPLATES_PATH):
        print(f"Error: Templates not found at {TEMPLATES_PATH}", file=sys.stderr)
        sys.exit(1)

    config = _load_yaml(CONFIG_PATH)
    templates_data = _load_yaml(TEMPLATES_PATH)
    templates = templates_data.get("templates", [])

    analysis_path = args.analysis
    if analysis_path is None:
        analysis_path = _find_latest_file(os.path.join(DATA_DIR, "analysis_*.md"))
        if analysis_path is None:
            print("Warning: No analysis file found. Only always-recommend templates will fire.",
                  file=sys.stderr)

    metrics: dict = {}
    if analysis_path and os.path.exists(analysis_path):
        metrics = _extract_analysis_metrics(analysis_path)
        print(f"Loaded metrics from: {analysis_path}", file=sys.stderr)
    else:
        print("Warning: Analysis file not found, proceeding with no metrics.", file=sys.stderr)

    patterns = _load_pattern_thresholds()

    recommendations = []
    today = _now_utc().strftime("%Y-%m-%d")

    for template in templates:
        tid = template.get("id", "unknown")
        name = template.get("name", tid)
        always = template.get("always_recommend", False)

        if always:
            reason = "Always recommended — core calendar intelligence automation"
            recommendations.append(_build_recommendation(template, config, reason, metrics, patterns))
            continue

        trigger_patterns = template.get("trigger_patterns", [])
        if not trigger_patterns:
            continue

        triggered = False
        reasons = []
        for tp in trigger_patterns:
            pattern_id = tp.get("pattern_id", "")
            condition = tp.get("condition", "")
            trigger_reason = tp.get("reason", f"Pattern {pattern_id} triggered")

            if _check_trigger_condition(condition, pattern_id, metrics, patterns):
                triggered = True
                current_level = _classify_threshold(pattern_id, metrics, patterns)
                level_str = f" (current: {current_level})" if current_level else ""
                reasons.append(f"{trigger_reason}{level_str}")

        if triggered:
            reason = "; ".join(reasons)
            recommendations.append(_build_recommendation(template, config, reason, metrics, patterns))

    output_data = {
        "version": "1.0",
        "generated": today,
        "analysis_source": analysis_path or "none",
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
    }

    output_path = args.output
    if output_path is None:
        output_path = os.path.join(DATA_DIR, f"recommendations_{today}.yaml")

    _write_yaml(output_path, output_data)

    print(f"\n{'=' * 60}")
    print(f"Calendar Intelligence — Recommendations ({today})")
    print(f"{'=' * 60}\n")

    if not recommendations:
        print("No recommendations generated. Analysis may not have enough data yet.")
    else:
        for i, rec in enumerate(recommendations, 1):
            status = rec.get("status", "pending")
            status_icon = {"pending": "⬜", "activated": "✅", "dismissed": "❌"}.get(status, "⬜")
            print(f"{i}. {status_icon} **{rec['name']}** (id: {rec['id']})")
            print(f"   {rec['description']}")
            print(f"   Schedule: {rec['schedule_description']}")
            print(f"   Delivery: {rec['delivery_method']}")
            print(f"   Reason: {rec['reason']}")
            print()

    print(f"Written to: {output_path}")


def _build_recommendation(template: dict, config: dict, reason: str, metrics: dict, patterns: dict) -> dict:
    tid = template.get("id", "unknown")
    return {
        "id": tid,
        "name": template.get("name", tid),
        "description": template.get("description", "").strip(),
        "rrule": _resolve_rrule(template, config),
        "schedule_description": template.get("schedule", {}).get("description", ""),
        "instruction": _resolve_instruction(template),
        "delivery_method": _resolve_delivery(template, config),
        "reason": reason,
        "status": "pending",
        "template_id": tid,
    }


def cmd_list(args: argparse.Namespace) -> None:
    if args.date:
        rec_path = os.path.join(DATA_DIR, f"recommendations_{args.date}.yaml")
    else:
        rec_path = _find_latest_file(os.path.join(DATA_DIR, "recommendations_*.yaml"))

    if not rec_path or not os.path.exists(rec_path):
        print("No recommendations file found. Run 'generate' first.", file=sys.stderr)
        sys.exit(1)

    data = _load_yaml(rec_path)
    recs = data.get("recommendations", [])

    print(f"Recommendations from: {rec_path}")
    print(f"Generated: {data.get('generated', '?')}")
    print(f"Total: {len(recs)}\n")

    if not recs:
        print("(no recommendations)")
        return

    for i, rec in enumerate(recs, 1):
        status = rec.get("status", "pending")
        status_icon = {"pending": "⬜", "activated": "✅", "dismissed": "❌"}.get(status, "⬜")
        print(f"{i}. {status_icon} {rec.get('name', '?')} (id: {rec.get('id', '?')})")
        print(f"   Schedule: {rec.get('schedule_description', '?')}")
        print(f"   Delivery: {rec.get('delivery_method', '?')}")
        print(f"   Reason: {rec.get('reason', '?')}")
        print(f"   Status: {status}")
        print()


def cmd_activate(args: argparse.Namespace) -> None:
    rec_path = _find_latest_file(os.path.join(DATA_DIR, "recommendations_*.yaml"))
    if not rec_path or not os.path.exists(rec_path):
        print("Error: No recommendations file found. Run 'generate' first.", file=sys.stderr)
        sys.exit(1)

    data = _load_yaml(rec_path)
    recs = data.get("recommendations", [])

    target = None
    for rec in recs:
        if rec.get("id") == args.id:
            target = rec
            break

    if target is None:
        available = [r.get("id") for r in recs]
        print(f"Error: Recommendation '{args.id}' not found.", file=sys.stderr)
        print(f"Available IDs: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)

    agent_params = {
        "rrule": target["rrule"],
        "instruction": target["instruction"],
        "delivery_method": target["delivery_method"],
    }

    print(json.dumps(agent_params, indent=2))

    target["status"] = "activated"
    target["activated_at"] = _now_utc().isoformat()
    _write_yaml(rec_path, data)

    if os.path.exists(CONFIG_PATH):
        config = _load_yaml(CONFIG_PATH)
        automations = config.get("automations", [])
        if not isinstance(automations, list):
            automations = []
        existing_ids = {a.get("template_id") for a in automations}
        if target["id"] not in existing_ids:
            automations.append({
                "template_id": target["id"],
                "name": target["name"],
                "activated_at": target["activated_at"],
                "rrule": target["rrule"],
                "delivery_method": target["delivery_method"],
            })
            config["automations"] = automations
            _write_yaml(CONFIG_PATH, config)
            print(f"\nConfig updated: added {target['id']} to automations list", file=sys.stderr)

    print(f"\nRecommendation '{target['id']}' marked as activated.", file=sys.stderr)
    print("Use the JSON above as parameters for Zo's create_agent tool.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="recommend.py",
        description="Generate and manage automation recommendations based on calendar analysis",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_gen = subparsers.add_parser(
        "generate",
        help="Produce recommendations from analysis + templates",
    )
    p_gen.add_argument(
        "--analysis",
        default=None,
        help="Path to analysis markdown (default: latest in data/)",
    )
    p_gen.add_argument(
        "--output",
        default=None,
        help="Output path for recommendations YAML (default: data/recommendations_YYYY-MM-DD.yaml)",
    )
    p_gen.set_defaults(func=cmd_generate)

    p_list = subparsers.add_parser(
        "list",
        help="Show current recommendations",
    )
    p_list.add_argument(
        "--date",
        default=None,
        help="Date to look up (YYYY-MM-DD; default: latest)",
    )
    p_list.set_defaults(func=cmd_list)

    p_activate = subparsers.add_parser(
        "activate",
        help="Output create_agent parameters for a recommendation",
    )
    p_activate.add_argument(
        "--id",
        required=True,
        help="Recommendation ID to activate (e.g. eod-roundup)",
    )
    p_activate.set_defaults(func=cmd_activate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
