#!/usr/bin/env python3
"""
Generate visually appealing HTML reports for LLM cost monitoring - PPT Horizontal Style
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
    """Generate a horizontal PPT-style HTML report"""
    
    today_dt = datetime.now()
    if not start_date:
        start_date = today_dt.replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today_dt.strftime("%Y-%m-%d")
    
    # Trend ranges
    last_30d_start = (today_dt - timedelta(days=29)).strftime("%Y-%m-%d")
    
    # Comparison range
    requested_start = datetime.strptime(start_date, "%Y-%m-%d")
    requested_end = datetime.strptime(end_date, "%Y-%m-%d")
    period_days = (requested_end - requested_start).days + 1
    prev_start = (requested_start - timedelta(days=period_days)).strftime("%Y-%m-%d")
    prev_end = (requested_start - timedelta(days=1)).strftime("%Y-%m-%d")

    # Fetch data
    all_data = store.get_usage(min(last_30d_start, prev_start), end_date)
    
    daily_summary = {}
    by_model_tokens = {}
    by_model_cost = {}
    total_savings = 0
    prev_period_cost = 0
    
    for record in all_data:
        date = record['date']
        if date not in daily_summary:
            daily_summary[date] = {'cost': 0, 'tokens': 0}
        daily_summary[date]['cost'] += record['cost']
        daily_summary[date]['tokens'] += record['input_tokens'] + record['output_tokens']
        
        if start_date <= date <= end_date:
            model = record['model']
            by_model_tokens[model] = by_model_tokens.get(model, 0) + record['input_tokens'] + record['output_tokens']
            by_model_cost[model] = by_model_cost.get(model, 0) + record['cost']
            total_savings += record.get('savings', 0)
            
        if prev_start <= date <= prev_end:
            prev_period_cost += record['cost']

    period_usage = [d for d in all_data if start_date <= d['date'] <= end_date]
    total_cost = sum(r['cost'] for r in period_usage)
    total_tokens = sum(r['input_tokens'] + r['output_tokens'] for r in period_usage)
    days_count = len(set(r['date'] for r in period_usage)) or 1
    
    growth_html = ""
    if prev_period_cost > 0:
        growth_pct = ((total_cost - prev_period_cost) / prev_period_cost) * 100
        color = "#ef4444" if growth_pct > 0 else "#10b981"
        symbol = "↑" if growth_pct > 0 else "↓"
        growth_html = f'<span style="color:{color};font-size:14px;margin-left:8px;font-weight:600">{symbol}{abs(growth_pct):.1f}%</span>'

    def get_trend_svg(dates, data_dict, key, width=320, height=40):
        values = [data_dict.get(d, {}).get(key, 0) for d in dates]
        max_val = max(values) if values else 1
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
            <defs><linearGradient id="grad-{key}" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:#10b981;stop-opacity:0.3"/><stop offset="100%" style="stop-color:#10b981;stop-opacity:0"/></linearGradient></defs>
            <path d="{path_data} L{width},{height} L0,{height} Z" fill="url(#grad-{key})" />
            <path d="{path_data}" fill="none" stroke="#10b981" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
        </svg>"""

    last_7_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    last_30_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    
    def fmt_cost(c): return f"${c:.2f}"
    def fmt_tokens(t):
        if t >= 1000000: return f"{t/1000000:.1f}M"
        if t >= 1000: return f"{t/1000:.1f}K"
        return str(t)

    avg_unit_cost = (total_cost / total_tokens * 1000000) if total_tokens > 0 else 0
    daily_avg_cost = (total_cost / days_count) if days_count > 0 else 0

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0d0d0d;color:#fff">
    <div style="width:840px;margin:0 auto;padding:24px;display:flex;flex-direction:column;gap:16px">
        
        <!-- Header Row -->
        <div style="display:flex;gap:16px">
            <div style="flex:1.5;background:linear-gradient(135deg,#059669,#10b981);border-radius:20px;padding:24px;display:flex;justify-content:space-between;align-items:center">
                <div>
                    <div style="font-size:14px;opacity:0.9;margin-bottom:4px">AI Resource Usage</div>
                    <div style="font-size:48px;font-weight:800;line-height:1">{fmt_tokens(total_tokens)}</div>
                    <div style="font-size:12px;opacity:0.6;margin-top:12px">{start_date} ~ {end_date}</div>
                </div>
                <div style="text-align:right">
                    <div style="display:flex;align-items:baseline;justify-content:flex-end">
                        <span style="font-size:24px;font-weight:700">≈ {fmt_cost(total_cost)}</span>
                        {growth_html}
                    </div>
                    {f'<div style="margin-top:8px;font-size:13px;font-weight:600;color:#f0fdf4;display:flex;align-items:center;justify-content:flex-end">⚡ Saved {fmt_cost(total_savings)}</div>' if total_savings > 0 else ""}
                </div>
            </div>
            
            <div style="flex:1;background:#1a1a1a;border-radius:20px;padding:20px;display:flex;flex-direction:column;justify-content:center;gap:12px">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:12px;color:#6b7280">Unit Cost</span>
                    <span style="font-size:18px;font-weight:600;color:#10b981">${avg_unit_cost:.2f}/M</span>
                </div>
                <div style="height:1px;background:#2a2a2a"></div>
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:12px;color:#6b7280">Daily Avg</span>
                    <span style="font-size:18px;font-weight:600;color:#10b981">{fmt_cost(daily_avg_cost)}</span>
                </div>
            </div>
        </div>

        <!-- Main Body Row -->
        <div style="display:flex;gap:16px">
            
            <!-- Left Column: Trends -->
            <div style="flex:1;background:#1a1a1a;border-radius:20px;padding:24px">
                <div style="font-size:14px;font-weight:600;margin-bottom:20px;color:#10b981">Usage Trends (30D)</div>
                <div style="margin-bottom:28px">
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:8px">
                        <span>Tokens</span>
                        <span>Trend</span>
                    </div>
                    {get_trend_svg(last_30_dates, daily_summary, 'tokens', width=350)}
                </div>
                <div>
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:8px">
                        <span>Cost</span>
                        <span>Trend</span>
                    </div>
                    {get_trend_svg(last_30_dates, daily_summary, 'cost', width=350)}
                </div>
            </div>

            <!-- Right Column: Last 7 Days & Models -->
            <div style="flex:1;display:flex;flex-direction:column;gap:16px">
                <!-- Models -->
                <div style="background:#1a1a1a;border-radius:20px;padding:20px">
                    <div style="font-size:14px;font-weight:600;margin-bottom:16px;color:#10b981">Model Efficiency</div>
"""
    
    for model in sorted(by_model_tokens.keys(), key=lambda x: -by_model_tokens[x])[:4]:
        cost = by_model_cost.get(model, 0)
        tokens = by_model_tokens[model]
        bar_width = (tokens / total_tokens * 100) if total_tokens > 0 else 0
        unit_cost = (cost / tokens * 1000000) if tokens > 0 else 0
        display_name = model
        for k in ['MiniMax', 'Claude', 'Gemini', 'GPT']:
            if k.lower() in model.lower(): display_name = k; break
        
        html += f"""                    <div style="margin-bottom:14px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:12px">
                            <span style="color:#10b981">{display_name}</span>
                            <span>{fmt_tokens(tokens)} <span style="color:#6b7280">(${unit_cost:.2f}/M)</span></span>
                        </div>
                        <div style="height:6px;background:#2a2a2a;border-radius:3px;overflow:hidden">
                            <div style="height:100%;width:{bar_width}%;background:#10b981"></div>
                        </div>
                    </div>
"""
    
    html += """                </div>
                
                <!-- 7 Days -->
                <div style="background:#1a1a1a;border-radius:20px;padding:20px">
                    <div style="font-size:14px;font-weight:600;margin-bottom:16px;color:#10b981">Last 7 Days</div>
                    <div style="display:flex;gap:8px;align-items:flex-end;height:60px">
"""
    
    max_day_tokens = max([daily_summary.get(d, {}).get('tokens', 0) for d in last_7_dates] or [1]) or 1
    for date in last_7_dates:
        day_tokens = daily_summary.get(date, {}).get('tokens', 0)
        h_pct = (day_tokens / max_day_tokens * 100)
        day_label = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
        
        html += f"""                        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:6px">
                            <div style="width:100%;background:#2a2a2a;border-radius:4px;height:60px;position:relative;overflow:hidden">
                                <div style="position:absolute;bottom:0;width:100%;height:{h_pct}%;background:#10b981;border-radius:2px"></div>
                            </div>
                            <span style="font-size:10px;color:#6b7280">{day_label}</span>
                        </div>
"""

    html += """                    </div>
                </div>
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
