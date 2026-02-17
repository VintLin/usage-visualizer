#!/usr/bin/env python3
"""
Generate visually appealing HTML reports for LLM cost monitoring - PPT Horizontal Style V3 (Ultra Detail)
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
    """Generate a high-resolution horizontal PPT-style HTML report with full legends and labels"""
    
    today_dt = datetime.now()
    if not start_date:
        start_date = today_dt.replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today_dt.strftime("%Y-%m-%d")
    
    last_30d_start = (today_dt - timedelta(days=29)).strftime("%Y-%m-%d")
    
    requested_start = datetime.strptime(start_date, "%Y-%m-%d")
    requested_end = datetime.strptime(end_date, "%Y-%m-%d")
    period_days = (requested_end - requested_start).days + 1
    prev_start = (requested_start - timedelta(days=period_days)).strftime("%Y-%m-%d")
    prev_end = (requested_start - timedelta(days=1)).strftime("%Y-%m-%d")

    all_data = store.get_usage(min(last_30d_start, prev_start), end_date)
    
    daily_total = {}
    daily_models = {}
    by_model_tokens = {}
    by_model_cost = {}
    total_savings = 0
    prev_period_cost = 0
    
    for record in all_data:
        date = record['date']
        model = record['model']
        
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
        growth_html = f'<span style="color:{color};font-size:18px;margin-left:12px;font-weight:600">{symbol}{abs(growth_pct):.1f}%</span>'

    top_trend_models = sorted(by_model_tokens.keys(), key=lambda x: -by_model_tokens[x])[:3]
    # Colors: Green(Total), Blue, Orange, Purple
    colors = ["#10b981", "#3b82f6", "#f59e0b", "#a855f7"]

    def fmt_tokens(t):
        if t >= 1000000: return f"{t/1000000:.1f}M"
        if t >= 1000: return f"{t/1000:.1f}K"
        return str(int(t))
    
    def fmt_cost(c): return f"${c:.2f}"

    def get_trend_svg(dates, key, width=450, height=120):
        max_val = max([daily_total.get(d, {}).get(key, 0) for d in dates] or [1]) or 1
        
        svg_content = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="overflow:visible;display:block">'
        svg_content += '<defs>'
        for i, color in enumerate(colors):
            svg_content += f'<linearGradient id="grad-{key}-{i}" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:{color};stop-opacity:0.2"/><stop offset="100%" style="stop-color:{color};stop-opacity:0"/></linearGradient>'
        svg_content += '</defs>'

        # Draw total line
        points = []
        for i, d in enumerate(dates):
            val = daily_total.get(d, {}).get(key, 0)
            x = (i / (len(dates) - 1)) * width
            y = height - (val / max_val * height)
            points.append(f"{x:.1f},{y:.1f}")
        path = "L".join(points)
        svg_content += f'<path d="M{path} L{width},{height} L0,{height} Z" fill="url(#grad-{key}-0)" />'
        svg_content += f'<path d="M{path}" fill="none" stroke="{colors[0]}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" />'

        # Draw model lines
        for idx, m in enumerate(top_trend_models):
            m_points = []
            for i, d in enumerate(dates):
                val = daily_models.get(d, {}).get(m, {}).get(key, 0)
                x = (i / (len(dates) - 1)) * width
                y = height - (val / max_val * height)
                m_points.append(f"{x:.1f},{y:.1f}")
            m_path = "L".join(m_points)
            m_color = colors[(idx + 1) % len(colors)]
            svg_content += f'<path d="M{m_path}" fill="none" stroke="{m_color}" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.8" />'
            
        svg_content += '</svg>'
        return svg_content

    last_7_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    last_30_dates = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(29, -1, -1)]
    
    avg_unit_cost = (total_cost / total_tokens * 1000000) if total_tokens > 0 else 0
    daily_avg_cost = (total_cost / days_count) if days_count > 0 else 0

    # Clean model names for display
    def clean_m(m):
        for k in ['MiniMax', 'Claude', 'Gemini', 'GPT']:
            if k.lower() in m.lower(): return k
        return (m[:12]+'..') if len(m)>12 else m

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0d0d0d;color:#fff">
    <div style="width:1080px;margin:0 auto;padding:40px;display:flex;flex-direction:column;gap:24px">
        
        <!-- Header Row -->
        <div style="display:flex;gap:24px">
            <div style="flex:2;background:linear-gradient(135deg,#059669,#10b981);border-radius:24px;padding:32px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 20px 25px -5px rgba(0,0,0,0.3)">
                <div>
                    <div style="font-size:18px;opacity:0.9;margin-bottom:8px;font-weight:500">AI Resource Usage Overview</div>
                    <div style="font-size:64px;font-weight:800;line-height:1;letter-spacing:-1px">{fmt_tokens(total_tokens)}</div>
                    <div style="font-size:14px;opacity:0.7;margin-top:16px;background:rgba(0,0,0,0.1);padding:4px 12px;border-radius:100px;display:inline-block">{start_date} ~ {end_date}</div>
                </div>
                <div style="text-align:right">
                    <div style="display:flex;align-items:baseline;justify-content:flex-end">
                        <span style="font-size:36px;font-weight:700">{fmt_cost(total_cost)}</span>
                        {growth_html}
                    </div>
                    {f'<div style="margin-top:12px;font-size:16px;font-weight:600;color:#f0fdf4;display:flex;align-items:center;justify-content:flex-end"><span style="background:rgba(255,255,255,0.2);width:20px;height:20px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;margin-right:8px;font-size:12px">⚡</span>Saved {fmt_cost(total_savings)}</div>' if total_savings > 0 else ""}
                </div>
            </div>
            
            <div style="flex:1;background:#1a1a1a;border-radius:24px;padding:32px;display:flex;flex-direction:column;justify-content:center;gap:20px;border:1px solid #2a2a2a">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:14px;color:#6b7280;text-transform:uppercase;letter-spacing:1px">Unit Cost</span>
                    <span style="font-size:24px;font-weight:700;color:#10b981">${avg_unit_cost:.2f}<span style="font-size:14px;opacity:0.6">/M</span></span>
                </div>
                <div style="height:1px;background:#2a2a2a"></div>
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:14px;color:#6b7280;text-transform:uppercase;letter-spacing:1px">Daily Average</span>
                    <span style="font-size:24px;font-weight:700;color:#10b981">{fmt_cost(daily_avg_cost)}</span>
                </div>
            </div>
        </div>

        <!-- Main Body Row -->
        <div style="display:flex;gap:24px">
            
            <!-- Left: Trends with Legend -->
            <div style="flex:1.2;background:#1a1a1a;border-radius:24px;padding:32px;border:1px solid #2a2a2a">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px">
                    <div style="font-size:18px;font-weight:700;color:#10b981">Usage Trends (30D)</div>
                    <!-- Legend -->
                    <div style="display:flex;gap:12px;font-size:11px">
                        <div style="display:flex;align-items:center;gap:5px"><span style="width:12px;height:3px;background:{colors[0]}"></span>Total</div>
                        {" ".join([f'<div style="display:flex;align-items:center;gap:5px"><span style="width:12px;height:0;border-top:2px dashed {colors[i+1]}"></span>{clean_m(m)}</div>' for i, m in enumerate(top_trend_models)])}
                    </div>
                </div>
                
                <div style="margin-bottom:40px">
                    <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:16px">
                        <span style="font-weight:500;color:#9ca3af">Token Consumption</span>
                        <span>Peak: {fmt_tokens(max([daily_total.get(d, {}).get('tokens', 0) for d in last_30_dates] or [0]))}</span>
                    </div>
                    {get_trend_svg(last_30_dates, 'tokens', width=540, height=130)}
                </div>
                
                <div>
                    <div style="display:flex;justify-content:space-between;font-size:12px;color:#6b7280;margin-bottom:16px">
                        <span style="font-weight:500;color:#9ca3af">Cost Distribution (USD)</span>
                        <span>Peak: {fmt_cost(max([daily_total.get(d, {}).get('cost', 0) for d in last_30_dates] or [0]))}</span>
                    </div>
                    {get_trend_svg(last_30_dates, 'cost', width=540, height=130)}
                </div>
            </div>

            <!-- Right Column -->
            <div style="flex:1;display:flex;flex-direction:column;gap:24px">
                <!-- Efficiency -->
                <div style="background:#1a1a1a;border-radius:24px;padding:32px;border:1px solid #2a2a2a;flex:1.2">
                    <div style="font-size:18px;font-weight:700;margin-bottom:24px;color:#10b981">Model Efficiency Metrics</div>
                    { "".join([f'''
                    <div style="margin-bottom:20px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:14px">
                            <span style="color:#10b981;font-weight:600">{m}</span>
                            <span style="font-weight:600">{fmt_tokens(by_model_tokens[m])} <span style="color:#6b7280;font-weight:400;font-size:12px">(${ (by_model_cost[m]/by_model_tokens[m]*1000000) if by_model_tokens[m]>0 else 0:.2f}/M)</span></span>
                        </div>
                        <div style="height:10px;background:#2a2a2a;border-radius:5px;overflow:hidden">
                            <div style="height:100%;width:{ (by_model_tokens[m]/total_tokens*100) if total_tokens>0 else 0 }%;background:linear-gradient(90deg,#059669,#10b981)"></div>
                        </div>
                    </div>
                    ''' for m in sorted(by_model_tokens.keys(), key=lambda x: -by_model_tokens[x])[:4]]) }
                </div>
                
                <!-- Last 7 Days with labels -->
                <div style="background:#1a1a1a;border-radius:24px;padding:32px;border:1px solid #2a2a2a;flex:1">
                    <div style="font-size:18px;font-weight:700;margin-bottom:24px;color:#10b981">Last 7 Days Activity</div>
                    <div style="display:flex;gap:12px;align-items:flex-end;height:120px;padding-top:20px">
"""
    
    max_day_tokens = max([daily_total.get(d, {}).get('tokens', 0) for d in last_7_dates] or [1]) or 1
    for date in last_7_dates:
        day_tokens = daily_total.get(date, {}).get('tokens', 0)
        h_pct = (day_tokens / max_day_tokens * 100)
        day_label = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
        
        html += f"""                        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:10px">
                            <div style="font-size:10px;color:#10b981;font-weight:600">{fmt_tokens(day_tokens) if day_tokens>0 else ''}</div>
                            <div style="width:100%;background:#2a2a2a;border-radius:8px;height:100px;position:relative;overflow:hidden">
                                <div style="position:absolute;bottom:0;width:100%;height:{h_pct}%;background:linear-gradient(0deg,#059669,#10b981);border-radius:4px"></div>
                            </div>
                            <span style="font-size:11px;color:#6b7280;font-weight:500">{day_label}</span>
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
