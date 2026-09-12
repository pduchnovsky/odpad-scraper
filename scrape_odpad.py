#!/usr/bin/env python3
"""Fetch a waste-collection schedule and publish it as an ICS calendar."""

import re
import uuid
from datetime import UTC, date, datetime, timedelta
from os import environ, replace
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

SOURCE_URL = environ["ODPAD_URL"].strip()
if not SOURCE_URL:
    raise RuntimeError("ODPAD_URL must not be empty")

OUTPUT_PATH = Path(environ.get("ODPAD_OUTPUT", "/data/odvoz-odpadu.ics"))

MONTHS = {
    "január": 1,
    "február": 2,
    "marec": 3,
    "apríl": 4,
    "máj": 5,
    "jún": 6,
    "júl": 7,
    "august": 8,
    "september": 9,
    "október": 10,
    "november": 11,
    "december": 12,
}

CATEGORIES = {
    "PL": "Plasty",
    "PA": "Papier",
    "SK": "Sklo",
    "KZ": "Komunál",
}

DATE_PATTERN = re.compile(
    r"(?P<day>\d{1,2})\.\s*(?P<month>[A-Za-zÁ-Žá-ž]+)\s*(?P<year>\d{4})"
)
CATEGORY_PATTERN = re.compile(
    r"\[(?P<code>PL|PA|SK|KZ)\]\s*"
    r"(?P<name>Plasty|Papier|Sklo|Komunál)",
    re.IGNORECASE,
)


def fetch_text() -> str:
    parsed_url = urlparse(SOURCE_URL)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("ODPAD_URL must be a valid HTTP(S) URL")

    response = requests.get(
        SOURCE_URL,
        headers={"User-Agent": "odpad-scraper/1.0"},
        timeout=(10, 30),
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser").get_text(separator="\n")


def parse_dates(text: str) -> dict[str, list[date]]:
    markers = list(CATEGORY_PATTERN.finditer(text))
    schedule = {name: [] for name in CATEGORIES.values()}

    for index, marker in enumerate(markers):
        code = marker.group("code").upper()
        name = CATEGORIES[code]
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        block = text[marker.end():end]

        dates = set()
        for match in DATE_PATTERN.finditer(block):
            month = MONTHS.get(match.group("month").lower())
            if month is None:
                continue
            dates.add(
                date(
                    int(match.group("year")),
                    month,
                    int(match.group("day")),
                )
            )
        schedule[name].extend(sorted(dates))

    return schedule


def escape_ics_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")


UID_LINE = re.compile(r"^UID:(?P<uid>.+)$", re.MULTILINE)
DTSTAMP_LINE = re.compile(r"^DTSTAMP:(?P<value>.+)$", re.MULTILINE)


def read_previous_timestamps(path: Path) -> dict[str, str]:
    """Map UID -> DTSTAMP from an existing ICS so unchanged events keep it."""
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}

    timestamps: dict[str, str] = {}
    for block in content.split("BEGIN:VEVENT")[1:]:
        uid_match = UID_LINE.search(block)
        dtstamp_match = DTSTAMP_LINE.search(block)
        if uid_match and dtstamp_match:
            timestamps[uid_match.group("uid").strip()] = dtstamp_match.group("value").strip()
    return timestamps


def build_ics(
    schedule: dict[str, list[date]], previous_timestamps: dict[str, str]
) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Odvoz odpadu//SK",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Odvoz odpadu",
        "X-WR-TIMEZONE:Europe/Bratislava",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]

    for category, dates in schedule.items():
        for collection_date in dates:
            start = collection_date.strftime("%Y%m%d")
            end = (collection_date + timedelta(days=1)).strftime("%Y%m%d")
            uid = f"{uuid.uuid5(uuid.NAMESPACE_URL, f'{category}-{start}-odpad-calendar')}@odpad-calendar"
            # Reuse the event's previous DTSTAMP so unchanged events don't
            # produce a diff on every run; only new events get "now".
            timestamp = previous_timestamps.get(
                uid, datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            )
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{timestamp}",
                    f"DTSTART;VALUE=DATE:{start}",
                    f"DTEND;VALUE=DATE:{end}",
                    f"SUMMARY:{escape_ics_text(category)}",
                    "CATEGORIES:Odpad",
                    "TRANSP:TRANSPARENT",
                    "BEGIN:VALARM",
                    "ACTION:DISPLAY",
                    "DESCRIPTION:Zajtra je odvoz odpadu",
                    "TRIGGER:-P1DT0H0M0S",
                    "END:VALARM",
                    "END:VEVENT",
                ]
            )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def write_ics(schedule: dict[str, list[date]]) -> int:
    missing = [name for name, dates in schedule.items() if not dates]
    if missing:
        raise ValueError(f"Missing or empty categories: {', '.join(missing)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    previous_timestamps = read_previous_timestamps(OUTPUT_PATH)
    content = build_ics(schedule, previous_timestamps)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=OUTPUT_PATH.parent,
            prefix=f".{OUTPUT_PATH.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
        replace(temporary_path, OUTPUT_PATH)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return sum(len(dates) for dates in schedule.values())


def main() -> None:
    schedule = parse_dates(fetch_text())
    total = write_ics(schedule)
    print(f"OK - zapisanych {total} terminov do {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
