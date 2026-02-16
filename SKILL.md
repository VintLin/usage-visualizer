---
name: llm-cost-monitor
description: Track and monitor LLM API usage and costs from OpenClaw sessions. Optional config for external API monitoring.
metadata:
  {
    "openclaw": {
      "emoji": "💰",
      "os": ["darwin", "linux"],
      "requires": { "bins": ["python3"] },
    },
  }
---

# LLM Cost Monitor

Track and monitor LLM API usage and costs from OpenClaw sessions.

## Overview

LLM Cost Monitor helps you track and monitor your LLM API usage and costs. By default, it reads directly from OpenClaw session logs - no configuration required!

**No config needed** - Just install and run!

## Quick Start (No Config Required!)

```bash
# Today's cost report
python3 scripts/report.py

# Yesterday's report
python3 scripts/report.py --period yesterday

# Weekly summary
python3 scripts/report.py --period week

# Check budget
python3 scripts/alert.py --budget 50
```

## With Optional Configuration

Create `config/config.yaml` for advanced features:

```yaml
# Optional: Monitor external APIs in addition to OpenClaw
providers:
  openai:
    keys:
      - sk-your-openai-key
  anthropic:
    keys:
      - your-anthropic-key
    organization_id: your-org-id

# Optional: Budget settings
budget:
  monthly_limit: 100
  alert_threshold: 0.8

# Optional: Notification channels
notify:
  - feishu
  # - telegram
```

## Features

### Default (No Config)
- ✅ Read OpenClaw session logs automatically
- ✅ Daily/weekly/monthly cost reports
- ✅ Cost breakdown by model
- ✅ Cache token tracking
- ✅ Budget alerts (local)

### With Config (Optional)
- ✅ Monitor external APIs (OpenAI, Anthropic)
- ✅ Cross-platform usage aggregation
- ✅ Budget alerts via webhook (Feishu, Telegram, Discord)

## Scripts

| Script | Description |
|--------|-------------|
| `fetch_usage.py` | Fetch usage data (auto-runs for OpenClaw) |
| `report.py` | Generate cost reports |
| `alert.py` | Check budget and send alerts |
| `calc_cost.py` | Cost calculation logic |

## Examples

```bash
# Quick report (no config needed)
python3 scripts/report.py

# JSON output for automation
python3 scripts/report.py --json

# Budget check
python3 scripts/alert.py --budget 50

# Last 7 days
python3 scripts/report.py --period week
```

## Cron Automation

```bash
# Daily report at 9 AM
0 9 * * * python3 /path/to/scripts/report.py
```

## Project Structure

```
llm-cost-monitor/
├── SKILL.md
├── README.md
├── config/
│   └── config.yaml.example  # Optional config
├── scripts/
│   ├── fetch_usage.py    # Fetch from OpenClaw + external APIs
│   ├── calc_cost.py     # Cost calculation
│   ├── store.py         # SQLite storage
│   ├── report.py        # Reports
│   └── alert.py         # Budget alerts
└── examples/
    └── cron.sh
```
