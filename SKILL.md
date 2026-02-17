---
name: llm-cost-monitor
description: Track LLM API usage and costs from OpenClaw sessions with SQLite persistence, budget alerts, and visual PPT-style reports. No config required.
metadata: {"openclaw":{"emoji":"💰","requires":{"bins":["python3"]}}}
---

# LLM Cost Monitor

Track and monitor LLM API usage and costs from OpenClaw sessions with SQLite persistence, budget alerts, and high-resolution visual reports.

## ✨ Features

- **Zero Config** - Automatically detects OpenClaw and Clawdbot session logs.
- **Accurate Tracking** - Supports real cost data and manual calculation with latest pricing.
- **Smart Analytics** - Tracks Anthropic prompt caching (read/write) and calculates **Savings**.
- **PPT-Style Reports** - Generates high-res horizontal reports with 30D SVG trend lines and model efficiency metrics.
- **Idempotent Storage** - SQLite backend ensures data consistency even after full re-scans.
- **Budget Guard** - Built-in alerting system for daily, weekly, and monthly spending.

## 🚀 Quick Start

```bash
# Clone or install to your OpenClaw skills directory
git clone https://github.com/VintLin/llm-cost-monitor.git
cd llm-cost-monitor

# Install dependencies
pip install -r requirements.txt

# Sync all historical data (First run)
python3 scripts/fetch_usage.py --full

# Generate your first visual report
python3 scripts/generate_report_image.py --today
```

## ⚡️ Usage

**To view your usage report:**
Simply run the image generator. It automatically fetches today's data before rendering.

```bash
# From the skill directory:
python3 scripts/generate_report_image.py --today

# Or for a weekly view:
python3 scripts/generate_report_image.py --period week
```

The script will:
1. Fetch latest usage from session logs.
2. Calculate costs and cache savings.
3. Generate a PPT-style horizontal HTML report.
4. Convert to a cropped PNG saved to your workspace (e.g., `~/llm-cost-report.png`).

### Output Modes

| Scenario | Command | Output |
|----------|---------|--------|
| **Visual (Default)** | `generate_report_image.py` | 📊 High-res PNG → Workspace |
| Text Summary | `report.py` | 📝 Markdown Text → Console |
| Raw Data | `report.py --json` | 📋 JSON → Console |

## 🔧 Available Commands

### 1. Data Fetching
```bash
python3 scripts/fetch_usage.py --today       # Incremental sync (Today)
python3 scripts/fetch_usage.py --last-days 7 # Sync last week
python3 scripts/fetch_usage.py --full        # Full historical re-scan (Idempotent)
```

### 2. Reporting
```bash
python3 scripts/report.py --period today     # Today's text report
python3 scripts/report.py --period week      # Weekly text summary
python3 scripts/report.py --json             # Output raw JSON for integrations
```

### 3. Visualizations
```bash
python3 scripts/generate_report_image.py --today       # Today's PPT card
python3 scripts/generate_report_image.py --period week # Weekly PPT card
```

### 4. Budget Alerts
```bash
python3 scripts/alert.py --budget-usd 10 --period today  # Exit code 2 if exceeded
python3 scripts/alert.py --budget-usd 50 --mode warn     # Log warning only
```

## 📊 Data Schema (SQLite)

| Field | Description |
|-------|-------------|
| `date` | ISO Date (YYYY-MM-DD) |
| `provider` | Model provider (Anthropic, OpenAI, Gemini, etc.) |
| `model` | Specific model name |
| `input_tokens` | Prompt tokens consumed |
| `output_tokens` | Completion tokens generated |
| `cache_read_tokens` | Tokens retrieved from cache (Savings applied) |
| `cost` | Total calculated cost in USD |
| `savings` | Estimated money saved via prompt caching |

## 📁 Project Structure

```
llm-cost-monitor/
├── assets/                     # Versioned screenshots and assets
├── config/                     # Configuration templates
├── examples/                   # Usage examples and sample reports
├── scripts/
│   ├── fetch_usage.py          # Log parser and sync engine
│   ├── calc_cost.py            # Pricing logic and savings calculator
│   ├── store.py                # SQLite database interface
│   ├── report.py               # Text/JSON reporter
│   ├── html_report.py          # PPT-style HTML template engine
│   ├── generate_report_image.py # Image renderer (html2image + PIL)
│   ├── alert.py                # Budget monitor
│   └── notify.py               # Notification dispatcher
├── SKILL.md                    # Skill definition
└── README.md                   # Project documentation
```

## 🤖 OpenClaw Integration

### Automated Daily Report (Cron)
Add this to your OpenClaw cron configuration:

```json
{
  "name": "daily-cost-report",
  "schedule": {"kind": "cron", "expr": "0 23 * * *", "tz": "Asia/Shanghai"},
  "payload": {
    "kind": "agentTurn", 
    "message": "Run generate_report_image.py --today and send the resulting PNG from my workspace."
  },
  "sessionTarget": "isolated"
}
```

## 📝 Requirements

- Python 3.8+
- `html2image` (Browser-based rendering)
- `Pillow` (Smart cropping and image processing)
- `PyYAML` (Config parsing)

## 📄 License

MIT
