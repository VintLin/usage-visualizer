#!/usr/bin/env python3
"""
Generate visually appealing HTML reports for LLM cost monitoring - Minimalist card style
"""
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import UsageStore


def generate_html_report(
    store: UsageStore,
    start_date: str = None,
    end_date: str = None,
    title: str = "AI 消耗"
) -> str:
    """Generate a minimalist card-style HTML report"""
    
    if not start_date:
        today = datetime.now()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch data
    daily_data = store.get_usage(start_date, end_date)
    total_cost = store.get_total_cost(start_date, end_date)
    by_model = store.get_cost_by_model(start_date, end_date)
    
    # Group by date for daily breakdown, also track tokens by model
    daily_summary = {}
    by_model_tokens = {}
    for record in daily_data:
        date = record['date']
        if date not in daily_summary:
            daily_summary[date] = {'cost': 0, 'input_tokens': 0, 'output_tokens': 0, 'models': {}}
        daily_summary[date]['cost'] += record['cost']
        daily_summary[date]['input_tokens'] += record['input_tokens']
        daily_summary[date]['output_tokens'] += record['output_tokens']
        
        model = record['model']
        if model not in daily_summary[date]['models']:
            daily_summary[date]['models'][model] = {'cost': 0, 'tokens': 0}
        daily_summary[date]['models'][model]['cost'] += record['cost']
        daily_summary[date]['models'][model]['tokens'] += record['input_tokens'] + record['output_tokens']
        
        # Track by model overall
        if model not in by_model_tokens:
            by_model_tokens[model] = 0
        by_model_tokens[model] += record['input_tokens'] + record['output_tokens']
    
    dates_with_data = sorted(daily_summary.keys())
    days_count = len(dates_with_data)
    total_tokens = sum(d['input_tokens'] + d['output_tokens'] for d in daily_summary.values())
    
    # Always show last 7 days
    today = datetime.now()
    chart_dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    
    def fmt_cost(c):
        return f"${c:.2f}"
    
    def fmt_tokens(t):
        if t >= 1000000:
            return f"{t/1000000:.1f}M"
        elif t >= 1000:
            return f"{t/1000:.1f}K"
        return str(t)
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0d0d0d">
    <div style="max-width:380px;margin:0 auto;padding:16px">
        <div style="background:linear-gradient(135deg,#059669,#10b981);border-radius:16px;padding:24px;color:#fff;margin-bottom:12px">
            <div style="font-size:14px;opacity:0.9;margin-bottom:4px">Monthly AI Usage</div>
            <div style="font-size:42px;font-weight:700">{fmt_tokens(total_tokens)}</div>
            <div style="font-size:14px;opacity:0.8;margin-top:8px">≈ {fmt_cost(total_cost)}</div>
            <div style="font-size:12px;opacity:0.6;margin-top:4px">{start_date} ~ {end_date} · {days_count} days</div>
        </div>
        
        <div style="background:#1a1a1a;border-radius:16px;padding:20px;margin-bottom:12px">
            <div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:16px">Last 7 Days</div>
"""
    
    # Daily bars - show all 7 days
    daily_costs = [daily_summary.get(d, {}).get('cost', 0) for d in chart_dates]
    max_daily_cost = max(daily_costs) if daily_costs else 1
    if max_daily_cost == 0:
        max_daily_cost = 1
    
    for date in chart_dates:
        day_cost = daily_summary.get(date, {}).get('cost', 0)
        day_tokens = daily_summary.get(date, {}).get('input_tokens', 0) + daily_summary.get(date, {}).get('output_tokens', 0)
        
        bar_width = (day_cost / max_daily_cost * 100) if max_daily_cost > 0 else 0
        day_label = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
        
        # Show placeholder if no data
        if day_cost == 0:
            display_tokens = "-"
            display_cost = ""
        else:
            display_tokens = fmt_tokens(day_tokens)
            display_cost = f"<div style='color:#6b7280;font-size:10px;line-height:1'>{fmt_cost(day_cost)}</div>"
        
        html += f"""            <div style="display:flex;align-items:center;margin-bottom:12px">
                <div style="width:40px;font-size:12px;color:#10b981">{day_label}</div>
                <div style="flex:1;height:20px;background:#2a2a2a;border-radius:4px;overflow:hidden;margin-right:10px">
                    <div style="height:100%;width:{bar_width}%;background:linear-gradient(90deg,#059669,#10b981);border-radius:4px"></div>
                </div>
                <div style="width:60px;text-align:right;display:flex;flex-direction:column;justify-content:center">
                    <div style="font-size:12px;color:#fff;font-weight:500;line-height:1.2">{display_tokens}</div>
                    {display_cost}
                </div>
            </div>
"""
    
    html += """        </div>
        
        <div style="background:#1a1a1a;border-radius:16px;padding:20px;margin-bottom:12px">
            <div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:16px">By Model</div>
"""
    
    # Model bars
    for model in sorted(by_model_tokens.keys(), key=lambda x: -by_model_tokens[x])[:5]:
        cost = by_model.get(model, 0)
        tokens = by_model_tokens[model]
        pct = (tokens / total_tokens * 100) if total_tokens > 0 else 0
        bar_width = pct
        
        # Model display name
        if 'MiniMax' in model:
            display_name = 'MiniMax'
        elif 'claude' in model.lower():
            display_name = 'Claude'
        elif 'gemini' in model.lower():
            display_name = 'Gemini'
        elif 'gpt' in model.lower():
            display_name = 'GPT'
        else:
            display_name = model[:12]
        
        html += f"""            <div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:13px;color:#10b981">{display_name}</span>
                    <span style="font-size:13px;color:#fff;font-weight:500">{fmt_tokens(tokens)} <span style="color:#6b7280;font-weight:400">≈{fmt_cost(cost)}</span></span>
                </div>
                <div style="height:8px;background:#2a2a2a;border-radius:4px;overflow:hidden">
                    <div style="height:100%;width:{bar_width}%;background:#10b981;border-radius:4px"></div>
                </div>
            </div>
"""
    
    html += f"""        </div>
        
        <div style="display:flex;gap:12px">
            <div style="flex:1;background:#1a1a1a;border-radius:12px;padding:16px;text-align:center">
                <div style="font-size:12px;color:#10b981;margin-bottom:4px">Total Tokens</div>
                <div style="font-size:18px;font-weight:600;color:#fff">{fmt_tokens(total_tokens)}</div>
            </div>
            <div style="flex:1;background:#1a1a1a;border-radius:12px;padding:16px;text-align:center">
                <div style="font-size:12px;color:#10b981;margin-bottom:4px">Daily Avg</div>
                <div style="font-size:18px;font-weight:600;color:#fff">{fmt_cost(total_cost/days_count) if days_count>0 else '$0'}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML report")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default="/tmp/llm-cost-report.html", help="Output HTML file")
    parser.add_argument("--title", type=str, default="AI Usage", help="Report title")
    
    args = parser.parse_args()
    
    store = UsageStore()
    html = generate_html_report(store, args.start, args.end, args.title)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML report saved to: {args.output}")


if __name__ == "__main__":
    main()
