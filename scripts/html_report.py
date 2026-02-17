#!/usr/bin/env python3
"""
Generate visually appealing HTML reports for LLM cost monitoring - PPT Horizontal Style V2
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
    """Generate a horizontal PPT-style HTML report with multi-line trends"""
    
    today_dt = datetime.now()
    if not start_date:
        start_date = today_dt.replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today_dt.strftime("%Y-%m-%d")
    
    # Trend ranges (30 days)
    last_30d_start = (today_dt - timedelta(days=29)).strftime("%Y-%m-%d")
    
    # Comparison range
    requested_start = datetime.strptime(start_date, "%Y-%m-%d")
    requested_end = datetime.strptime(end_date, "%Y-%m-%d")
    period_days = (requested_end - requested_start).days + 1
    prev_start = (requested_start - timedelta(days=period_days)).strftime("%Y-%m-%d")
    prev_end = (requested_start - timedelta(days=1)).strftime("%Y-%m-%d")

    # Fetch data
    all_data = store.get_usage(last_30d_start, end_date)
    
    daily_total = {} # {date: {'cost': 0, 'tokens': 0}}
    daily_models = {} # {date: {model: {'cost': 0, 'tokens': 0}}}
    by_model_tokens = {}
    by_model_cost = {}
    total_savings = 0
    prev_period_cost = 0
    
    models_set = set()
    
    for record in all_data:
        date = record['date']
        model = record['model']
        models_set.add(model)
        
        if date not in daily_total: daily_total[date] = {'cost': 0, 'tokens': 0}
        daily_total[date]['cost'] += record['cost']
        daily_total[date]['tokens'] += record['input_tokens'] + record['output_tokens']
        
        if date not in daily_models: daily_models[date] = {}
        if model not in daily_models[date]: daily_models[date][model] = {'cost': 0, 'tokens': 0}
        daily_models[date][model]['cost'] += record['cost']
        daily_models[date][model]['tokens'] += record['input_tokens'] + record['output_tokens']
        
        if start_date <= date <= end_date:
            by_model_tokens[model] = by_model_tokens.get(model, 0) + record['input_tokens'] + record['output_tokens']
            by_model_cost[model] = by_model_cost.get(model, 0) + record['cost']
            total_savings += record.get('savings', 0)
            
        if prev_start <= date <= prev_end:
            prev_period_cost += record['cost']

    total_cost = sum(by_model_cost.values())
    total_tokens = sum(by_model_tokens.values())
    days_count = len(set(r['date'] for r in all_data if start_date <= r['date'] <= end_date)) or 1
    
    growth_html = ""
    if prev_period_cost > 0:
        growth_pct = ((total_cost - prev_period_cost) / prev_period_cost) * 100
        color = "#ef4444" if growth_pct > 0 else "#10b981"
        symbol = "↑" if growth_pct > 0 else "↓"
        growth_html = f'<span style="color:{color};font-size:14px;margin-left:8px;font-weight:600">{symbol}{abs(growth_pct):.1f}%</span>'

    # Top models for trend lines (top 3)
    top_trend_models = sorted(by_model_tokens.keys(), key=lambda x: -by_model_tokens[x])[:3]
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6"]

    def get_trend_svg(dates, key, width=350, height=80):
        # Calculate max from total for scaling
        max_val = max([daily_total.get(d, {}).get(key, 0) for d in dates] or [1]) or 1
        
        svg_content = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="overflow:visible;display:block">'
        svg_content += '<defs>'
        for i, color in enumerate(colors):
            svg_content += f'<linearGradient id="grad-{key}-{i}" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:{color};stop-opacity:0.2"/><stop offset="100%" style="stop-color:{color};stop-opacity:0"/></linearGradient>'
        svg_content += '</defs>'

        # Draw total line first
        points = []
        for i, d in enumerate(dates):
            val = daily_total.get(d, {}).get(key, 0)
            x = (i / (len(dates) - 1)) * width
            y = height - (val / max_val * height)
            points.append(f"{x:.1f},{y:.1f}")
        path = "L".join(points)
        svg_content += f'<path d="M{path} L{width},{height} L0,{height} Z" fill="url(#grad-{key}-0)" />'
        svg_content += f'<path d="M{path}" fill="none" stroke="{colors[0]}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />'

        # Draw model lines (top 3)
        for idx, m in enumerate(top_trend_models):
            m_points = []
            for i, d in enumerate(dates):
                val = daily_models.get(d, {}).get(m, {}).get(key, 0)
                x = (i / (len(dates) - 1)) * width
                y = height - (val / max_val * height)
                m_points.append(f"{x:.1f},{y:.1f}")
            m_path = "L".join(m_points)
            m_color = colors[(idx + 1) % len(colors)]
            svg_content += f'<path d="M{m_path}" fill="none" stroke="{m_color}" stroke-width="1.2" stroke-dasharray="3,2" opacity="0.7" />'
            
        svg_content += '</svg>'
        return svg_content

    last_7_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    last_30_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    
    def fmt_cost(c): return f"${c:.2f}"
    def fmt_tokens(t):
        if t >= 1000000: return f"{t/1000000:.1f}M"
        if t >= 1000: return f"{t/1000:.1f}K"
        return str(int(t))

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
        
        <!-- Header Row: Aligned Widths -->
        <div style="display:flex;gap:16px">
            <!-- Main Stats: Flex 2nd card for alignment -->
            <div style="flex:2;background:linear-gradient(135deg,#059669,#10b981);border-radius:20px;padding:24px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 10px 15px -3px rgba(0,0,0,0.2)">
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
            
            <div style="flex:1;background:#1a1a1a;border-radius:20px;padding:20px;display:flex;flex-direction:column;justify-content:center;gap:16px;border:1px solid #2a2a2a">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:12px;color:#6b7280">Unit Cost</span>
                    <span style="font-size:20px;font-weight:700;color:#10b981">${avg_unit_cost:.2f}/M</span>
                </div>
                <div style="height:1px;background:#2a2a2a"></div>
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:12px;color:#6b7280">Daily Avg</span>
                    <span style="font-size:20px;font-weight:700;color:#10b981">{fmt_cost(daily_avg_cost)}</span>
                </div>
            </div>
        </div>

        <!-- Body Row -->
        <div style="display:flex;gap:16px">
            
            <!-- Left: High Trends -->
            <div style="flex:1;background:#1a1a1a;border-radius:20px;padding:24px;display:flex;flex-direction:column;justify-content:space-between;border:1px solid #2a2a2a">
                <div style="font-size:15px;font-weight:700;margin-bottom:24px;color:#10b981;display:flex;justify-content:space-between;align-items:center">
                    <span>Usage Trends (30D)</span>
                    <div style="display:flex;gap:8px;font-size:9px;font-weight:400">
                        <span style="display:flex;align-items:center;gap:3px"><i style="width:6px;height:6px;background:#10b981;border-radius:50%"></i>Total</span>
                        <span style="display:flex;align-items:center;gap:3px"><i style="width:6px;height:6px;border:1px dashed #3b82f6;border-radius:50%"></i>Models</span>
                    </div>
                </div>
                
                <div style="margin-bottom:32px;flex:1">
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:12px">
                        <span>Tokens Consumption</span>
                        <span>Peak: {fmt_tokens(max([daily_total.get(d, {}).get('tokens', 0) for d in last_30_dates] or [0]))}</span>
                    </div>
                    {get_trend_svg(last_30_dates, 'tokens', width=355, height=90)}
                </div>
                
                <div style="flex:1">
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#6b7280;margin-bottom:12px">
                        <span>Cost Distribution (USD)</span>
                        <span>Peak: {fmt_cost(max([daily_total.get(d, {}).get('cost', 0) for d in last_30_dates] or [0]))}</span>
                    </div>
                    {get_trend_svg(last_30_dates, 'cost', width=355, height=90)}
                </div>
            </div>

            <!-- Right: Aligned Height -->
            <div style="flex:1;display:flex;flex-direction:column;gap:16px">
                <!-- Models -->
                <div style="background:#1a1a1a;border-radius:20px;padding:24px;border:1px solid #2a2a2a;flex:1.2">
                    <div style="font-size:15px;font-weight:700;margin-bottom:20px;color:#10b981">Model Efficiency</div>
                    { "".join([f'''
                    <div style="margin-bottom:18px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:13px">
                            <span style="color:#10b981;font-weight:500">{(m[:10]+'..') if len(m)>10 else m}</span>
                            <span style="font-weight:600">{fmt_tokens(by_model_tokens[m])} <span style="color:#6b7280;font-weight:400;font-size:11px">(${ (by_model_cost[m]/by_model_tokens[m]*1000000) if by_model_tokens[m]>0 else 0:.2f}/M)</span></span>
                        </div>
                        <div style="height:8px;background:#2a2a2a;border-radius:4px;overflow:hidden">
                            <div style="height:100%;width:{ (by_model_tokens[m]/total_tokens*100) if total_tokens>0 else 0 }%;background:linear-gradient(90deg,#059669,#10b981)"></div>
                        </div>
                    </div>
                    ''' for m in sorted(by_model_tokens.keys(), key=lambda x: -by_model_tokens[x])[:4]]) }
                </div>
                
                <!-- 7 Days -->
                <div style="background:#1a1a1a;border-radius:20px;padding:24px;border:1px solid #2a2a2a;flex:1">
                    <div style="font-size:15px;font-weight:700;margin-bottom:20px;color:#10b981">Last 7 Days</div>
                    <div style="display:flex;gap:10px;align-items:flex-end;height:80px">
"""
    
    max_day_tokens = max([daily_total.get(d, {}).get('tokens', 0) for d in last_7_dates] or [1]) or 1
    for date in last_7_dates:
        day_tokens = daily_total.get(date, {}).get('tokens', 0)
        h_pct = (day_tokens / max_day_tokens * 100)
        day_label = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
        
        html += f"""                        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:8px">
                            <div style="width:100%;background:#2a2a2a;border-radius:6px;height:80px;position:relative;overflow:hidden">
                                <div style="position:absolute;bottom:0;width:100%;height:{h_pct}%;background:linear-gradient(0deg,#059669,#10b981);border-radius:3px"></div>
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
