#!/bin/bash
exec >> /Users/yxiaamz/Documents/Agent/alaska-monitor/cron.log 2>&1
echo ""
echo "=========================================="
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
export HOME=/Users/yxiaamz
export PATH="/Users/yxiaamz/.local/share/mise/installs/python/3.12.11/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export GMAIL_USER="yan.xia.cs@gmail.com"
export GMAIL_APP_PASSWORD="iweybczcxsqelhtu"
export EMAIL_TO="yan.xia.cs@gmail.com"
cd /Users/yxiaamz/Documents/Agent/alaska-monitor

# Wait for Wi-Fi after wake (max 30 seconds)
for i in $(seq 1 6); do
  if ping -c 1 -t 2 google.com &>/dev/null; then
    break
  fi
  echo "  Waiting for network... ($i)"
  sleep 5
done

python monitor_cron.py
echo "------------------------------------------"
