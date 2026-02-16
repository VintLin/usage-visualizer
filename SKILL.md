---
name: llm-cost-monitor
description: Track and monitor LLM API usage and costs across multiple providers (OpenAI, Anthropic, Gemini). Features include cost calculation, budget alerts, and usage reports.
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

Track and monitor LLM API usage and costs across multiple providers.

## Overview

LLM Cost Monitor is a lightweight, non-invasive tool that helps you track and monitor your LLM API usage and costs across multiple providers (OpenAI, Anthropic, Gemini). It fetches usage data directly from provider APIs, calculates costs using up-to-date pricing, and provides budget alerts.

## Use Cases

- **Track API spending** across multiple providers and API keys
- **Budget alerts** - get notified when usage exceeds thresholds
- **Usage reports** - daily, weekly, monthly cost breakdowns by model
- **Cost optimization** - identify expensive models and usage patterns

## Quick Start

### 1. Configure API Keys

Edit `config/config.yaml`:

```yaml
providers:
  openai:
    keys:
      - sk-your-openai-key-here
  anthropic:
    keys:
      - your-anthropic-key-here
    organization_id: your-org-id

budget:
  monthly_limit: 100  # USD
  alert_threshold: 0.8  # Alert at 80% of budget
  notify_channels:
    - feishu  # or telegram, discord

storage:
  path: ~/.llm-cost-monitor
```

### 2. Fetch Usage

```bash
# Fetch today's usage
python3 scripts/fetch_usage.py --today

# Fetch usage for a specific date
python3 scripts/fetch_usage.py --date 2026-02-16

# Fetch last 7 days
python3 scripts/fetch_usage.py --last-days 7
```

### 3. View Reports

```bash
# Today's cost report
python3 scripts/report.py --today

# Weekly report
python3 scripts/report.py --week

# Monthly report
python3 scripts/report.py --month

# JSON output for automation
python3 scripts/report.py --today --json
```

### 4. Check Budget

```bash
# Check if within budget (exit code 0 if OK, 2 if exceeded)
python3 scripts/alert.py --budget 100

# Warn but don't fail
python3 scripts/alert.py --budget 100 --mode warn
```

## Features

### Supported Providers

| Provider | Models Supported | Usage API |
|----------|-----------------|-----------|
| OpenAI | GPT-4o, GPT-4, GPT-3.5, etc. | ✅ |
| Anthropic | Claude 4, Claude 3.5, etc. | ✅ |
| Gemini | Gemini 1.5, Gemini 2.0 | Soon |

### Cost Calculation

- **Base cost**: (input_tokens × input_price) + (output_tokens × output_price)
- **Cache discount**: For Anthropic prompt caching (90% off for cache reads)
- **Tiered pricing**: Automatic detection for >128K token context

### Storage

- Local SQLite database at `~/.llm-cost-monitor/usage.db`
- All data stays on your machine
- No telemetry or cloud sync

### Alerts

Supported notification channels:
- Feishu
- Telegram
- Discord
- Email (via webhook)

## Project Structure

```
llm-cost-monitor/
├── SKILL.md              # This file
├── README.md             # Detailed documentation
├── config/
│   └── config.yaml       # API keys and settings
├── scripts/
│   ├── fetch_usage.py   # Fetch usage from providers
│   ├── calc_cost.py     # Cost calculation logic
│   ├── store.py         # SQLite storage
│   ├── report.py        # Generate reports
│   └── alert.py         # Budget alerts
├── data/
│   └── model_prices.json # Model pricing data
└── examples/
    └── cron_example.sh   # Cron job examples
```

## Cron Automation

Add to your HEARTBEAT.md or cron:

```bash
# Run daily at 11 PM
0 23 * * * cd /path/to/llm-cost-monitor && python3 scripts/fetch_usage.py --yesterday
0 23 * * * cd /path/to/llm-cost-monitor && python3 scripts/alert.py --budget 100
```

## Pricing Data

Pricing is updated from LiteLLM's model_prices_and_context_window.json.
Run `python3 scripts/update_pricing.py` to sync latest prices.

## License

MIT
