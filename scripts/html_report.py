#!/usr/bin/env python3
"""
Generate visually appealing HTML reports for LLM cost monitoring - Minimalist card style with Trend Lines
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
    """Generate a minimalist card-style HTML report with trend lines"""
    
    today_dt = datetime.now()
    if not start_date:
        start_date = today_dt.replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today_dt.strftime("%Y-%m-%d")
    
    # Trend ranges (30 days for line chart)
    last_30d_start = (today_dt - timedelta(days=29)).strftime("%Y-%m-%d")
    
    # Fetch all data needed for trends and main report
    all_data = store.get_usage(last_30d_start, end_date)
    
    daily_summary = {}
    by_model_tokens = {}
    by_model_cost = {}
    
    for record in all_data:
        date = record['date']
        if date not in daily_summary:
            daily_summary[date] = {'cost': 0, 'tokens': 0}
        daily_summary[date]['cost'] += record['cost']
        daily_summary[date]['tokens'] += record['input_tokens'] + record['output_tokens']
        
        # Only include data within start_date ~ end_date for model breakdown
        if start_date <= date <= end_date:
            model = record['model']
            by_model_tokens[model] = by_model_tokens.get(model, 0) + record['input_tokens'] + record['output_tokens']
            by_model_cost[model] = by_model_cost.get(model, 0) + record['cost']

    # Filtered totals for the requested period
    period_usage = [d for d in all_data if start_date <= d['date'] <= end_date]
    total_cost = sum(r['cost'] for r in period_usage)
    total_tokens = sum(r['input_tokens'] + r['output_tokens'] for r in period_usage)
    days_count = len(set(r['date'] for r in period_usage)) or 1

    # Trend calculation helper (SVG)
    def get_trend_svg(dates, data_dict, key, width=340, height=50):
        values = [data_dict.get(d, {}).get(key, 0) for d in dates]
        max_val = max(values) if values else 0
        if max_val == 0: max_val = 1
        
        points = []
        for i, val in enumerate(values):
            x = (i / (len(dates) - 1)) * width if len(dates) > 1 else 0
            y = height - (val / max_val * height)
            points.append(f"{x:.1f},{y:.1f}")
        
        path_data = "L".join(points)
        if path_data: path_data = "M" + path_data
        
        return f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="overflow:visible;display:block">
            <defs>
                <linearGradient id="grad-{key}" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#10b981;stop-opacity:0.3" />
                    <stop offset="100%" style="stop-color:#10b981;stop-opacity:0" />
                </linearGradient>
            </defs>
            <path d="{path_data} L{width},{height} L0,{height} Z" fill="url(#grad-{key})" />
            <path d="{path_data}" fill="none" stroke="#10b981" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
        </svg>
        """

    # Prepare chart dates
    last_7_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    last_30_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    
    def fmt_cost(c): return f"${c:.2f}"
    def fmt_tokens(t):
        if t >= 1000000: return f"{t/1000000:.1f}M"
        if t >= 1000: return f"{t/1000:.1f}K"
        return str(t)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0d0d0d;color:#fff">
    <div style="max-width:380px;margin:0 auto;padding:16px">
        <!-- Main Card -->
        <div style="background:linear-gradient(135deg,#059669,#10b981);border-radius:16px;padding:24px;margin-bottom:12px">
            <div style="font-size:14px;opacity:0.9;margin-bottom:4px">Monthly AI Usage</div>
            <div style="font-size:42px;font-weight:700">{fmt_tokens(total_tokens)}</div>
            <div style="font-size:14px;opacity:0.8;margin-top:8px">≈ {fmt_cost(total_cost)}</div>
            <div style="font-size:12px;opacity:0.6;margin-top:4px">{start_date} ~ {end_date} · {days_count} days</div>
        </div>

        <!-- Trends Section -->
        <div style="background:#1a1a1a;border-radius:16px;padding:20px;margin-bottom:12px">
            <div style="font-size:14px;font-weight:600;margin-bottom:16px">Usage Trends (30D)</div>
            <div style="margin-bottom:24px">
                <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:8px">
                    <span>Token Trend</span>
                    <span>Last 30 Days</span>
                </div>
                {get_trend_svg(last_30_dates, daily_summary, 'tokens')}
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:8px">
                    <span>Cost Trend</span>
                    <span>Last 30 Days</span>
                </div>
                {get_trend_svg(last_30_dates, daily_summary, 'cost')}
            </div>
        </div>
        
        <!-- Last 7 Days Section -->
        <div style="background:#1a1a1a;border-radius:16px;padding:20px;margin-bottom:12px">
            <div style="font-size:14px;font-weight:600;margin-bottom:16px">Last 7 Days Breakdown</div>
"""
    
    # Daily bars
    max_daily_cost = max([daily_summary.get(d, {}).get('cost', 0) for d in last_7_dates] or [1]) or 1
    for date in last_7_dates:
        day_cost = daily_summary.get(date, {}).get('cost', 0)
        day_tokens = daily_summary.get(date, {}).get('tokens', 0)
        bar_width = (day_cost / max_daily_cost * 100)
        day_label = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
        
        display_tokens = fmt_tokens(day_tokens) if day_tokens > 0 else "-"
        display_cost = f"<div style='color:#6b7280;font-size:10px;line-height:1'>{fmt_cost(day_cost)}</div>" if day_cost > 0 else ""
        
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
        
        <!-- Model Section -->
        <div style="background:#1a1a1a;border-radius:16px;padding:20px;margin-bottom:12px">
            <div style="font-size:14px;font-weight:600;margin-bottom:16px">By Model (Period)</div>
"""
    
    # Model bars
    for model in sorted(by_model_tokens.keys(), key=lambda x: -by_model_tokens[x])[:5]:
        cost = by_model_cost.get(model, 0)
        tokens = by_model_tokens[model]
        bar_width = (tokens / total_tokens * 100) if total_tokens > 0 else 0
        
        display_name = model
        for k in ['MiniMax', 'Claude', 'Gemini', 'GPT']:
            if k.lower() in model.lower():
                display_name = k
                break
        
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
        
        <!-- Summary Stats -->
        <div style="display:flex;gap:12px">
            <div style="flex:1;background:#1a1a1a;border-radius:12px;padding:16px;text-align:center">
                <div style="font-size:12px;color:#10b981;margin-bottom:4px">Period Tokens</div>
                <div style="font-size:18px;font-weight:600">{fmt_tokens(total_tokens)}</div>
            </div>
            <div style="flex:1;background:#1a1a1a;border-radius:12px;padding:16px;text-align:center">
                <div style="font-size:12px;color:#10b981;margin-bottom:4px">Daily Avg</div>
                <div style="font-size:18px;font-weight:600">{fmt_cost(total_cost/days_count)}</div>
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
