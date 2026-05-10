#!/usr/bin/env python3
"""Single run for crontab - check fares, email if deal found."""

import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import asyncio
import os
import re
import smtplib
import subprocess
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from playwright.async_api import async_playwright

BASE_URL = (
    "https://www.alaskaair.com/search/calendar"
    "?O=SEA&D=TPE&A=1&RT=false"
    "&RequestType=Calendar&ShoppingMethod=onlineaward"
    "&int=flightresultsmicrosite%3Aviewby-calendar"
    "&locale=en-us&FareType=Partner+Business&OD="
)

MONTHS = ["2026-10-01", "2026-11-01", "2026-12-01"]
THRESHOLD = 80

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
EMAIL_TO = os.environ.get("EMAIL_TO", GMAIL_USER)


async def check_fares():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        all_fares = []
        for month in MONTHS:
            try:
                await page.goto(BASE_URL + month, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector('button[role="gridcell"]', timeout=30000)
                await page.wait_for_timeout(2000)
                buttons = await page.query_selector_all('button[role="gridcell"]')
                for btn in buttons:
                    label = await btn.get_attribute("aria-label")
                    if not label:
                        continue
                    match = re.search(
                        r"(.+?\d{4})\.\s*Fare:\s*(\d+)k\s*\+\s*\$(\d+)", label
                    )
                    if match:
                        all_fares.append((match.group(1), int(match.group(2)), int(match.group(3))))
            except Exception as e:
                print(f"  Skipped {month}: {e}")
        await browser.close()
        return all_fares


def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = EMAIL_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] Checking {MONTHS[0]} to {MONTHS[-1]}...")

    fares = asyncio.run(check_fares())

    if not fares:
        print("  No fares found.")
        return

    deals = [(d, m, c) for d, m, c in fares if m < THRESHOLD]
    best = min(fares, key=lambda x: x[1])
    print(f"  Scanned {len(fares)} days. Best: {best[0]} = {best[1]}k")

    if deals:
        body = f"SEA -> TPE Partner Business deals below {THRESHOLD}k:\n\n"
        for d, m, c in deals:
            body += f"  {d}: {m}k + ${c}\n"
        body += f"\nBest: {best[0]} = {best[1]}k + ${best[2]}"
        send_email(f"SEA-台湾 < {THRESHOLD}k! ({len(deals)} dates)", body)
        print(f"  🔥 {len(deals)} deals! Email sent.")
    else:
        print(f"  No deals below {THRESHOLD}k.")


def schedule_next_wake():
    """Schedule Mac to wake 1 hour from now."""
    next_wake = datetime.now() + timedelta(hours=1)
    wake_str = next_wake.strftime("%m/%d/%Y %H:%M:%S")
    try:
        subprocess.run(
            ["sudo", "pmset", "schedule", "wake", wake_str],
            capture_output=True,
        )
        print(f"  Next wake scheduled: {wake_str}")
    except Exception as e:
        print(f"  Failed to schedule wake: {e}")


if __name__ == "__main__":
    main()
