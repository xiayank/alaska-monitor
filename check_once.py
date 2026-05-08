#!/usr/bin/env python3
"""Single check for GitHub Actions - outputs results."""

import asyncio
import os
import re
from datetime import date
from dateutil.relativedelta import relativedelta
from playwright.async_api import async_playwright

BASE_URL = (
    "https://www.alaskaair.com/search/calendar"
    "?O=SEA&D=TPE&A=1&RT=false"
    "&RequestType=Calendar&ShoppingMethod=onlineaward"
    "&int=flightresultsmicrosite%3Aviewby-calendar"
    "&locale=en-us&FareType=Partner+Business&OD="
)

NUM_MONTHS = 7
THRESHOLD = int(os.environ.get("THRESHOLD", "80"))


def get_months_to_check():
    today = date.today()
    first_of_next = today.replace(day=1) + relativedelta(months=1)
    return [
        (first_of_next + relativedelta(months=i)).strftime("%Y-%m-01")
        for i in range(NUM_MONTHS)
    ]


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
        months = get_months_to_check()
        for month in months:
            url = BASE_URL + month
            print(f"Checking {month[:7]}...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)

            buttons = await page.query_selector_all('button[role="gridcell"]')
            for btn in buttons:
                label = await btn.get_attribute("aria-label")
                if not label:
                    continue
                match = re.search(
                    r"(.+?\d{4})\.\s*Fare:\s*(\d+)k\s*\+\s*\$(\d+)", label
                )
                if match:
                    date_str = match.group(1)
                    miles = int(match.group(2))
                    cash = int(match.group(3))
                    all_fares.append((date_str, miles, cash))

        await browser.close()
        return all_fares


def main():
    fares = asyncio.run(check_fares())

    if not fares:
        print("No fares found.")
        set_output("has_deals", "false")
        return

    deals = [(d, m, c) for d, m, c in fares if m < THRESHOLD]
    best = min(fares, key=lambda x: x[1])

    print(f"\nScanned {len(fares)} days. Best: {best[0]} = {best[1]}k + ${best[2]}")

    if deals:
        print(f"\nDEALS FOUND ({len(deals)}):")
        msg_lines = [f"SEA->TPE Partner Business deals below {THRESHOLD}k:\n"]
        for d, m, c in deals:
            line = f"  {d}: {m}k + ${c}"
            print(line)
            msg_lines.append(line)
        msg_lines.append(f"\nBest: {best[0]} = {best[1]}k + ${best[2]}")
        set_output("has_deals", "true")
        set_output("message", "\n".join(msg_lines))
    else:
        print(f"No deals below {THRESHOLD}k.")
        set_output("has_deals", "false")


def set_output(name, value):
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            if "\n" in value:
                f.write(f"{name}<<EOF\n{value}\nEOF\n")
            else:
                f.write(f"{name}={value}\n")


if __name__ == "__main__":
    main()
