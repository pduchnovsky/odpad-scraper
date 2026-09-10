#!/usr/bin/env python3
"""
Stiahne harmonogram odvozu odpadu z trstany.sk a vygeneruje .ics.
Parsuje podľa textových značiek "[PL] Plasty", "[PA] Papier", "[SK] Sklo",
"[KZ] Komunál" - robustné voči zmenám HTML štruktúry, keďže sa nespolieha
na CSS triedy.
"""

import re
import uuid
from datetime import datetime, timedelta
from os import environ

import requests
from bs4 import BeautifulSoup

URL = environ.get("ODPAD_URL")
OUTPUT = "/data/odvoz-odpadu.ics"

MONTHS = {
    "január": 1, "február": 2, "marec": 3, "apríl": 4, "máj": 5, "jún": 6,
    "júl": 7, "august": 8, "september": 9, "október": 10, "november": 11,
    "december": 12,
}

CATEGORIES = {
    "Plasty": "PL",
    "Papier": "PA",
    "Sklo": "SK",
    "Komunál": "KZ",
}

DATE_RE = re.compile(r"(\d{1,2})\.\s*([A-Za-zÁ-Žá-ž]+)\s*(\d{4})")


def fetch_text() -> str:
    resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return soup.get_text(separator="\n")


def parse_dates(text: str) -> dict:
    result = {}
    for name, code in CATEGORIES.items():
        marker = re.search(rf"\[{code}\]\s*{name}", text)
        if not marker:
            continue
        # Zober blok textu od značky po prvý výskyt "PATRIA SEM"
        start = marker.end()
        end_match = re.search(r"PATRIA SEM", text[start:])
        block = text[start:start + end_match.start()] if end_match else text[start:start + 3000]
        dates = []
        for d, month_name, y in DATE_RE.findall(block):
            month = MONTHS.get(month_name.lower())
            if not month:
                continue
            dates.append(datetime(int(y), month, int(d)))
        result[name] = dates
    return result


def build_ics(schedule: dict) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Trstany//Odvoz odpadu//SK",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Odvoz odpadu - Trsťany",
        "X-WR-TIMEZONE:Europe/Bratislava",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for name, dates in schedule.items():
        for d in dates:
            start = d.strftime("%Y%m%d")
            end = (d + timedelta(days=1)).strftime("%Y%m%d")
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uuid.uuid5(uuid.NAMESPACE_DNS, f'{name}-{start}-trstany')}@trstany-odpad",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{start}",
                f"DTEND;VALUE=DATE:{end}",
                f"SUMMARY:Odvoz odpadu - {name}",
                "TRANSP:TRANSPARENT",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                "DESCRIPTION:Zajtra je odvoz odpadu",
                "TRIGGER:-P1DT0H0M0S",
                "END:VALARM",
                "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def main():
    text = fetch_text()
    schedule = parse_dates(text)
    ics = build_ics(schedule)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(ics)
    total = sum(len(v) for v in schedule.values())
    print(f"OK - zapisanych {total} terminov do {OUTPUT}")


if __name__ == "__main__":
    main()
