---
name: llm-cost-monitor
description: Track LLM API usage and costs from OpenClaw sessions with SQLite persistence, budget alerts, and visual HTML reports. No config required - works out of the box.
metadata: {"openclaw":{"emoji":"💰","requires":{"bins":["python3"]}}}
---

# LLM Cost Monitor

Track and monitor LLM API usage and costs from OpenClaw sessions with SQLite persistence, budget alerts, and visual HTML reports.

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
1. Run `fetch_usage.py --today` to fetch latest session data
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

### Available Commands

```bash
# Fetch usage data from OpenClaw sessions
python3 scripts/fetch_usage.py                    # Today's usage
python3 scripts/fetch_usage.py --yesterday         # Yesterday
python3 scripts/fetch_usage.py --last-days 7      # Last 7 days

# Text reports
python3 scripts/report.py                         # Today's report
python3 scripts/report.py --period yesterday       # Yesterday
python3 scripts/report.py --period week           # This week
python3 scripts/report.py --period month          # This month
python3 scripts/report.py --json                   # JSON output

# Visual HTML report (generate image)
python3 scripts/html_report.py                    # Generate HTML
python3 scripts/html_report.py --start 2026-01-01 --end 2026-01-31

# Budget alerts
python3 scripts/alert.py --budget-usd 50         # Check $50 budget (exit code 2 on breach)
python3 scripts/alert.py --budget-usd 100 --mode warn  # Just warn, don't exit
python3 scripts/alert.py --budget-usd 10 --period week   # Check weekly budget
```

## 📊 Data Dimensions

The tracker stores and analyzes:

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

## 💾 SQLite Storage

Data is stored at `~/.llm-cost-monitor/usage.db`

### Query Examples

```python
from scripts.store import UsageStore

store = UsageStore()

# Get today's cost
cost = store.get_total_cost("2026-02-17", "2026-02-17")

# Get tokens summary (including cache)
tokens = store.get_tokens_summary("2026-02-01", "2026-02-17")
# Returns: {input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens, total_tokens, total_cost}

# Get daily breakdown
daily = store.get_daily_summary("2026-02-01", "2026-02-17")
# Returns: [{date, input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens, cost}, ...]

# Get by model
by_model = store.get_cost_by_model("2026-02-01", "2026-02-17")
# Returns: {"claude-opus-4": 45.50, "gpt-4o": 23.20, ...}

# Get by app
by_app = store.get_by_app("2026-02-01", "2026-02-17")
# Returns: {"openclaw": 100.50, "clawdbot": 20.30}

# Get by source
by_source = store.get_by_source("2026-02-01", "2026-02-17")
# Returns: {"session": 120.80}
```

## 🔔 Budget Alerts

Integrate with cron or HEARTBEAT for automated monitoring:

```bash
# Check daily budget - exits with code 2 if exceeded
python3 scripts/alert.py --budget-usd 10 --period today

# Check weekly budget - warn only (no exit)
python3 scripts/alert.py --budget-usd 50 --period week --mode warn

# Check monthly budget
python3 scripts/alert.py --budget-usd 100 --period month
```

### Exit Codes

- `0` - Within budget
- `2` - Budget exceeded (use in cron to trigger alerts)

## 🖼️ Visual Reports

Generate HTML reports that can be converted to images:

```bash
# Generate HTML report
python3 scripts/html_report.py --output /tmp/report.html

# The HTML uses minimal inline styles and can be converted to PNG
# using html2image or similar tools
```

## 📁 Project Structure

```
llm-cost-monitor/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
├── requirements.txt             # Python dependencies
├── config/
│   └── config.yaml.example    # Optional config template
├── scripts/
│   ├── fetch_usage.py         # Fetch usage from sessions
│   ├── calc_cost.py           # Cost calculation with pricing
│   ├── store.py               # SQLite storage
│   ├── report.py              # Text reports
│   ├── html_report.py         # Visual HTML reports
│   ├── alert.py               # Budget alerts
│   └── notify.py             # Multi-channel notification
└── examples/
    ├── report-sample.png       # Sample image output
    └── cron_example.sh         # Cron examples
```

## 🤖 Automation

### Cron Job Example

```bash
# Run daily at 9 AM - fetch and check budget
0 9 * * * cd /path/to/llm-cost-monitor && python3 scripts/fetch_usage.py --yesterday && python3 scripts/alert.py --budget-usd 10 --period yesterday || echo "Budget exceeded!"
```

### OpenClaw HEARTBEAT Integration

Add to your HEARTBEAT.md:

```markdown
### LLM Cost Check (daily)
- Run: python3 scripts/alert.py --budget-usd 10 --period yesterday --mode warn
- If exit code 2, send alert to user
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

## 🔧 How It Works

1. **Finds session files**: `~/.openclaw/agents/*/sessions/*.jsonl`
2. **Parses usage data**: Extracts tokens, cache, cost from each call
3. **Stores in SQLite**: Persists historical data locally
4. **Generates reports**: Text or HTML output

## 📄 License

MIT
