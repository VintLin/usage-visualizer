#!/usr/bin/env python3
"""
Budget alerts for LLM Cost Monitor
"""
import argparse
import os
import sys
import yaml
from datetime import datetime, timedelta

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import UsageStore


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration"""
    paths_to_try = [
        config_path,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), config_path),
        os.path.expanduser("~/.llm-cost-monitor/config.yaml"),
    ]

    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)

    return {"providers": {}, "budget": {}, "storage": {}}


def format_cost(cost: float) -> str:
    """Format cost for display"""
    if cost >= 1:
        return f"${cost:.2f}"
    else:
        return f"${cost:.4f}"


def send_feishu_alert(webhook_url: str, message: str):
    """Send alert to Feishu"""
    import requests

    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Feishu alert sent")
    except Exception as e:
        print(f"❌ Failed to send Feishu alert: {e}")


def send_telegram_alert(bot_token: str, chat_id: str, message: str):
    """Send alert to Telegram"""
    import requests

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Telegram alert sent")
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")


def check_budget(
    budget: float,
    config: dict,
    mode: str = "exit",
    period: str = "month"
):
    """Check budget and send alerts"""
    storage_path = config.get("storage", {}).get("path", "~/.llm-cost-monitor")
    store = UsageStore(storage_path)

    # Get current month date range
    today = datetime.now()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    # Get usage
    total_cost = store.get_total_cost(start_date, end_date)

    # Calculate percentage
    pct = (total_cost / budget * 100) if budget > 0 else 0

    # Build message
    threshold = config.get("budget", {}).get("alert_threshold", 0.8) * 100

    if pct >= threshold:
        status = "🔴 EXCEEDED" if pct >= 100 else "⚠️ WARNING"
        message = f"""💰 LLM Cost Alert

{status} Budget Alert!

Current spending: {format_cost(total_cost)}
Budget limit: {format_cost(budget)}
Usage: {pct:.1f}%

Period: {start_date} to {end_date}
"""
    else:
        print(f"✅ Budget OK: {format_cost(total_cost)} / {format_cost(budget)} ({pct:.1f}%)")
        return 0

    # Send notifications
    notify_channels = config.get("budget", {}).get("notify_channels", [])
    notifications = config.get("notifications", {})

    for channel in notify_channels:
        if channel == "feishu":
            webhook = notifications.get("feishu", {}).get("webhook_url", "")
            if webhook:
                send_feishu_alert(webhook, message)
        elif channel == "telegram":
            token = notifications.get("telegram", {}).get("bot_token", "")
            chat_id = notifications.get("telegram", {}).get("chat_id", "")
            if token and chat_id:
                send_telegram_alert(token, chat_id, message)

    # Exit code based on mode
    if mode == "exit" and pct >= 100:
        print(f"\n🔴 Budget exceeded! Exiting with code 2")
        sys.exit(2)
    elif mode == "warn" or (mode == "exit" and pct >= threshold and pct < 100):
        print(f"\n⚠️ Budget warning! Exiting with code 1")
        sys.exit(1)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Check LLM cost budget")
    parser.add_argument("--budget", type=float, help="Budget limit in USD")
    parser.add_argument("--mode", type=str, choices=["exit", "warn"], default="exit",
                       help="Mode: exit with code on exceed, warn always exits 0")
    parser.add_argument("--period", type=str, choices=["today", "week", "month"],
                       default="month", help="Budget period")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")

    args = parser.parse_args()

    config = load_config(args.config)

    # Get budget from args or config
    budget = args.budget
    if budget is None:
        budget = config.get("budget", {}).get("monthly_limit", 0)

    if budget <= 0:
        print("No budget set. Use --budget or set monthly_limit in config.")
        sys.exit(1)

    exit_code = check_budget(budget, config, args.mode, args.period)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
