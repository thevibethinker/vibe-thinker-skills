#!/usr/bin/env python3
"""Calendar Intelligence — configuration lifecycle manager.

Subcommands:
    init      Create config from CLI flags
    status    Show current config
    update    Update specific config fields
    validate  Check config completeness and consistency
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import yaml

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_ROOT, "data")
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")
CONFIG_PATH = os.path.join(DATA_DIR, "config.yaml")
TEMPLATE_PATH = os.path.join(ASSETS_DIR, "config_template.yaml")

VALID_CAL_PROVIDERS = ("google_calendar", "microsoft_outlook")
VALID_MAIL_PROVIDERS = ("gmail", "microsoft_outlook")
VALID_DELIVERY_METHODS = ("email", "sms", "telegram")
VALID_WORK_DAYS = range(1, 8)  # 1=Monday … 7=Sunday


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Config file is empty or contains no YAML data: {path}")
    if not isinstance(data, dict):
        raise ValueError(f"Config file must be a YAML mapping, got {type(data).__name__}: {path}")
    return data


def _write_yaml(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _parse_calendars(raw: str) -> list[dict]:
    """Turn a comma-separated calendar string into a list of calendar dicts.

    Accepts either bare IDs ("primary,work") or id:name pairs
    ("primary:My Calendar,work:Work Calendar").
    """
    calendars = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            cal_id, cal_name = entry.split(":", 1)
            cal_id = cal_id.strip()
            cal_name = cal_name.strip()
        else:
            cal_id = entry
            cal_name = entry.capitalize()
        if not cal_id:
            raise ValueError(f"Empty calendar ID in '{entry}' — each calendar needs an ID (e.g. 'primary' or 'primary:My Calendar')")
        calendars.append({"id": cal_id, "name": cal_name or cal_id, "include": True})
    return calendars


def _parse_work_days(raw: str) -> list[int]:
    days = []
    for d in raw.split(","):
        d = d.strip()
        if not d:
            continue
        val = int(d)
        if val not in VALID_WORK_DAYS:
            raise ValueError(f"Invalid work day {val} — must be 1-7 (1=Monday, 7=Sunday)")
        days.append(val)
    return sorted(set(days))


def _validate_time(value: str, label: str) -> str:
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError:
        raise ValueError(f"Invalid {label} '{value}' — expected HH:MM (e.g. 09:00)")
    return value


def _day_name(d: int) -> str:
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d - 1]


def _validate_timezone(tz: str) -> str:
    """Validate that a timezone string is a known IANA timezone."""
    try:
        ZoneInfo(tz)
    except (KeyError, Exception):
        raise ValueError(f"Invalid timezone '{tz}' — must be a valid IANA timezone (e.g. America/New_York, UTC)")
    return tz


# ── init ──────────────────────────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> None:
    if os.path.exists(CONFIG_PATH) and not args.force:
        print(f"Config already exists at {CONFIG_PATH}")
        print("Use --force to overwrite, or 'update' to modify individual fields.")
        sys.exit(1)

    if not os.path.exists(TEMPLATE_PATH):
        print(f"ERROR: Template not found at {TEMPLATE_PATH}")
        sys.exit(1)

    cfg = _load_yaml(TEMPLATE_PATH)
    cfg["installed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # integrations.calendar
    if args.cal_provider:
        if args.cal_provider not in VALID_CAL_PROVIDERS:
            print(f"ERROR: --cal-provider must be one of {VALID_CAL_PROVIDERS}")
            sys.exit(1)
        cfg["integrations"]["calendar"]["provider"] = args.cal_provider

    if args.cal_email:
        cfg["integrations"]["calendar"]["email"] = args.cal_email

    if args.calendars:
        cfg["integrations"]["calendar"]["calendars"] = _parse_calendars(args.calendars)

    # integrations.email
    if args.mail_provider:
        if args.mail_provider not in VALID_MAIL_PROVIDERS:
            print(f"ERROR: --mail-provider must be one of {VALID_MAIL_PROVIDERS}")
            sys.exit(1)
        cfg["integrations"]["email"]["provider"] = args.mail_provider

    if args.mail_email:
        cfg["integrations"]["email"]["email"] = args.mail_email

    # integrations.linkedin
    if args.linkedin:
        cfg["integrations"]["linkedin"]["available"] = args.linkedin == "available"

    # preferences
    if args.timezone:
        cfg["preferences"]["timezone"] = _validate_timezone(args.timezone)

    if args.eod_time:
        cfg["preferences"]["eod_time"] = _validate_time(args.eod_time, "eod-time")

    if args.delivery:
        if args.delivery not in VALID_DELIVERY_METHODS:
            print(f"ERROR: --delivery must be one of {VALID_DELIVERY_METHODS}")
            sys.exit(1)
        cfg["preferences"]["delivery_method"] = args.delivery

    if args.work_start:
        cfg["preferences"]["work_hours"]["start"] = _validate_time(args.work_start, "work-start")

    if args.work_end:
        cfg["preferences"]["work_hours"]["end"] = _validate_time(args.work_end, "work-end")

    if args.work_days:
        cfg["preferences"]["work_days"] = _parse_work_days(args.work_days)

    _write_yaml(CONFIG_PATH, cfg)
    _print_init_summary(cfg)


def _print_init_summary(cfg: dict) -> None:
    cal = cfg["integrations"]["calendar"]
    mail = cfg["integrations"]["email"]
    li = cfg["integrations"]["linkedin"]
    prefs = cfg["preferences"]

    print("✓ Calendar Intelligence config created")
    print(f"  installed_at: {cfg['installed_at']}")
    print()
    print("  Integrations:")
    print(f"    Calendar : {cal['provider'] or '(not set)'} — {cal['email'] or '(not set)'}")
    if cal.get("calendars"):
        names = ", ".join(c["name"] for c in cal["calendars"])
        print(f"               calendars: {names}")
    print(f"    Email    : {mail['provider'] or '(not set)'} — {mail['email'] or '(not set)'}")
    print(f"    LinkedIn : {'available' if li.get('available') else 'unavailable'}")
    print()
    print("  Preferences:")
    print(f"    Timezone : {prefs['timezone']}")
    print(f"    EOD time : {prefs['eod_time']}")
    print(f"    Delivery : {prefs['delivery_method']}")
    day_str = ", ".join(_day_name(d) for d in prefs.get("work_days", []))
    print(f"    Work hrs : {prefs['work_hours']['start']}–{prefs['work_hours']['end']} ({day_str})")
    print()
    print(f"  Config path: {CONFIG_PATH}")


# ── status ────────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> None:
    if not os.path.exists(CONFIG_PATH):
        print("No config found. Run 'init' first.")
        sys.exit(1)

    cfg = _load_yaml(CONFIG_PATH)

    if args.json:
        print(json.dumps(cfg, indent=2, default=str))
        return

    try:
        cal = cfg["integrations"]["calendar"]
        mail = cfg["integrations"]["email"]
        li = cfg["integrations"]["linkedin"]
        prefs = cfg["preferences"]
    except KeyError as e:
        print(f"✗ Config is malformed — missing required key: {e}")
        print(f"  Run 'validate' to check, or 'init --force' to recreate.")
        sys.exit(1)

    print("╭─ Calendar Intelligence — Status ─────────────────────╮")
    print(f"│  Version     : {cfg.get('version', '?')}")
    print(f"│  Installed   : {cfg.get('installed_at', '?')}")
    print("│")
    print("│  Integrations")
    print(f"│    Calendar  : {cal.get('provider') or '✗ not configured'}")
    if cal.get("provider"):
        print(f"│               email: {cal.get('email') or '(not set)'}")
        if cal.get("calendars"):
            for c in cal["calendars"]:
                marker = "✓" if c.get("include") else "✗"
                print(f"│               {marker} {c['id']} ({c['name']})")
        else:
            print("│               (no calendars selected)")
    print(f"│    Email     : {mail.get('provider') or '✗ not configured'}")
    if mail.get("provider"):
        print(f"│               email: {mail.get('email') or '(not set)'}")
    print(f"│    LinkedIn  : {'✓ available' if li.get('available') else '✗ unavailable'}")
    print("│")
    print("│  Preferences")
    print(f"│    Timezone  : {prefs.get('timezone', '?')}")
    print(f"│    EOD time  : {prefs.get('eod_time', '?')}")
    print(f"│    Delivery  : {prefs.get('delivery_method', '?')}")
    day_str = ", ".join(_day_name(d) for d in prefs.get("work_days", []))
    wh = prefs.get("work_hours", {})
    print(f"│    Work hrs  : {wh.get('start', '?')}–{wh.get('end', '?')}")
    print(f"│    Work days : {day_str}")
    print("│")
    autos = cfg.get("automations") or []
    if autos:
        print(f"│  Automations ({len(autos)})")
        for a in autos:
            status = "active" if a.get("active") else "inactive"
            print(f"│    {a.get('id', '?'):20s} [{status}]")
    else:
        print("│  Automations : none")
    print("╰──────────────────────────────────────────────────────╯")


# ── update ────────────────────────────────────────────────────────────────────

def cmd_update(args: argparse.Namespace) -> None:
    if not os.path.exists(CONFIG_PATH):
        print("No config found. Run 'init' first.")
        sys.exit(1)

    cfg = _load_yaml(CONFIG_PATH)
    changes: list[str] = []

    # integrations.calendar
    if args.cal_provider:
        if args.cal_provider not in VALID_CAL_PROVIDERS:
            print(f"ERROR: --cal-provider must be one of {VALID_CAL_PROVIDERS}")
            sys.exit(1)
        cfg.setdefault("integrations", {}).setdefault("calendar", {})["provider"] = args.cal_provider
        changes.append(f"calendar.provider → {args.cal_provider}")

    if args.cal_email:
        cfg.setdefault("integrations", {}).setdefault("calendar", {})["email"] = args.cal_email
        changes.append(f"calendar.email → {args.cal_email}")

    if args.calendars:
        cals = _parse_calendars(args.calendars)
        cfg.setdefault("integrations", {}).setdefault("calendar", {})["calendars"] = cals
        names = ", ".join(c["id"] for c in cals)
        changes.append(f"calendar.calendars → [{names}]")

    # integrations.email
    if args.mail_provider:
        if args.mail_provider not in VALID_MAIL_PROVIDERS:
            print(f"ERROR: --mail-provider must be one of {VALID_MAIL_PROVIDERS}")
            sys.exit(1)
        cfg.setdefault("integrations", {}).setdefault("email", {})["provider"] = args.mail_provider
        changes.append(f"email.provider → {args.mail_provider}")

    if args.mail_email:
        cfg.setdefault("integrations", {}).setdefault("email", {})["email"] = args.mail_email
        changes.append(f"email.email → {args.mail_email}")

    # integrations.linkedin
    if args.linkedin:
        val = args.linkedin == "available"
        cfg.setdefault("integrations", {}).setdefault("linkedin", {})["available"] = val
        changes.append(f"linkedin.available → {val}")

    # preferences
    if args.timezone:
        cfg.setdefault("preferences", {})["timezone"] = _validate_timezone(args.timezone)
        changes.append(f"timezone → {args.timezone}")

    if args.eod_time:
        cfg.setdefault("preferences", {})["eod_time"] = _validate_time(args.eod_time, "eod-time")
        changes.append(f"eod_time → {args.eod_time}")

    if args.delivery:
        if args.delivery not in VALID_DELIVERY_METHODS:
            print(f"ERROR: --delivery must be one of {VALID_DELIVERY_METHODS}")
            sys.exit(1)
        cfg.setdefault("preferences", {})["delivery_method"] = args.delivery
        changes.append(f"delivery_method → {args.delivery}")

    if args.work_start:
        cfg.setdefault("preferences", {}).setdefault("work_hours", {})["start"] = _validate_time(args.work_start, "work-start")
        changes.append(f"work_hours.start → {args.work_start}")

    if args.work_end:
        cfg.setdefault("preferences", {}).setdefault("work_hours", {})["end"] = _validate_time(args.work_end, "work-end")
        changes.append(f"work_hours.end → {args.work_end}")

    if args.work_days:
        days = _parse_work_days(args.work_days)
        cfg.setdefault("preferences", {})["work_days"] = days
        day_str = ", ".join(_day_name(d) for d in days)
        changes.append(f"work_days → [{day_str}]")

    if not changes:
        print("No changes specified. Pass flags to update (see --help).")
        sys.exit(0)

    _write_yaml(CONFIG_PATH, cfg)
    print(f"✓ Config updated ({len(changes)} change{'s' if len(changes) != 1 else ''}):")
    for c in changes:
        print(f"  • {c}")


# ── validate ──────────────────────────────────────────────────────────────────

def cmd_validate(args: argparse.Namespace) -> None:
    if not os.path.exists(CONFIG_PATH):
        print("✗ No config found at", CONFIG_PATH)
        print("  Run 'init' to create one.")
        sys.exit(1)

    cfg = _load_yaml(CONFIG_PATH)
    issues: list[str] = []

    # version
    if not cfg.get("version"):
        issues.append("Missing top-level 'version'")

    # installed_at
    if not cfg.get("installed_at"):
        issues.append("Missing 'installed_at' timestamp")

    # integrations
    integrations = cfg.get("integrations")
    if not integrations:
        issues.append("Missing 'integrations' block")
    else:
        # calendar
        cal = integrations.get("calendar", {})
        if not cal.get("provider"):
            issues.append("integrations.calendar.provider is not set")
        elif cal["provider"] not in VALID_CAL_PROVIDERS:
            issues.append(
                f"integrations.calendar.provider '{cal['provider']}' "
                f"is invalid — expected one of {VALID_CAL_PROVIDERS}"
            )

        if not cal.get("email"):
            issues.append("integrations.calendar.email is not set")

        if not cal.get("calendars"):
            issues.append("integrations.calendar.calendars is empty — at least one required")
        else:
            for i, c in enumerate(cal["calendars"]):
                if not c.get("id"):
                    issues.append(f"integrations.calendar.calendars[{i}] missing 'id'")

        # email
        mail = integrations.get("email", {})
        if not mail.get("provider"):
            issues.append("integrations.email.provider is not set")
        elif mail["provider"] not in VALID_MAIL_PROVIDERS:
            issues.append(
                f"integrations.email.provider '{mail['provider']}' "
                f"is invalid — expected one of {VALID_MAIL_PROVIDERS}"
            )

        if not mail.get("email"):
            issues.append("integrations.email.email is not set")

        # cross-check: matching provider families
        cal_prov = cal.get("provider", "")
        mail_prov = mail.get("provider", "")
        if cal_prov and mail_prov:
            cal_is_ms = "microsoft" in cal_prov
            mail_is_ms = "microsoft" in mail_prov
            if cal_is_ms != mail_is_ms:
                issues.append(
                    f"Provider mismatch: calendar is '{cal_prov}' but email is '{mail_prov}'. "
                    "This may work but is unusual — verify this is intentional."
                )

    # preferences
    prefs = cfg.get("preferences")
    if not prefs:
        issues.append("Missing 'preferences' block")
    else:
        tz = prefs.get("timezone")
        if not tz:
            issues.append("preferences.timezone is not set")
        else:
            try:
                ZoneInfo(tz)
            except (KeyError, Exception):
                issues.append(f"preferences.timezone '{tz}' is not a valid IANA timezone")

        for time_field in ("eod_time",):
            val = prefs.get(time_field)
            if val:
                try:
                    datetime.strptime(val, "%H:%M")
                except ValueError:
                    issues.append(f"preferences.{time_field} '{val}' is not valid HH:MM")

        dm = prefs.get("delivery_method")
        if dm and dm not in VALID_DELIVERY_METHODS:
            issues.append(
                f"preferences.delivery_method '{dm}' "
                f"is invalid — expected one of {VALID_DELIVERY_METHODS}"
            )

        wh = prefs.get("work_hours", {})
        for key in ("start", "end"):
            val = wh.get(key)
            if val:
                try:
                    datetime.strptime(val, "%H:%M")
                except ValueError:
                    issues.append(f"preferences.work_hours.{key} '{val}' is not valid HH:MM")

        if wh.get("start") and wh.get("end"):
            try:
                s = datetime.strptime(wh["start"], "%H:%M")
                e = datetime.strptime(wh["end"], "%H:%M")
                if e <= s:
                    issues.append(
                        f"preferences.work_hours.end ({wh['end']}) "
                        f"must be after start ({wh['start']})"
                    )
            except ValueError:
                pass

        wd = prefs.get("work_days", [])
        if not wd:
            issues.append("preferences.work_days is empty")
        else:
            for d in wd:
                if not isinstance(d, int):
                    issues.append(f"preferences.work_days contains non-integer value '{d}' (type: {type(d).__name__})")
                elif d not in VALID_WORK_DAYS:
                    issues.append(f"preferences.work_days contains invalid day {d}")

    # result
    if issues:
        print(f"✗ Validation failed — {len(issues)} issue{'s' if len(issues) != 1 else ''}:")
        for issue in issues:
            print(f"  • {issue}")
        sys.exit(1)
    else:
        print("✓ Config is valid")


# ── CLI wiring ────────────────────────────────────────────────────────────────

def _add_shared_flags(parser: argparse.ArgumentParser) -> None:
    g = parser.add_argument_group("integrations")
    g.add_argument("--cal-provider", metavar="PROVIDER",
                   help=f"Calendar provider: {', '.join(VALID_CAL_PROVIDERS)}")
    g.add_argument("--cal-email", metavar="EMAIL",
                   help="Email address for the calendar integration")
    g.add_argument("--calendars", metavar="IDS",
                   help="Comma-separated calendar IDs or id:name pairs (e.g. 'primary:My Calendar,work')")
    g.add_argument("--mail-provider", metavar="PROVIDER",
                   help=f"Email provider: {', '.join(VALID_MAIL_PROVIDERS)}")
    g.add_argument("--mail-email", metavar="EMAIL",
                   help="Email address for the email integration")
    g.add_argument("--linkedin", choices=["available", "unavailable"],
                   help="LinkedIn integration availability")

    p = parser.add_argument_group("preferences")
    p.add_argument("--timezone", metavar="TZ", help="IANA timezone (e.g. America/New_York)")
    p.add_argument("--eod-time", metavar="HH:MM", help="End-of-day time for digests")
    p.add_argument("--delivery", choices=VALID_DELIVERY_METHODS,
                   help="Delivery method for notifications")
    p.add_argument("--work-start", metavar="HH:MM", help="Work hours start")
    p.add_argument("--work-end", metavar="HH:MM", help="Work hours end")
    p.add_argument("--work-days", metavar="DAYS",
                   help="Comma-separated work days as ints, 1=Mon … 7=Sun")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="Calendar Intelligence — configuration lifecycle manager",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = sub.add_parser("init", help="Create config from CLI flags")
    p_init.add_argument("--force", action="store_true",
                        help="Overwrite existing config")
    _add_shared_flags(p_init)

    # status
    p_status = sub.add_parser("status", help="Show current config")
    p_status.add_argument("--json", action="store_true",
                          help="Output config as JSON")

    # update
    p_update = sub.add_parser("update", help="Update specific config fields")
    _add_shared_flags(p_update)

    # validate
    sub.add_parser("validate", help="Check config is complete and consistent")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "status": cmd_status,
        "update": cmd_update,
        "validate": cmd_validate,
    }

    try:
        dispatch[args.command](args)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    except (ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    except (KeyError, TypeError) as exc:
        print(f"ERROR: Config is malformed — {type(exc).__name__}: {exc}")
        print("  Run 'validate' to check your config, or 'init --force' to recreate.")
        sys.exit(1)


if __name__ == "__main__":
    main()
