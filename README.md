# LLM Cost Monitor

Track and monitor LLM API usage and costs from OpenClaw sessions.

## ✨ Features

- **No config required!** - Just install and run
- **Automatic OpenClaw detection** - Reads session logs automatically
- **Accurate cost tracking** - Uses real cost data when available, calculates otherwise
- **Cache token support** - Tracks Anthropic prompt caching
- **Daily/weekly/monthly reports** - Multiple time periods
- **Budget alerts** - Monitor your spending
- **Optional config** - Add external API monitoring later

## 🚀 Quick Start (No Config Needed!)

```bash
# Clone or install
git clone https://github.com/VintLin/llm-cost-monitor.git
cd llm-cost-monitor

# Install dependencies
pip install -r requirements.txt

# Run report - that's it!
python3 scripts/report.py
```

### Available Commands

```bash
# Reports
python3 scripts/report.py                    # Today's report
python3 scripts/report.py --period yesterday # Yesterday
python3 scripts/report.py --period week      # This week
python3 scripts/report.py --period month     # This month
python3 scripts/report.py --json             # JSON output

# Budget alerts
python3 scripts/alert.py --budget 50         # Check $50 budget

# Fetch usage
python3 scripts/fetch_usage.py               # Fetch today's data
python3 scripts/fetch_usage.py --yesterday   # Fetch yesterday
python3 scripts/fetch_usage.py --last-days 7 # Last 7 days
```

## 📊 Example Output

```
💰 LLM Cost Report - Today
==================================================
Period: 2026-02-16 to 2026-02-16

Total Cost: $12.45

📊 By Provider:
  • anthropic: $8.20 (66%)
  • openai: $4.25 (34%)

📈 By Model:
  • claude-sonnet-4.5: $5.50 (44%)
  • gpt-4o: $4.25 (34%)
  • gpt-4o-mini: $2.70 (22%)

🎯 Budget: $12.45 / $100.00 (12%) ✅
```

## ⚙️ Optional Configuration

Want to monitor external APIs too? Create `config/config.yaml`:

```yaml
# Monitor external APIs (OPTIONAL)
providers:
  openai:
    keys:
      - sk-your-openai-key
  anthropic:
    keys:
      - your-anthropic-key
    organization_id: your-org-id

# Budget settings (OPTIONAL)
budget:
  monthly_limit: 100
  alert_threshold: 0.8

# Notifications (OPTIONAL)
notify:
  - feishu
  # - telegram
```

**Note:** Without config, the tool still works perfectly by reading OpenClaw sessions!

## 📁 Project Structure

```
llm-cost-monitor/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config/
│   └── config.yaml.example    # Optional config template
├── scripts/
│   ├── fetch_usage.py         # Fetch usage data
│   ├── calc_cost.py           # Cost calculation
│   ├── store.py               # SQLite storage
│   ├── report.py              # Generate reports
│   └── alert.py               # Budget alerts
└── examples/
    └── cron.sh                # Cron examples
```

## 🔧 How It Works

### Default Mode (No Config)
1. Finds OpenClaw session files: `~/.openclaw/agents/*/sessions/*.jsonl`
2. Parses each session for `usage` data
3. Extracts: input_tokens, output_tokens, cache tokens, cost
4. Stores in local SQLite database
5. Generates reports

### With Config (Optional)
1. Same as default mode, plus:
2. Fetches usage from external APIs (OpenAI, Anthropic)
3. Aggregates all data together
4. Sends alerts via webhook

## 🤖 Automation

### Cron Job
```bash
# Add to crontab (crontab -e)
0 9 * * * /path/to/llm-cost-monitor/scripts/report.py
```

## 📝 Requirements

- Python 3.8+
- pyyaml
- requests

## 📄 License

MIT
