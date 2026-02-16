#!/usr/bin/env python3
"""
Generate usage and cost reports
"""
import argparse
import json
import os
import sys
import yaml
from datetime import datetime, timedelta
from typing import Dict, Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import UsageStore


def load_config(config_path: str = "config/config.yaml") -> Dict:
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


def get_date_range(period: str) -> tuple:
    """Get start and end dates for a period"""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    if period == "today":
        return today_str, today_str
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d"), yesterday.strftime("%Y-%m-%d")
    elif period == "week":
        week_ago = today - timedelta(days=7)
        return week_ago.strftime("%Y-%m-%d"), today_str
    elif period == "month":
        month_ago = today - timedelta(days=30)
        return month_ago.strftime("%Y-%m-%d"), today_str
    else:
        return today_str, today_str


def format_cost(cost: float) -> str:
    """Format cost for display"""
    if cost >= 1:
        return f"${cost:.2f}"
    else:
        return f"${cost:.4f}"


def print_report(period: str, config: Dict):
    """Print usage report"""
    storage_path = config.get("storage", {}).get("path", "~/.llm-cost-monitor")
    store = UsageStore(storage_path)

    start_date, end_date = get_date_range(period)

    # Get data
    total_cost = store.get_total_cost(start_date, end_date)
    by_provider = store.get_cost_by_provider(start_date, end_date)
    by_model = store.get_cost_by_model(start_date, end_date)

    # Get budget info
    budget_limit = config.get("budget", {}).get("monthly_limit", 0)

    # Print report
    date_label = {
        "today": "Today",
        "yesterday": "Yesterday",
        "week": "This Week",
        "month": "This Month"
    }.get(period, period)

    print(f"\n💰 LLM Cost Report - {date_label}")
    print("=" * 50)
    print(f"Period: {start_date} to {end_date}")
    print(f"\nTotal Cost: {format_cost(total_cost)}")

    # By provider
    if by_provider:
        print(f"\n📊 By Provider:")
        for provider, cost in sorted(by_provider.items(), key=lambda x: x[1], reverse=True):
            pct = (cost / total_cost * 100) if total_cost > 0 else 0
            print(f"  • {provider}: {format_cost(cost)} ({pct:.0f}%)")

    # By model
    if by_model:
        print(f"\n📈 By Model:")
        for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = (cost / total_cost * 100) if total_cost > 0 else 0
            print(f"  • {model}: {format_cost(cost)} ({pct:.0f}%)")

    # Budget info
    if budget_limit > 0:
        pct_of_budget = (total_cost / budget_limit * 100) if budget_limit > 0 else 0
        status = "✅" if pct_of_budget < 80 else "⚠️" if pct_of_budget < 100 else "🔴"
        print(f"\n🎯 Budget: {format_cost(total_cost)} / {format_cost(budget_limit)} ({pct_of_budget:.0f}%) {status}")

    print()


def print_json(period: str, config: Dict):
    """Print report as JSON"""
    storage_path = config.get("storage", {}).get("path", "~/.llm-cost-monitor")
    store = UsageStore(storage_path)

    start_date, end_date = get_date_range(period)

    # Get data
    total_cost = store.get_total_cost(start_date, end_date)
    by_provider = store.get_cost_by_provider(start_date, end_date)
    by_model = store.get_cost_by_model(start_date, end_date)

    # Build JSON
    output = {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_cost": round(total_cost, 6),
        "by_provider": {k: round(v, 6) for k, v in by_provider.items()},
        "by_model": {k: round(v, 6) for k, v in by_model.items()}
    }

    # Add budget info
    budget_limit = config.get("budget", {}).get("monthly_limit", 0)
    if budget_limit > 0:
        output["budget"] = {
            "limit": budget_limit,
            "used": round(total_cost, 6),
            "percentage": round(total_cost / budget_limit * 100, 1)
        }

    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Generate LLM cost reports")
    parser.add_argument("--period", type=str, choices=["today", "yesterday", "week", "month"],
                       default="today", help="Report period")
    parser.add_argument("--date", type=str, help="Specific date (YYYY-MM-DD)")
    parser.add_argument("--from", dest="start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    config = load_config(args.config)

    if args.json:
        print_json(args.period, config)
    else:
        print_report(args.period, config)


if __name__ == "__main__":
    main()
