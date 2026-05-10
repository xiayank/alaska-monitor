# Alaska Airlines Award Monitor

## What it does
Monitors Alaska Airlines award calendar for SEA→TPE (Seattle to Taipei) Partner Business class tickets.
Sends email notification when any date drops below the mileage threshold.

## Configuration
- **Route:** SEA → TPE (Partner Business)
- **Months monitored:** Oct, Nov, Dec 2026
- **Threshold:** < 80k miles (currently lowest available is 175k)
- **Check frequency:** Every hour (via crontab + pmset wake)
- **Notification:** Email to yan.xia.cs@gmail.com
- **Runs on:** Local Mac (plugged in, lid can be closed)

## How it works
1. Uses Playwright (headless Chromium) to load Alaska Air's calendar page
2. Parses `aria-label` attribute from `button[role="gridcell"]` elements
3. Format: `"Nov 1, 2026. Fare: 175k + $19"`
4. If any fare < threshold, sends email via Gmail SMTP
5. After each run, schedules next Mac wake via `pmset schedule wake`

## Sleep/Wake behavior
- Mac can be closed (lid down) as long as it's **plugged into power**
- Script schedules next wake 1 hour later using `sudo pmset schedule wake`
- Chain: sleep → pmset wakes Mac → crontab runs script → script schedules next wake → Mac sleeps again
- Requires sudoers entry: `yxiaamz ALL=(ALL) NOPASSWD: /usr/bin/pmset` in `/etc/sudoers.d/pmset`

## Files
- `monitor_cron.py` — Single run script for crontab (no loop), schedules next wake
- `monitor.py` — Loop version for manual background running (alternative)
- `check_once.py` — GitHub Actions version (doesn't work due to IP blocking)
- `requirements.txt` — Python dependencies
- `com.alaska.monitor.plist` — launchd alternative (not currently used)

## Dependencies
```bash
pip install playwright python-dateutil
playwright install chromium
```

## Crontab entry
```
0 * * * * GMAIL_USER="yan.xia.cs@gmail.com" GMAIL_APP_PASSWORD="<app-password>" EMAIL_TO="yan.xia.cs@gmail.com" /Users/yxiaamz/.local/share/mise/installs/python/3.12.11/bin/python /Users/yxiaamz/Documents/Agent/alaska-monitor/monitor_cron.py >> /Users/yxiaamz/Documents/Agent/alaska-monitor/cron.log 2>&1
```

## Management

### Check if job is running
```bash
crontab -l | grep alaska
```
If it shows the entry, the job is active.

### Check scheduled wakes
```bash
sudo pmset -g sched
```

### View logs (see recent checks)
```bash
cat /Users/yxiaamz/Documents/Agent/alaska-monitor/cron.log
tail -20 /Users/yxiaamz/Documents/Agent/alaska-monitor/cron.log
```

### Stop the job
```bash
crontab -l | grep -v alaska | crontab -
```

### Start the job (re-add to crontab)
```bash
(crontab -l 2>/dev/null; echo '0 * * * * GMAIL_USER="yan.xia.cs@gmail.com" GMAIL_APP_PASSWORD="<app-password>" EMAIL_TO="yan.xia.cs@gmail.com" /Users/yxiaamz/.local/share/mise/installs/python/3.12.11/bin/python /Users/yxiaamz/Documents/Agent/alaska-monitor/monitor_cron.py >> /Users/yxiaamz/Documents/Agent/alaska-monitor/cron.log 2>&1') | crontab -
```

### Manual test (run once immediately)
```bash
GMAIL_USER="yan.xia.cs@gmail.com" GMAIL_APP_PASSWORD="<app-password>" EMAIL_TO="yan.xia.cs@gmail.com" python /Users/yxiaamz/Documents/Agent/alaska-monitor/monitor_cron.py
```

### Clear logs
```bash
> /Users/yxiaamz/Documents/Agent/alaska-monitor/cron.log
```

## Why not Cloud Desktop?
Amazon Acceptable Use Policy allows only "limited personal use" of company resources.
Running a 24/7 automated scraper for personal flight monitoring is not "limited" — it uses
continuous CPU/bandwidth and sends traffic from Amazon IPs to external commercial sites.
Stick to local Mac to avoid compliance issues.

## Why not GitHub Actions?
Alaska Air blocks datacenter IPs. The Playwright browser times out when running from
GitHub's Ubuntu runners. Must run from a residential IP (home network).

## Notes
- Gmail App Password required (not regular password): https://myaccount.google.com/apppasswords
- Alaska Air page uses Svelte, data is in `aria-label` of `button[role="gridcell"]`
- No JSON API available; must use browser automation
- sudoers file for pmset: `/etc/sudoers.d/pmset`

## GitHub repo (non-functional, kept for reference)
https://github.com/xiayank/alaska-monitor

## To modify
- Change threshold: edit `THRESHOLD` in `monitor_cron.py`
- Change months: edit `MONTHS` list in `monitor_cron.py`
- Change route: edit `BASE_URL` parameters (O=origin, D=destination)
- Change frequency: edit crontab schedule (e.g., `*/30 * * * *` for every 30 min)
- Email subject contains "台湾" for easy filtering
