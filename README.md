# LLM Cost Monitor

Track and monitor LLM API usage and costs across multiple providers.

## ✨ Features

- **Multi-provider support**: OpenAI, Anthropic, Gemini
- **Accurate cost calculation**: Uses real-time pricing from LiteLLM
- **Cache token support**: Tracks Anthropic prompt caching discounts
- **Budget alerts**: Get notified when usage exceeds thresholds
- **Usage reports**: Daily, weekly, monthly breakdowns by model
- **Local storage**: All data stays on your machine
- **Cron automation**: Schedule automatic fetching and alerts

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/VintLin/llm-cost-monitor.git
cd llm-cost-monitor
```

### Configuration

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
    - feishu

storage:
  path: ~/.llm-cost-monitor
```

### Fetch Usage

```bash
# Today's usage
python3 scripts/fetch_usage.py --today

# Yesterday
python3 scripts/fetch_usage.py --yesterday

# Last 7 days
python3 scripts/fetch_usage.py --last-days 7
```

### View Reports

```bash
# Today's report
python3 scripts/report.py --today

# Weekly summary
python3 scripts/report.py --week

# Monthly breakdown
python3 scripts/report.py --month
```

## 📊 Examples

### Daily Report

```
💰 LLM Cost Report - 2026-02-16
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Today: $12.45 (🟢 -5% vs yesterday)

📊 By Provider:
• OpenAI: $8.20 (66%)
• Anthropic: $4.25 (34%)

📈 By Model:
• gpt-4o: $5.50 (44%)
• claude-sonnet-4: $4.25 (34%)
• gpt-4o-mini: $2.70 (22%)

📅 Month to Date: $342.50
🎯 Budget: $100/mo (342% ⚠️)
```

### JSON Output

```bash
$ python3 scripts/report.py --today --json
{
  "date": "2026-02-16",
  "total_cost": 12.45,
  "by_provider": {
    "openai": 8.20,
    "anthropic": 4.25
  },
  "by_model": {
    "gpt-4o": 5.50,
    "claude-sonnet-4": 4.25,
    "gpt-4o-mini": 2.70
  }
}
```

## 🔧 Configuration

### config.yaml

```yaml
providers:
  openai:
    # List of API keys to track
    keys:
      - sk-proj-xxx1
      - sk-proj-xxx2
    # Optional: specific models to track
    # models:
    #   - gpt-4o
    #   - gpt-4o-mini

  anthropic:
    keys:
      - sk-ant-api-xxx
    # Required for Anthropic
    organization_id: org-xxx

  # Coming soon
  # gemini:
  #   keys:
  #     - your-gemini-key

budget:
  # Monthly budget in USD
  monthly_limit: 100
  # Send alert at this threshold (0.8 = 80%)
  alert_threshold: 0.8
  # Notification channels
  notify_channels:
    - feishu
    # - telegram
    # - discord

storage:
  # Where to store database
  path: ~/.llm-cost-monitor

# Notification settings
notifications:
  feishu:
    webhook_url: ""  # Your webhook
  telegram:
    bot_token: ""
    chat_id: ""
```

## 🤖 Automation

### Cron Jobs

```bash
# Add to crontab (crontab -e)

# Fetch usage daily at 11 PM
0 23 * * * /path/to/scripts/fetch_usage.py --yesterday

# Check budget and send alerts
0 23 * * * /path/to/scripts/alert.py --budget 100

# Weekly report every Monday
0 9 * * 1 /path/to/scripts/report.py --week
```

### OpenClaw Integration

Add to HEARTBEAT.md:

```markdown
### LLM Cost Check (Daily)

- Run `python3 scripts/fetch_usage.py --yesterday`
- Run `python3 scripts/report.py --today`
```

## 📈 Supported Models

### OpenAI

- GPT-5, GPT-5 Mini
- GPT-4.1, GPT-4.1 Mini
- GPT-4o, GPT-4o Mini, GPT-4o Audio
- o1, o1 Mini, o1 Pro
- GPT-4 Turbo, GPT-4
- GPT-3.5 Turbo
- DALL-E 3, Whisper

### Anthropic

- Claude 4 Opus, Claude 4 Sonnet
- Claude 3.5 Sonnet, Claude 3.5 Haiku
- Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku

### Gemini (Coming Soon)

- Gemini 2.0 Flash
- Gemini 1.5 Pro, Gemini 1.5 Flash

## 🔐 Security

- API keys are stored locally in `config/config.yaml`
- No data is sent to external servers (except for usage fetching to providers)
- All usage data is stored in local SQLite database
- You can encrypt the config file for extra security

## 📝 License

MIT License - feel free to use and modify!

## 🙏 Credits

- Pricing data from [LiteLLM](https://github.com/BerriAI/litellm)
- Inspired by api-usage, llm-token-tracker, and cost-report
