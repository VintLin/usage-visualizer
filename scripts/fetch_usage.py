#!/usr/bin/env python3
"""
Fetch usage data from LLM providers (OpenAI, Anthropic)
"""
import argparse
import json
import os
import sys
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import UsageStore
from calc_cost import calculate_cost, MODEL_PRICING


def load_config(config_path: str = "config/config.yaml") -> Dict:
    """Load configuration from YAML file"""
    # Try multiple paths
    paths_to_try = [
        config_path,
        os.path.join(os.path.dirname(os.path.dirname(__file__)), config_path),
        os.path.expanduser("~/.llm-cost-monitor/config.yaml"),
    ]

    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)

    # Return empty config if no file found
    return {"providers": {}, "budget": {}, "storage": {}}


def fetch_openai_usage(api_key: str, date: str) -> List[Dict]:
    """Fetch usage from OpenAI API"""
    import requests

    url = "https://api.openai.com/v1/usage"
    params = {"date": date}

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        usage_records = []
        for item in data.get("data", []):
            # Skip if no usage
            if item.get("n_context_tokens_total", 0) == 0 and item.get("n_generated_tokens_total", 0) == 0:
                continue

            model = item.get("snapshot_id", "unknown")
            input_tokens = item.get("n_context_tokens_total", 0)
            output_tokens = item.get("n_generated_tokens_total", 0)

            # Calculate cost
            cost = calculate_cost(model, input_tokens, output_tokens)

            usage_records.append({
                "provider": "openai",
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": 0,
                "cache_creation_tokens": 0,
                "cost": cost
            })

        return usage_records

    except requests.exceptions.RequestException as e:
        print(f"Error fetching OpenAI usage: {e}")
        return []


def fetch_anthropic_usage(api_key: str, organization_id: str, start_date: str, end_date: str) -> List[Dict]:
    """Fetch usage from Anthropic API"""
    import requests

    # Anthropic API endpoint
    url = f"https://api.anthropic.com/v1/organizations/{organization_id}/usage"

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    params = {
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        usage_records = []

        # Process by day
        for day_data in data.get("daily_usage", []):
            date = day_data.get("date", start_date)

            for usage in day_data.get("usage", []):
                model = usage.get("model", "unknown")
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                cache_read_tokens = usage.get("cache_read_tokens", 0)
                cache_creation_tokens = usage.get("cache_creation_tokens", 0)

                # Calculate cost with cache
                cost = calculate_cost(
                    model,
                    input_tokens,
                    output_tokens,
                    cache_read_tokens,
                    cache_creation_tokens
                )

                usage_records.append({
                    "provider": "anthropic",
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read_tokens": cache_read_tokens,
                    "cache_creation_tokens": cache_creation_tokens,
                    "cost": cost
                })

        return usage_records

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Anthropic usage: {e}")
        return []


def fetch_usage(
    date: str,
    config_path: str = "config/config.yaml",
    dry_run: bool = False
):
    """Fetch usage for a specific date"""
    config = load_config(config_path)

    storage_path = config.get("storage", {}).get("path", "~/.llm-cost-monitor")
    store = UsageStore(storage_path)

    providers = config.get("providers", {})
    total_fetched = 0

    # Fetch OpenAI usage
    openai_keys = providers.get("openai", {}).get("keys", [])
    for api_key in openai_keys:
        print(f"Fetching OpenAI usage for {date}...")
        records = fetch_openai_usage(api_key, date)

        if not dry_run:
            for record in records:
                store.add_usage(
                    date=date,
                    provider="openai",
                    api_key=api_key,
                    model=record["model"],
                    input_tokens=record["input_tokens"],
                    output_tokens=record["output_tokens"],
                    cache_read_tokens=record.get("cache_read_tokens", 0),
                    cache_creation_tokens=record.get("cache_creation_tokens", 0),
                    cost=record["cost"]
                )

        total_fetched += len(records)
        print(f"  → {len(records)} records")

    # Fetch Anthropic usage
    anthropic_config = providers.get("anthropic", {})
    anthropic_keys = anthropic_config.get("keys", [])
    org_id = anthropic_config.get("organization_id", "")

    if anthropic_keys and org_id:
        print(f"Fetching Anthropic usage for {date}...")
        for api_key in anthropic_keys:
            records = fetch_anthropic_usage(api_key, org_id, date, date)

            if not dry_run:
                for record in records:
                    store.add_usage(
                        date=date,
                        provider="anthropic",
                        api_key=api_key,
                        model=record["model"],
                        input_tokens=record["input_tokens"],
                        output_tokens=record["output_tokens"],
                        cache_read_tokens=record.get("cache_read_tokens", 0),
                        cache_creation_tokens=record.get("cache_creation_tokens", 0),
                        cost=record["cost"]
                    )

            total_fetched += len(records)
            print(f"  → {len(records)} records")

    print(f"\nTotal: {total_fetched} records fetched")
    return total_fetched


def main():
    parser = argparse.ArgumentParser(description="Fetch LLM API usage data")
    parser.add_argument("--date", type=str, help="Specific date (YYYY-MM-DD)")
    parser.add_argument("--today", action="store_true", help="Fetch today's usage")
    parser.add_argument("--yesterday", action="store_true", help="Fetch yesterday's usage")
    parser.add_argument("--last-days", type=int, help="Fetch last N days")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to database")

    args = parser.parse_args()

    # Determine date(s) to fetch
    dates = []

    if args.today:
        dates.append(datetime.now().strftime("%Y-%m-%d"))
    elif args.yesterday:
        dates.append((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))
    elif args.last_days:
        for i in range(args.last_days):
            date = (datetime.now() - timedelta(days=i+1)).strftime("%Y-%m-%d")
            dates.append(date)
    elif args.date:
        dates.append(args.date)
    else:
        # Default to yesterday
        dates.append((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))

    # Fetch for each date
    for date in dates:
        print(f"\n{'='*50}")
        print(f"Fetching usage for {date}")
        print('='*50)
        fetch_usage(date, args.config, args.dry_run)


if __name__ == "__main__":
    main()
