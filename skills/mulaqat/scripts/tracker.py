#!/usr/bin/env python3
"""Mulaqat pipeline tracker.

A small CSV-backed lead tracker for LinkedIn outreach. Standard library only,
Python 3.9+. It never talks to LinkedIn: it records what the user has done and
tells them what is due and how close they are to safe weekly limits.

Usage:
    python3 tracker.py --file mulaqat-pipeline.csv add --name "Sara Khan" --company "Acme"
    python3 tracker.py --file mulaqat-pipeline.csv update --id 1 --stage requested
    python3 tracker.py --file mulaqat-pipeline.csv queue
    python3 tracker.py --file mulaqat-pipeline.csv limits
    python3 tracker.py --file mulaqat-pipeline.csv stale --days 21
    python3 tracker.py --file mulaqat-pipeline.csv report --days 7
    python3 tracker.py --file mulaqat-pipeline.csv list --stage replied
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile
from datetime import date, datetime, timedelta

STAGES = [
    "found",
    "requested",
    "connected",
    "messaged",
    "replied",
    "qualified",
    "booked",
    "won",
]
TERMINAL = {"won", "lost"}
ALL_STAGES = STAGES + ["lost"]

COLUMNS = [
    "id",
    "name",
    "role",
    "company",
    "country",
    "url",
    "service",
    "source",
    "stage",
    "reached",
    "created",
    "requested_on",
    "last_action",
    "next_action",
    "notes",
]

DEFAULT_WEEKLY_CAP = 80
SMALL_ACCOUNT_WEEKLY_CAP = 30
DAILY_CAP = 20
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

Lead = dict[str, str]


class TrackerError(Exception):
    """A user-facing error: bad input or an unknown lead."""


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise TrackerError(f"invalid date {value!r}, use YYYY-MM-DD") from exc


def safe_cell(value: str | None) -> str:
    """Neutralise spreadsheet formula injection in free-text cells."""
    text = (value or "").strip()
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return text


def stage_index(stage: str) -> int:
    return STAGES.index(stage) if stage in STAGES else -1


def load(path: str) -> list[Lead]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{col: row.get(col, "") or "" for col in COLUMNS} for row in reader]


def save(path: str, leads: list[Lead]) -> None:
    """Write atomically so an interrupted run never corrupts the file."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".mulaqat-", suffix=".csv")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(leads)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def find(leads: list[Lead], lead_id: str) -> Lead:
    for lead in leads:
        if lead["id"] == str(lead_id):
            return lead
    raise TrackerError(f"no lead with id {lead_id}")


def add_lead(leads: list[Lead], today: date, **fields: str | None) -> Lead:
    name = safe_cell(fields.get("name"))
    if not name:
        raise TrackerError("--name is required")
    next_id = max((int(l["id"]) for l in leads if l["id"].isdigit()), default=0) + 1
    lead = {col: "" for col in COLUMNS}
    for key in ("role", "company", "country", "url", "service", "source"):
        lead[key] = safe_cell(fields.get(key))
    lead.update(
        id=str(next_id),
        name=name,
        stage="found",
        reached="found",
        created=today.isoformat(),
        last_action=today.isoformat(),
    )
    leads.append(lead)
    return lead


def update_lead(
    leads: list[Lead],
    lead_id: str,
    today: date,
    stage: str | None = None,
    note: str | None = None,
    next_action: str | None = None,
) -> Lead:
    lead = find(leads, lead_id)
    if stage:
        if stage not in ALL_STAGES:
            raise TrackerError(
                f"unknown stage {stage!r}; use one of {', '.join(ALL_STAGES)}"
            )
        lead["stage"] = stage
        if stage_index(stage) > stage_index(lead["reached"]):
            lead["reached"] = stage
        if stage == "requested" and not lead["requested_on"]:
            lead["requested_on"] = today.isoformat()
    if note:
        entry = f"{today.isoformat()}: {safe_cell(note)}"
        lead["notes"] = f"{lead['notes']} | {entry}" if lead["notes"] else entry
    if next_action is not None:
        lead["next_action"] = parse_date(next_action).isoformat() if next_action else ""
    if lead["stage"] in TERMINAL:
        lead["next_action"] = ""  # won/lost leads never come back into the queue
    lead["last_action"] = today.isoformat()
    return lead


def due(leads: list[Lead], on: date) -> list[Lead]:
    result = []
    for lead in leads:
        if lead["stage"] in TERMINAL or not lead["next_action"]:
            continue
        if parse_date(lead["next_action"]) <= on:
            result.append(lead)
    return sorted(result, key=lambda l: (l["next_action"], int(l["id"])))


def requests_in_window(leads: list[Lead], today: date, days: int = 7) -> int:
    start = today - timedelta(days=days - 1)
    count = 0
    for lead in leads:
        if lead["requested_on"]:
            sent = parse_date(lead["requested_on"])
            if start <= sent <= today:
                count += 1
    return count


def limits(
    leads: list[Lead], today: date, small_account: bool = False
) -> dict[str, int]:
    cap = SMALL_ACCOUNT_WEEKLY_CAP if small_account else DEFAULT_WEEKLY_CAP
    sent_week = requests_in_window(leads, today, 7)
    sent_today = requests_in_window(leads, today, 1)
    remaining_week = max(cap - sent_week, 0)
    remaining_today = max(min(DAILY_CAP - sent_today, remaining_week), 0)
    return {
        "weekly_cap": cap,
        "sent_last_7_days": sent_week,
        "remaining_this_week": remaining_week,
        "sent_today": sent_today,
        "remaining_today": remaining_today,
    }


def stale(leads: list[Lead], today: date, days: int = 21) -> list[Lead]:
    cutoff = today - timedelta(days=days)
    return [
        l
        for l in leads
        if l["stage"] == "requested"
        and l["requested_on"]
        and parse_date(l["requested_on"]) < cutoff
    ]


def _rate(numerator: int, denominator: int) -> float | None:
    return round(100.0 * numerator / denominator, 1) if denominator else None


def report(leads: list[Lead], today: date, days: int = 7) -> dict[str, object]:
    """Funnel numbers for leads requested in the window, plus totals by stage."""
    start = today - timedelta(days=days - 1)
    cohort = [
        l
        for l in leads
        if l["requested_on"] and start <= parse_date(l["requested_on"]) <= today
    ]

    def reached(group: list[Lead], stage: str) -> int:
        return sum(1 for l in group if stage_index(l["reached"]) >= stage_index(stage))

    requested = len(cohort)
    connected = reached(cohort, "connected")
    messaged = reached(cohort, "messaged")
    replied = reached(cohort, "replied")
    by_stage = {s: sum(1 for l in leads if l["stage"] == s) for s in ALL_STAGES}
    return {
        "window_days": days,
        "requested": requested,
        "connected": connected,
        "acceptance_rate_pct": _rate(connected, requested),
        "messaged": messaged,
        "replied": replied,
        "reply_rate_pct": _rate(replied, messaged),
        "booked": reached(cohort, "booked"),
        "won": reached(cohort, "won"),
        "all_leads_by_stage": by_stage,
    }


def _print_leads(leads: list[Lead]) -> None:
    if not leads:
        print("(none)")
        return
    for l in leads:
        bits = [f"#{l['id']}", l["name"]]
        if l["company"]:
            bits.append(f"@ {l['company']}")
        bits.append(f"[{l['stage']}]")
        if l["service"]:
            bits.append(f"service={l['service']}")
        if l["next_action"]:
            bits.append(f"next={l['next_action']}")
        print("  ".join(bits))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mulaqat LinkedIn pipeline tracker")
    parser.add_argument(
        "--file", default="mulaqat-pipeline.csv", help="tracker CSV path"
    )
    parser.add_argument("--today", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a lead")
    p_add.add_argument("--name", required=True)
    for opt in ("role", "company", "country", "url", "service", "source"):
        p_add.add_argument(f"--{opt}")

    p_up = sub.add_parser("update", help="change stage, add a note, set next action")
    p_up.add_argument("--id", required=True)
    p_up.add_argument("--stage", choices=ALL_STAGES)
    p_up.add_argument("--note")
    p_up.add_argument(
        "--next", dest="next_action", help="YYYY-MM-DD, or empty to clear"
    )

    p_q = sub.add_parser("queue", help="actions due")
    p_q.add_argument("--date")

    p_l = sub.add_parser("limits", help="connection requests vs safe caps")
    p_l.add_argument(
        "--small-account", action="store_true", help="account under ~500 connections"
    )

    p_s = sub.add_parser("stale", help="requests pending too long")
    p_s.add_argument("--days", type=int, default=21)

    p_r = sub.add_parser("report", help="funnel numbers")
    p_r.add_argument("--days", type=int, default=7)

    p_ls = sub.add_parser("list", help="show leads")
    p_ls.add_argument("--stage", choices=ALL_STAGES)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        # The user's local calendar day: follow-ups and limits are counted in it.
        today = (
            parse_date(args.today) if args.today else datetime.now().astimezone().date()
        )
        leads = load(args.file)

        if args.command == "add":
            lead = add_lead(
                leads,
                today,
                name=args.name,
                role=args.role,
                company=args.company,
                country=args.country,
                url=args.url,
                service=args.service,
                source=args.source,
            )
            save(args.file, leads)
            print(f"added #{lead['id']} {lead['name']}")
        elif args.command == "update":
            lead = update_lead(
                leads, args.id, today, args.stage, args.note, args.next_action
            )
            save(args.file, leads)
            print(f"updated #{lead['id']} {lead['name']} -> {lead['stage']}")
        elif args.command == "queue":
            on = parse_date(args.date) if args.date else today
            print(f"Due on or before {on.isoformat()}:")
            _print_leads(due(leads, on))
        elif args.command == "limits":
            for key, value in limits(leads, today, args.small_account).items():
                print(f"{key}: {value}")
        elif args.command == "stale":
            print(f"Requests pending more than {args.days} days (withdraw candidates):")
            _print_leads(stale(leads, today, args.days))
        elif args.command == "report":
            for key, value in report(leads, today, args.days).items():
                print(f"{key}: {value}")
        elif args.command == "list":
            chosen = [l for l in leads if not args.stage or l["stage"] == args.stage]
            _print_leads(chosen)
    except TrackerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
