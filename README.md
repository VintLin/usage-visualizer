# LLM Cost Monitor

Track and monitor LLM API usage and costs from OpenClaw sessions with SQLite persistence, budget alerts, and visual HTML reports.

![AI Usage Report](examples/report-sample.png)

## ✨ Features

- **No config required!** - Just install and run
- **Automatic OpenClaw detection** - Reads session logs automatically
- **Accurate cost tracking** - Uses real cost data when available, calculates otherwise
- **Cache token support** - Tracks Anthropic prompt caching (read/write)
- **SQLite persistence** - Historical data stored locally
- **Daily/weekly/monthly reports** - Multiple time periods
- **Budget alerts** - Monitor your spending with exit codes
- **Visual HTML reports** - Generate images for sharing
- **Multi-provider support** - Anthropic, OpenAI, Gemini, MiniMax

## 🚀 Quick Start

```bash
# Clone or install
git clone https://github.com/VintLin/llm-cost-monitor.git
cd llm-cost-monitor

# Install dependencies
pip install -r requirements.txt

# Run - generates image report by default
python3 scripts/html_report.py
```

## ⚡️ Usage

**When user asks about usage:**
1. Run `fetch_usage.py` to fetch latest session data
2. Generate image report with `html_report.py`
3. Send to user

```bash
# Auto update + generate report
python3 scripts/fetch_usage.py --today && python3 scripts/html_report.py
```

### Output Modes

| Scenario | Command | Output |
|----------|---------|--------|
| **Default** | `html_report.py` | 📊 Image → user's default channel |
| User wants text | `report.py` | 📝 Text → user's default channel |
| User wants JSON | `report.py --json` | 📋 JSON → user's default channel |

## 📊 Sample Output

### Image Report

![AI Usage Report](examples/report-sample.png)

### Text Report

```
💰 LLM Cost Report - This Week
==================================================
Period: 2026-02-10 to 2026-02-17

Total Cost: $542.14
Total Tokens: 59.9M

📊 Token Breakdown:
   Input:  30.0M
   Output: 30.0M
   💡 Cache Savings: $0.00

📊 By Provider:
  • unknown: $533.89 (98%)
  • gemini: $7.32 (1%)
  • anthropic: $0.93 (0%)

📈 By Model (Top 10):
  • MiniMax-M2.5: $533.89 (98%)
  • gemini-3-flash: $7.32 (1%)
  • claude-opus-4-6-thinking: $0.93 (0%)
```

### JSON Output

```json
{
  "period": "week",
  "start_date": "2026-02-10",
  "end_date": "2026-02-17",
  "total_cost": 542.14,
  "tokens": {
    "input": 30000000,
    "output": 30000000,
    "cache_read": 0,
    "cache_write": 0,
    "total": 60000000
  },
  "cache_savings": {
    "read_savings": 0,
    "write_cost": 0,
    "total_savings": 0
  },
  "by_provider": {
    "unknown": 533.89,
    "gemini": 7.32,
    "anthropic": 0.93
  }
}
```

## 📁 Project Structure

```
llm-cost-monitor/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config/
│   └── config.yaml.example    # Optional config template
├── scripts/
│   ├── fetch_usage.py         # Fetch usage from sessions
│   ├── calc_cost.py           # Cost calculation with pricing
│   ├── store.py               # SQLite storage
│   ├── report.py              # Text reports
│   ├── html_report.py          # Visual HTML reports
│   ├── alert.py               # Budget alerts
│   └── notify.py              # Multi-channel notification
└── examples/
    ├── report-sample.png       # Sample image output
    └── cron_example.sh         # Cron examples
```

## 🔧 Available Commands

```bash
# Full flow: fetch + generate report
python3 scripts/fetch_usage.py --today && python3 scripts/html_report.py

# Text report
python3 scripts/report.py --period week

# JSON report
python3 scripts/report.py --json

# Budget alerts
python3 scripts/alert.py --budget-usd 50

# Fetch data
python3 scripts/fetch_usage.py --last-days 7
```

## 💾 Data Schema

| Field | Description |
|-------|-------------|
| `date` | Usage date |
| `provider` | API provider (anthropic, openai, gemini, etc.) |
| `model` | Model name |
| `app` | Application (openclaw, clawdbot) |
| `source` | Data source (session, manual, api) |
| `input_tokens` | Input tokens consumed |
| `output_tokens` | Output tokens generated |
| `cache_read_tokens` | Tokens read from cache (90% discount) |
| `cache_creation_tokens` | Tokens written to cache |
| `cost` | Calculated cost in USD |

## 🔔 Budget Alerts

```bash
# Check daily budget - exits with code 2 if exceeded
python3 scripts/alert.py --budget-usd 10 --period today

# Warn only (no exit)
python3 scripts/alert.py --budget-usd 50 --period week --mode warn

# Check monthly budget
python3 scripts/alert.py --budget-usd 100 --period month
```

Exit codes:
- `0` - Within budget
- `2` - Budget exceeded

## ⏰ Automation

### Cron Job

```bash
# Daily auto fetch + budget check
0 23 * * * cd /path/to/llm-cost-monitor && python3 scripts/fetch_usage.py --yesterday
30 23 * * * cd /path/to/llm-cost-monitor && python3 scripts/alert.py --budget-usd 10 --period yesterday
```

### OpenClaw Cron

```json
{
  "name": "llm-cost-weekly-report",
  "schedule": {"kind": "cron", "expr": "0 9 * * 1", "tz": "Asia/Shanghai"},
  "payload": {"kind": "agentTurn", "message": "Run fetch_usage.py && html_report.py"},
  "sessionTarget": "isolated",
  "delivery": {"mode": "announce"}
}
```

## 📝 Requirements

- Python 3.8+
- pyyaml
- requests
- html2image (for visual reports)

## 📄 License

MIT
