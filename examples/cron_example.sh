#!/bin/bash
# LLM Cost Monitor - Cron Examples
# Add these to your crontab (crontab -e)

# Change to the project directory
PROJECT_DIR="/path/to/llm-cost-monitor"
cd "$PROJECT_DIR"

# ============================================
# Daily Usage Fetch
# ============================================

# Fetch yesterday's usage every day at 11 PM
0 23 * * * cd "$PROJECT_DIR" && python3 scripts/fetch_usage.py --yesterday >> /tmp/llm-cost.log 2>&1

# ============================================
# Budget Alerts
# ============================================

# Check budget every day at 11:30 PM
# Exit code 2 = exceeded, 1 = warning, 0 = OK
0 23 * * * cd "$PROJECT_DIR" && python3 scripts/alert.py --budget 100 >> /tmp/llm-cost-alert.log 2>&1

# ============================================
# Weekly Reports
# ============================================

# Send weekly report every Monday at 9 AM
0 9 * * 1 cd "$PROJECT_DIR" && python3 scripts/report.py --week

# ============================================
# Alternative: Using OpenClaw Cron
# ============================================

# If using OpenClaw's cron feature, add to your cron jobs:

# {
#   "name": "llm-cost-daily-fetch",
#   "schedule": {"kind": "cron", "expr": "0 23 * * *"},
#   "payload": {"kind": "agentTurn", "message": "Run llm-cost-monitor fetch_usage.py --yesterday"},
#   "sessionTarget": "isolated"
# }

# ============================================
# Note: Make sure to set up your config.yaml
# before running cron jobs!
# ============================================
