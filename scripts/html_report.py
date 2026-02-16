#!/usr/bin/env python3
"""
Generate HTML report for LLM Cost Monitor
"""
import argparse
import json
import os
import sys
import yaml
from datetime import datetime, timedelta
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import UsageStore
from calc_cost import get_pricing


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
                return yaml.safe_load(f) or {}
    return {}


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


def generate_html(period: str, config: Dict, output_path: str = None) -> str:
    """Generate HTML report"""
    storage_path = config.get("storage", {}).get("path", "~/.llm-cost-monitor")
    store = UsageStore(storage_path)
    start_date, end_date = get_date_range(period)

    total_cost = store.get_total_cost(start_date, end_date)
    by_provider = store.get_cost_by_provider(start_date, end_date)
    by_model = store.get_cost_by_model(start_date, end_date)
    budget_limit = config.get("budget", {}).get("monthly_limit", 0)

    date_label = {
        "today": "Today",
        "yesterday": "Yesterday",
        "week": "This Week",
        "month": "This Month"
    }.get(period, period)

    # Check for unknown models
    unknown_models = []
    for model in by_model.keys():
        if get_pricing(model) is None:
            unknown_models.append(model)

    # Generate provider bars
    provider_bars = ""
    if by_provider:
        max_cost = max(by_provider.values()) if by_provider else 1
        for provider, cost in sorted(by_provider.items(), key=lambda x: x[1], reverse=True):
            pct = (cost / max_cost * 100) if max_cost > 0 else 0
            color = "#FF6B6B" if provider == "unknown" else "#4ECDC4" if provider == "anthropic" else "#45B7D1" if provider == "openai" else "#96CEB4"
            provider_bars += f"""
            <div class="provider-row">
                <div class="provider-name">{provider}</div>
                <div class="provider-bar-container">
                    <div class="provider-bar" style="width: {pct}%; background: {color};"></div>
                </div>
                <div class="provider-cost">{format_cost(cost)}</div>
            </div>
            """

    # Generate model bars
    model_bars = ""
    if by_model:
        max_cost = max(by_model.values()) if by_model else 1
        for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:8]:
            pct = (cost / max_cost * 100) if max_cost > 0 else 0
            model_bars += f"""
            <div class="model-row">
                <div class="model-name">{model}</div>
                <div class="model-bar-container">
                    <div class="model-bar" style="width: {pct}%;"></div>
                </div>
                <div class="model-cost">{format_cost(cost)}</div>
            </div>
            """

    # Budget status
    budget_html = ""
    if budget_limit > 0:
        pct = (total_cost / budget_limit * 100) if budget_limit > 0 else 0
        status = "✅" if pct < 80 else "⚠️" if pct < 100 else "🔴"
        budget_html = f"""
        <div class="budget-section">
            <div class="budget-header">🎯 Budget</div>
            <div class="budget-bar-container">
                <div class="budget-bar" style="width: {min(pct, 100)}%; background: {'#4ECDC4' if pct < 80 else '#FFE66D' if pct < 100 else '#FF6B6B'};"></div>
            </div>
            <div class="budget-text">{format_cost(total_cost)} / {format_cost(budget_limit)} ({pct:.0f}%) {status}</div>
        </div>
        """

    # Unknown models note
    unknown_note = ""
    if unknown_models:
        unknown_note = f"""
        <div class="unknown-note">
            ⚠️ No local pricing for: {', '.join(unknown_models)}<br>
            <small>Showing real cost from sessions</small>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Cost Report - {date_label}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 40px;
            color: #fff;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 32px;
            max-width: 600px;
            margin: 0 auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 32px;
        }}
        
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .header .period {{
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
        }}
        
        .total-cost {{
            text-align: center;
            padding: 24px;
            background: rgba(78, 205, 196, 0.1);
            border-radius: 16px;
            margin-bottom: 24px;
        }}
        
        .total-cost .amount {{
            font-size: 48px;
            font-weight: 700;
            color: #4ECDC4;
        }}
        
        .total-cost .label {{
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
            margin-top: 4px;
        }}
        
        .section {{
            margin-bottom: 24px;
        }}
        
        .section-title {{
            font-size: 14px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.6);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .provider-row, .model-row {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .provider-name, .model-name {{
            width: 100px;
            font-size: 13px;
            font-weight: 500;
            text-transform: capitalize;
        }}
        
        .provider-bar-container, .model-bar-container {{
            flex: 1;
            height: 24px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            margin: 0 12px;
        }}
        
        .provider-bar, .model-bar {{
            height: 100%;
            border-radius: 12px;
            transition: width 0.3s ease;
        }}
        
        .model-bar {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }}
        
        .provider-cost, .model-cost {{
            width: 80px;
            text-align: right;
            font-size: 13px;
            font-weight: 600;
        }}
        
        .budget-section {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px;
        }}
        
        .budget-header {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
        }}
        
        .budget-bar-container {{
            height: 12px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 8px;
        }}
        
        .budget-bar {{
            height: 100%;
            border-radius: 6px;
        }}
        
        .budget-text {{
            font-size: 13px;
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
        }}
        
        .unknown-note {{
            margin-top: 16px;
            padding: 12px;
            background: rgba(255, 230, 109, 0.1);
            border-radius: 8px;
            font-size: 12px;
            color: #FFE66D;
            text-align: center;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 24px;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.4);
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>💰 LLM Cost Report</h1>
            <div class="period">{date_label} · {start_date} to {end_date}</div>
        </div>
        
        <div class="total-cost">
            <div class="amount">{format_cost(total_cost)}</div>
            <div class="label">Total Cost</div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 By Provider</div>
            {provider_bars}
        </div>
        
        <div class="section">
            <div class="section-title">📈 By Model</div>
            {model_bars}
        </div>
        
        {budget_html}
        
        {unknown_note}
        
        <div class="footer">
            Generated by LLM Cost Monitor · {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
</body>
</html>"""

    if output_path:
        with open(output_path, 'w') as f:
            f.write(html)
        print(f"HTML saved to: {output_path}")
    
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML LLM cost report")
    parser.add_argument("--period", type=str, choices=["today", "yesterday", "week", "month"],
                       default="today", help="Report period")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Config file path")
    parser.add_argument("--output", type=str, help="Output HTML file path")

    args = parser.parse_args()

    config = load_config(args.config)
    html = generate_html(args.period, config, args.output)
    
    if not args.output:
        print(html)


if __name__ == "__main__":
    main()
