"""Export modules for producing structured JSON and the interactive executive dashboard with Chart.js."""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from .config import OUTPUT_DASHBOARD, OUTPUT_JSON, WORKSPACE_DIR
from .models import Order

logger = logging.getLogger(__name__)

Optional_Path = Optional[Path]


class DashboardExporter:
    """Generates the master JSON analytics file and self-contained executive HTML dashboard."""

    def __init__(self, orders: List[Order], analytics: Dict[str, Any]):
        self.orders = orders
        self.analytics = analytics
        self.chart_js_path = (
            WORKSPACE_DIR / "node_modules" / "chart.js" / "dist" / "chart.umd.min.js"
        )

    def export_json(self, output_path: Optional_Path = None) -> Path:
        """Export full serialized orders and analytics payload to JSON."""
        target = output_path or OUTPUT_JSON
        payload = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "totalOrders": len(self.orders),
                "dateRange": {
                    "start": self.analytics.get("summary", {}).get(
                        "dateRangeStart", ""
                    ),
                    "end": self.analytics.get("summary", {}).get("dateRangeEnd", ""),
                },
            },
            "kpis": self.analytics.get("summary", {}),
            "yearly": self.analytics.get("yearly", []),
            "monthly": self.analytics.get("monthly", []),
            "timePatterns": self.analytics.get("time_patterns", {}),
            "categories": self.analytics.get("categories", []),
            "logistics": self.analytics.get("logistics", {}),
            "returns": self.analytics.get("returns", {}),
            "geography": self.analytics.get("geography", []),
            "topSplurges": self.analytics.get("top_splurges", []),
            "repeatPurchases": self.analytics.get("repeat_purchases", []),
            "priceBrackets": self.analytics.get("price_brackets", []),
            "orders": [o.to_dict() for o in self.orders],
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return target

    def export_html_dashboard(self, output_path: Optional_Path = None) -> Path:
        """Generate standalone, interactive, executive HTML dashboard with Chart.js."""
        target = output_path or OUTPUT_DASHBOARD
        orders_dict = [o.to_dict() for o in self.orders]
        orders_json = json.dumps(orders_dict, separators=(",", ":"), ensure_ascii=True)
        orders_json = orders_json.replace("&", "\\u0026").replace("</", "<\\/")

        analytics_json = json.dumps(
            self.analytics, separators=(",", ":"), ensure_ascii=True
        )
        analytics_json = analytics_json.replace("&", "\\u0026").replace("</", "<\\/")

        chart_js_content = ""
        if self.chart_js_path.exists():
            try:
                with open(self.chart_js_path, "r", encoding="utf-8") as f:
                    chart_js_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read local Chart.js: {e}")

        html_content = self._render_template(
            orders_json, analytics_json, chart_js_content
        )
        with open(target, "w", encoding="utf-8") as f:
            f.write(html_content)
        return target

    def _render_template(
        self, orders_json: str, analytics_json: str, chart_js_content: str
    ) -> str:
        """Render complete HTML template with embedded payload, Chart.js runtime, and client UI."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Amazon Order Analytics & Insights Dashboard</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      --background: #0b1120;
      --card: #1e293b;
      --foreground: #f8fafc;
      --muted-foreground: #94a3b8;
      --border: #334155;
      --primary: #f59e0b;
      --primary-foreground: #000000;
      --accent: #293548;
      --success: #10b981;
      --danger: #ef4444;
      --info: #3b82f6;
    }}
    html.light {{
      --background: #f8fafc;
      --card: #ffffff;
      --foreground: #0f172a;
      --muted-foreground: #64748b;
      --border: #e2e8f0;
      --primary: #d97706;
      --primary-foreground: #ffffff;
      --accent: #f1f5f9;
      --success: #059669;
      --danger: #dc2626;
      --info: #2563eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--background);
      color: var(--foreground);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 16px;
      line-height: 1.5;
    }}
    .tab-btn {{
      transition: all 0.15s ease-in-out;
      cursor: pointer;
      background: var(--card);
      color: var(--muted-foreground);
    }}
    .tab-btn:hover {{ color: var(--foreground); background: var(--accent); }}
    .tab-btn.active {{
      background: var(--primary);
      color: var(--primary-foreground);
      font-weight: 700;
    }}
    .stat-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 18px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      min-width: 0;
    }}
    .chart-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      display: flex;
      flex-direction: column;
      min-width: 0;
      overflow: hidden;
    }}
    .chart-container {{
      position: relative;
      width: 100%;
      min-width: 0;
    }}
    .chart-container canvas {{
      display: block;
      width: 100% !important;
      max-width: 100%;
    }}
    .h-chart-260 {{ height: 260px; min-height: 260px; }}
    .h-chart-280 {{ height: 280px; min-height: 280px; }}
    .h-chart-300 {{ height: 300px; min-height: 300px; }}
    .h-chart-320 {{ height: 320px; min-height: 320px; }}
    .h-chart-380 {{ height: 380px; min-height: 380px; }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .b-green {{ background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .b-red {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .b-yellow {{ background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .b-blue {{ background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }}
    .b-purple {{ background: rgba(139, 92, 246, 0.15); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.3); }}
    .b-gray {{ background: var(--accent); color: var(--muted-foreground); border: 1px solid var(--border); }}
    table {{ width: 100%; border-collapse: collapse; }}
    thead th {{
      text-align: left;
      padding: 10px 10px;
      border-bottom: 2px solid var(--border);
      font-size: 11px;
      font-weight: 700;
      color: var(--muted-foreground);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    tbody td {{
      padding: 8px 10px;
      border-bottom: 1px solid var(--border);
      font-size: 12px;
      vertical-align: middle;
    }}
    tbody tr:hover {{ background: var(--accent); }}
    tbody tr:last-child td {{ border-bottom: none; }}
    .inp {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 6px 10px;
      color: var(--foreground);
      font-size: 12px;
      outline: none;
    }}
    .inp:focus {{ border-color: var(--primary); }}
    .col-filter-inp {{
      width: 100%;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 3px 6px;
      color: var(--foreground);
      font-size: 11px;
      font-weight: normal;
      outline: none;
      margin-top: 4px;
      text-transform: none;
      letter-spacing: normal;
    }}
    .col-filter-inp:focus {{ border-color: var(--primary); }}
    .col-filter-sel {{
      width: 100%;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 3px 4px;
      color: var(--foreground);
      font-size: 11px;
      font-weight: normal;
      outline: none;
      margin-top: 4px;
      text-transform: none;
      letter-spacing: normal;
    }}
    .col-filter-sel:focus {{ border-color: var(--primary); }}
    .sortable-hdr {{
      cursor: pointer;
      user-select: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }}
    .sortable-hdr:hover {{ color: var(--primary); }}
    .sec-title {{ font-size: 15px; font-weight: 700; color: var(--foreground); margin-bottom: 2px; }}
    .sec-sub {{ font-size: 11px; color: var(--muted-foreground); margin-bottom: 12px; }}
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
    .item-drawer {{ display: none; background: rgba(0,0,0,0.25); padding: 8px 14px; border-radius: 6px; margin: 4px 0; }}
    .filter-chip {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: 11px;
      background: rgba(245, 158, 11, 0.15);
      color: var(--primary);
      border: 1px solid rgba(245, 158, 11, 0.3);
      font-weight: 600;
    }}
    .filter-chip button {{
      cursor: pointer;
      background: transparent;
      border: none;
      color: inherit;
      padding: 0;
      line-height: 1;
      font-size: 12px;
    }}
    .clickable-chart-hint {{
      font-size: 10px;
      color: var(--primary);
      margin-left: 6px;
      font-weight: 500;
      opacity: 0.9;
    }}
  </style>
  <script>
    {chart_js_content}
  </script>
</head>
<body>
  <!-- Header Bar -->
  <header class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5 pb-4 border-b border-[var(--border)]">
    <div>
      <div class="flex items-center gap-3">
        <h1 class="text-xl font-extrabold tracking-tight">&#x1F4E6; Amazon Order Analytics & Intelligence</h1>
        <span class="badge b-yellow">Executive Edition</span>
      </div>
      <p class="text-xs text-[var(--muted-foreground)] mt-1">
        Comprehensive portfolio breakdown &bull; <strong id="hdrTotalOrders" class="text-[var(--foreground)]">--</strong> orders &bull; 
        <strong id="hdrDateSpan" class="text-[var(--foreground)]">--</strong> &bull; 
        Harmonized across Order History, Digital Orders, Returns, and Refunds
      </p>
    </div>
    <!-- Quick Actions -->
    <div class="flex items-center gap-2">
      <button onclick="toggleTheme()" class="inp text-xs font-semibold px-3 py-1.5 flex items-center gap-1.5 cursor-pointer">
        <span id="themeIcon">&#x2600;&#xFE0F;</span> <span id="themeLabel">Light</span>
      </button>
      <button onclick="exportCSV()" class="inp text-xs font-semibold px-3 py-1.5 flex items-center gap-1.5 cursor-pointer hover:border-[var(--primary)]">
        &#x1F4E5; Export CSV
      </button>
      <button onclick="resetAllGlobalFilters()" class="inp text-xs font-semibold px-3 py-1.5 flex items-center gap-1.5 cursor-pointer hover:border-[var(--primary)]">
        &#x21BA; Reset All Filters
      </button>
    </div>
  </header>

  <!-- Interactive Filter Toolbar -->
  <section class="chart-card mb-5 p-3.5">
    <div class="flex flex-wrap items-center gap-2.5">
      <div class="flex-1 min-w-[200px]">
        <input id="fSearch" type="text" placeholder="&#x1F50D; Search title, order ID, ASIN, tracking..." class="inp w-full" oninput="onGlobalFilterChange()">
      </div>
      <select id="fYear" class="inp" onchange="onGlobalFilterChange()">
        <option id="optAllYears" value="">All Years</option>
      </select>
      <select id="fCategory" class="inp" onchange="onGlobalFilterChange()">
        <option value="">All Categories</option>
      </select>
      <select id="fType" class="inp" onchange="onGlobalFilterChange()">
        <option value="">All Order Types</option>
        <option value="Physical Retail">Physical Retail</option>
        <option value="Utility & Recharge">Utility & Recharge</option>
        <option value="Digital Subscription">Digital Subscription</option>
        <option value="Digital Content">Digital Content</option>
      </select>
      <select id="fStatus" class="inp" onchange="onGlobalFilterChange()">
        <option value="">All Statuses</option>
        <option value="Delivered">Delivered</option>
        <option value="Returned & Refunded">Returned & Refunded</option>
        <option value="Replaced / Exchanged">Replaced / Exchanged</option>
        <option value="Cancelled">Cancelled</option>
        <option value="In Transit / Arriving">In Transit / Arriving</option>
      </select>
      <select id="fCity" class="inp" onchange="onGlobalFilterChange()">
        <option value="">All Locations</option>
      </select>
      <div class="text-xs text-[var(--muted-foreground)] font-medium pl-2">
        Showing <strong id="lblFilteredCount" class="text-[var(--foreground)]">--</strong> orders (<span id="lblFilteredSpend">₹0</span>)
      </div>
    </div>
  </section>

  <!-- KPI Executive Cards Grid -->
  <section class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-5">
    <div class="stat-card">
      <p class="text-xs text-[var(--muted-foreground)] mb-1">Gross Spend</p>
      <p class="text-lg font-bold" id="kpiGross">&#x2014;</p>
      <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5" id="kpiGrossSub">&#x2014;</p>
    </div>
    <div class="stat-card">
      <p class="text-xs text-[var(--muted-foreground)] mb-1">Net Realized Spend</p>
      <p class="text-lg font-bold text-[#10b981]" id="kpiNet">&#x2014;</p>
      <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5" id="kpiNetSub">&#x2014;</p>
    </div>
    <div class="stat-card">
      <p class="text-xs text-[var(--muted-foreground)] mb-1">Total Orders</p>
      <p class="text-lg font-bold" id="kpiOrders">&#x2014;</p>
      <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5" id="kpiOrdersSub">&#x2014;</p>
    </div>
    <div class="stat-card">
      <p class="text-xs text-[var(--muted-foreground)] mb-1">Average Order (AOV)</p>
      <p class="text-lg font-bold text-[#3b82f6]" id="kpiAOV">&#x2014;</p>
      <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5" id="kpiAOVSub">&#x2014;</p>
    </div>
    <div class="stat-card">
      <p class="text-xs text-[var(--muted-foreground)] mb-1">Discounts Saved</p>
      <p class="text-lg font-bold text-[#f59e0b]" id="kpiDiscounts">&#x2014;</p>
      <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5" id="kpiDiscountsSub">&#x2014;</p>
    </div>
    <div class="stat-card">
      <p class="text-xs text-[var(--muted-foreground)] mb-1">Refunds Recovered</p>
      <p class="text-lg font-bold text-[#8b5cf6]" id="kpiRefunds">&#x2014;</p>
      <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5" id="kpiRefundsSub">&#x2014;</p>
    </div>
    <div class="stat-card">
      <p class="text-xs text-[var(--muted-foreground)] mb-1">Shipping Fees Paid</p>
      <p class="text-lg font-bold text-[#ec4899]" id="kpiShipping">&#x2014;</p>
      <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5" id="kpiShippingSub">&#x2014;</p>
    </div>
  </section>

  <!-- Tabs Navigation -->
  <nav class="flex gap-1.5 mb-4 flex-wrap border-b border-[var(--border)] pb-2">
    <button class="tab-btn active text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('overview')">&#x1F4CA; Executive Overview</button>
    <button class="tab-btn text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('trends')">&#x1F4C8; Financial Trends</button>
    <button class="tab-btn text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('categories')">&#x1F5C2; Category & Products</button>
    <button class="tab-btn text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('logistics')">&#x1F69A; Logistics & City</button>
    <button class="tab-btn text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('returns')">&#x1F504; Returns & Refunds</button>
    <button class="tab-btn text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('digital')">&#x1F4F1; Digital & Bills</button>
    <button class="tab-btn text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('orders')">&#x1F4CB; Orders Master Ledger</button>
    <button class="tab-btn text-xs font-semibold px-3.5 py-2 rounded-lg border border-[var(--border)]" onclick="switchTab('insights')">&#x1F4A1; Strategic Insights</button>
  </nav>

  <!-- TAB 1: EXECUTIVE OVERVIEW -->
  <main id="tab-overview" class="tab-pane">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p id="titleAnnualWaterfall" class="sec-title">&#x1F4C5; Annual Spending Trajectory</p>
          <span class="clickable-chart-hint">&#x2728; Click bar to filter orders</span>
        </div>
        <p class="sec-sub">Gross vs Net spend trajectory and annual order volume</p>
        <div class="chart-container h-chart-280">
          <canvas id="chartYearly"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x2696;&#xFE0F; Order Outcome & Lifecycle Distribution</p>
          <span class="clickable-chart-hint">&#x2728; Click slice to filter orders</span>
        </div>
        <p class="sec-sub">Delivered vs Cancelled vs Refunded vs Exchanged orders</p>
        <div class="chart-container h-chart-280">
          <canvas id="chartStatus"></canvas>
        </div>
      </div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x1F4CA; Category Spend Distribution</p>
          <span class="clickable-chart-hint">&#x2728; Click slice to filter orders</span>
        </div>
        <p class="sec-sub">Macro-category share of total wallet expenditure</p>
        <div class="chart-container h-chart-280">
          <canvas id="chartCategoryShare"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x1F3E2; Channel & Order Type Composition</p>
          <span class="clickable-chart-hint">&#x2728; Click slice to filter orders</span>
        </div>
        <p class="sec-sub">Physical Retail vs Utility Bills vs Prime Subscriptions vs Digital Content</p>
        <div class="chart-container h-chart-280">
          <canvas id="chartOrderType"></canvas>
        </div>
      </div>
    </div>
  </main>

  <!-- TAB 2: FINANCIAL TRENDS -->
  <main id="tab-trends" class="tab-pane hidden">
    <div class="chart-card mb-4">
      <div class="flex items-center justify-between mb-2">
        <div>
          <div class="flex items-center gap-2">
            <p class="sec-title">&#x1F4C8; Longitudinal Spend Velocity</p>
            <span class="clickable-chart-hint">&#x2728; Click point to filter orders</span>
          </div>
          <p class="sec-sub">Longitudinal expenditure tracking showing Prime Day & Diwali festival spikes</p>
        </div>
        <select id="tTrendGranularity" class="inp text-xs" onchange="renderTrendsTab()">
          <option value="month">Monthly</option>
          <option value="quarter">Quarterly</option>
          <option value="year">Yearly</option>
        </select>
      </div>
      <div class="chart-container h-chart-320">
        <canvas id="chartTimeSeries"></canvas>
      </div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x1F552; Purchasing Habits by Day of Week</p>
          <span class="clickable-chart-hint">&#x2728; Click weekday to filter</span>
        </div>
        <p class="sec-sub">Order frequency and total expenditure by weekday</p>
        <div class="chart-container h-chart-260">
          <canvas id="chartDayOfWeek"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x1F319; Time-of-Day Shopping Hours (IST)</p>
          <span class="clickable-chart-hint">&#x2728; Click hour to filter</span>
        </div>
        <p class="sec-sub">Distribution of order timestamps across 24 hours</p>
        <div class="chart-container h-chart-260">
          <canvas id="chartHourOfDay"></canvas>
        </div>
      </div>
    </div>
  </main>

  <!-- TAB 3: CATEGORY & PRODUCTS -->
  <main id="tab-categories" class="tab-pane hidden">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x1F5C2; Spend by Macro Category</p>
          <span class="clickable-chart-hint">&#x2728; Click bar to filter orders</span>
        </div>
        <p class="sec-sub">Aggregated spend across all classifications</p>
        <div class="chart-container h-chart-380">
          <canvas id="chartCategoryBars"></canvas>
        </div>
      </div>
      <div class="chart-card flex flex-col">
        <p class="sec-title">&#x1F3C5; Top 15 Highest-Value Purchases (Splurges)</p>
        <p class="sec-sub">Your biggest ticket items with direct links</p>
        <div id="lstTopSplurges" class="flex-1 overflow-y-auto max-h-[380px] pr-2"></div>
      </div>
    </div>
    <div class="chart-card mb-4">
      <p class="sec-title">&#x1F4DA; Comprehensive Category Performance Ledger</p>
      <p class="sec-sub">Click on any category row to filter the master orders table</p>
      <div class="overflow-x-auto">
        <table>
          <thead>
            <tr>
              <th style="padding-left:14px">Category</th>
              <th>Orders</th>
              <th>Items</th>
              <th>Gross Spend</th>
              <th>AOV</th>
              <th>Share</th>
              <th>Returns</th>
              <th>Cancellations</th>
            </tr>
          </thead>
          <tbody id="tblCategoryMetrics"></tbody>
        </table>
      </div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="chart-card">
        <p class="sec-title">&#x1F501; Most Frequently Repurchased Items</p>
        <p class="sec-sub">Items ordered across multiple transactions</p>
        <div id="lstRepeatPurchases" class="overflow-y-auto max-h-[280px]"></div>
      </div>
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x1F4B5; Order Price Tier Distribution</p>
          <span class="clickable-chart-hint">&#x2728; Click tier to filter</span>
        </div>
        <p class="sec-sub">Ticket size distribution from micro-purchases to major hardware</p>
        <div class="chart-container h-chart-260">
          <canvas id="chartPriceBrackets"></canvas>
        </div>
      </div>
    </div>
  </main>

  <!-- TAB 4: LOGISTICS & GEOGRAPHY -->
  <main id="tab-logistics" class="tab-pane hidden">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x1F69A; Carrier Distribution (Physical Shipments)</p>
          <span class="clickable-chart-hint">&#x2728; Click carrier to filter</span>
        </div>
        <p class="sec-sub">Amazon Transportation Services (ATS) vs 3PL Networks</p>
        <div class="chart-container h-chart-280">
          <canvas id="chartCarriers"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <p class="sec-title">&#x1F4CD; Geographic Delivery Timeline</p>
        <p class="sec-sub">Relocation stages and expenditure by city</p>
        <div id="lstCityTimeline" class="overflow-y-auto max-h-[280px]"></div>
      </div>
    </div>
    <div class="chart-card">
      <p class="sec-title">&#x1F4DD; Carrier Performance Summary</p>
      <div class="overflow-x-auto">
        <table>
          <thead>
            <tr>
              <th style="padding-left:14px">Carrier Name</th>
              <th>Shipment Count</th>
              <th>Share of Logistics</th>
            </tr>
          </thead>
          <tbody id="tblCarriers"></tbody>
        </table>
      </div>
    </div>
  </main>

  <!-- TAB 5: RETURNS & REFUNDS -->
  <main id="tab-returns" class="tab-pane hidden">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x26A0;&#xFE0F; Return Reasons</p>
          <span class="clickable-chart-hint">&#x2728; Click slice</span>
        </div>
        <p class="sec-sub">Root causes behind returns</p>
        <div class="chart-container h-chart-260">
          <canvas id="chartReturnReasons"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="flex items-center justify-between">
          <p class="sec-title">&#x2696;&#xFE0F; Resolution Breakdown</p>
          <span class="clickable-chart-hint">&#x2728; Click slice</span>
        </div>
        <p class="sec-sub">Refunds vs Exchanges</p>
        <div class="chart-container h-chart-260">
          <canvas id="chartReturnResolutions"></canvas>
        </div>
      </div>
      <div class="chart-card flex flex-col">
        <p class="sec-title">&#x1F504; Replacement Orders Linked</p>
        <p class="sec-sub">Original orders replaced with new shipments</p>
        <div id="lstReplacementLinks" class="flex-1 overflow-y-auto max-h-[260px] text-xs"></div>
      </div>
    </div>

    <!-- Complete Returns & Refund Ledger with Column Filters -->
    <div id="tblReturnsLedgerCard" class="chart-card" style="padding:0">
      <div class="p-3 border-b border-[var(--border)] flex items-center justify-between flex-wrap gap-2">
        <div>
          <p class="sec-title">&#x1F4DC; Complete Returns & Refund Ledger</p>
          <p class="sec-sub" style="margin-bottom:0">Full audit trail with column-level interactive filters</p>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="resetReturnsFilters()" class="text-xs px-2.5 py-1 rounded bg-[var(--card)] hover:bg-[var(--accent)] text-[var(--muted-foreground)] border border-[var(--border)] cursor-pointer">
            &#x21BA; Reset Return Filters
          </button>
          <div class="text-xs text-[var(--muted-foreground)]">
            Showing <strong id="lblReturnsCount" class="text-[var(--foreground)]">30</strong> records (<span id="lblReturnsSum" class="text-[var(--primary)] font-semibold">₹0</span>)
          </div>
        </div>
      </div>

      <!-- Active Filters Chips for Returns -->
      <div id="returnsActiveChips" class="px-3 py-2 bg-[var(--accent)] border-b border-[var(--border)] flex flex-wrap items-center gap-1.5 hidden">
        <span class="text-xs font-semibold text-[var(--muted-foreground)]">Active Filters:</span>
        <div id="returnsChipsContainer" class="flex flex-wrap items-center gap-1.5"></div>
      </div>

      <div class="overflow-x-auto max-h-[500px]">
        <table>
          <thead>
            <tr>
              <th style="padding-left:14px; min-width:110px">
                <div class="sortable-hdr" onclick="sortReturnsBy('date')">
                  <span>DATE</span> <span id="sortRetIcon_date">&#x21C5;</span>
                </div>
                <input id="retColDate" type="text" placeholder="Filter..." class="col-filter-inp" oninput="applyReturnsFilters()">
              </th>
              <th style="min-width:130px">
                <div class="sortable-hdr" onclick="sortReturnsBy('orderId')">
                  <span>ORDER ID</span> <span id="sortRetIcon_orderId">&#x21C5;</span>
                </div>
                <input id="retColOrderId" type="text" placeholder="Filter ID..." class="col-filter-inp" oninput="applyReturnsFilters()">
              </th>
              <th style="min-width:180px">
                <div class="sortable-hdr" onclick="sortReturnsBy('itemTitle')">
                  <span>PRODUCT / DESCRIPTION</span> <span id="sortRetIcon_itemTitle">&#x21C5;</span>
                </div>
                <input id="retColProduct" type="text" placeholder="Filter product..." class="col-filter-inp" oninput="applyReturnsFilters()">
              </th>
              <th style="min-width:130px">
                <div class="sortable-hdr" onclick="sortReturnsBy('category')">
                  <span>CATEGORY</span> <span id="sortRetIcon_category">&#x21C5;</span>
                </div>
                <select id="retColCategory" class="col-filter-sel" onchange="applyReturnsFilters()">
                  <option value="">All Categories</option>
                </select>
              </th>
              <th style="min-width:140px">
                <div class="sortable-hdr" onclick="sortReturnsBy('reason')">
                  <span>REASON</span> <span id="sortRetIcon_reason">&#x21C5;</span>
                </div>
                <select id="retColReason" class="col-filter-sel" onchange="applyReturnsFilters()">
                  <option value="">All Reasons</option>
                </select>
              </th>
              <th style="min-width:110px">
                <div class="sortable-hdr" onclick="sortReturnsBy('resolution')">
                  <span>RESOLUTION</span> <span id="sortRetIcon_resolution">&#x21C5;</span>
                </div>
                <select id="retColResolution" class="col-filter-sel" onchange="applyReturnsFilters()">
                  <option value="">All</option>
                  <option value="Refund">Refund</option>
                  <option value="Exchange">Exchange</option>
                </select>
              </th>
              <th style="min-width:120px; text-align:right; padding-right:14px">
                <div class="sortable-hdr justify-end" onclick="sortReturnsBy('refundAmount')">
                  <span>REFUND AMOUNT</span> <span id="sortRetIcon_refundAmount">&#x21C5;</span>
                </div>
                <select id="retColAmount" class="col-filter-sel" onchange="applyReturnsFilters()">
                  <option value="">All</option>
                  <option value="refund">Refunded (&gt; ₹0)</option>
                  <option value="exchange">Exchange Only</option>
                </select>
              </th>
            </tr>
          </thead>
          <tbody id="tblReturnsLedger"></tbody>
        </table>
      </div>
    </div>
  </main>

  <!-- TAB 6: DIGITAL & UTILITIES -->
  <main id="tab-digital" class="tab-pane hidden">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <div class="chart-card">
        <p class="sec-title">&#x1F4F1; Mobile & Utility Recharges</p>
        <p class="sec-sub">Prepaid mobile recharges and electricity bill payments</p>
        <div id="lstUtilitySummary" class="text-xs mb-3"></div>
        <div class="overflow-y-auto max-h-[300px]">
          <table>
            <thead>
              <tr>
                <th style="padding-left:14px">Date</th>
                <th>Order ID</th>
                <th>Utility Type</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody id="tblUtilityLedger"></tbody>
          </table>
        </div>
      </div>
      <div class="chart-card">
        <p class="sec-title">&#x1F4D6; Digital Media, Books & Subscriptions</p>
        <p class="sec-sub">Kindle Unlimited, Audible audiobooks, and Prime memberships</p>
        <div id="lstDigitalSummary" class="text-xs mb-3"></div>
        <div class="overflow-y-auto max-h-[300px]">
          <table>
            <thead>
              <tr>
                <th style="padding-left:14px">Date</th>
                <th>Title / Subscription</th>
                <th>Format</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody id="tblDigitalLedger"></tbody>
          </table>
        </div>
      </div>
    </div>
  </main>

  <!-- TAB 7: MASTER ORDER LEDGER -->
  <main id="tab-orders" class="tab-pane hidden">
    <div class="chart-card" style="padding:0">
      <div class="p-3 border-b border-[var(--border)] flex items-center justify-between flex-wrap gap-2">
        <div>
          <p class="sec-title">&#x1F4CB; Orders Master Ledger</p>
          <p class="sec-sub" style="margin-bottom:0">Multi-column filtered view &bull; click on order IDs for external records</p>
        </div>
        <div class="flex items-center gap-3">
          <button onclick="resetColFilters()" class="text-xs px-2.5 py-1 rounded bg-[var(--card)] hover:bg-[var(--accent)] text-[var(--muted-foreground)] border border-[var(--border)] cursor-pointer">
            &#x21BA; Reset Column Filters
          </button>
          <div class="text-xs text-[var(--muted-foreground)]">
            Page <strong id="lblCurrentPage" class="text-[var(--foreground)]">1</strong> of <strong id="lblTotalPages" class="text-[var(--foreground)]">1</strong>
          </div>
        </div>
      </div>

      <!-- Active Filters Chips for Orders -->
      <div id="ordersActiveChips" class="px-3 py-2 bg-[var(--accent)] border-b border-[var(--border)] flex flex-wrap items-center gap-1.5 hidden">
        <span class="text-xs font-semibold text-[var(--muted-foreground)]">Active Filters:</span>
        <div id="ordersChipsContainer" class="flex flex-wrap items-center gap-1.5"></div>
      </div>

      <div class="overflow-x-auto">
        <table>
          <thead>
            <tr>
              <th style="padding-left:14px; min-width:110px">
                <div class="sortable-hdr" onclick="sortOrdersBy('date')">
                  <span>DATE</span> <span id="sortOrdIcon_date">&#x21C5;</span>
                </div>
                <input id="ordColDate" type="text" placeholder="YYYY-MM..." class="col-filter-inp" oninput="applyColFilters()">
              </th>
              <th style="min-width:130px">
                <div class="sortable-hdr" onclick="sortOrdersBy('orderId')">
                  <span>ORDER ID</span> <span id="sortOrdIcon_orderId">&#x21C5;</span>
                </div>
                <input id="ordColOrderId" type="text" placeholder="Filter ID..." class="col-filter-inp" oninput="applyColFilters()">
              </th>
              <th style="min-width:200px">
                <div class="sortable-hdr" onclick="sortOrdersBy('item')">
                  <span>ITEMS & DETAILS</span> <span id="sortOrdIcon_item">&#x21C5;</span>
                </div>
                <input id="ordColItem" type="text" placeholder="Filter title/ASIN..." class="col-filter-inp" oninput="applyColFilters()">
              </th>
              <th style="min-width:130px">
                <div class="sortable-hdr" onclick="sortOrdersBy('category')">
                  <span>CATEGORY</span> <span id="sortOrdIcon_category">&#x21C5;</span>
                </div>
                <select id="ordColCategory" class="col-filter-sel" onchange="applyColFilters()">
                  <option value="">All Categories</option>
                </select>
              </th>
              <th style="min-width:110px; text-align:right">
                <div class="sortable-hdr justify-end" onclick="sortOrdersBy('amount')">
                  <span>AMOUNT</span> <span id="sortOrdIcon_amount">&#x21C5;</span>
                </div>
                <select id="ordColAmount" class="col-filter-sel" onchange="applyColFilters()">
                  <option value="">All Tiers</option>
                  <option value="0-500">&lt; ₹500</option>
                  <option value="500-2000">₹500 - ₹2K</option>
                  <option value="2000-10000">₹2K - ₹10K</option>
                  <option value="10000+">&gt; ₹10K</option>
                </select>
              </th>
              <th style="min-width:130px">
                <div class="sortable-hdr" onclick="sortOrdersBy('status')">
                  <span>STATUS</span> <span id="sortOrdIcon_status">&#x21C5;</span>
                </div>
                <select id="ordColStatus" class="col-filter-sel" onchange="applyColFilters()">
                  <option value="">All Statuses</option>
                  <option value="Delivered">Delivered</option>
                  <option value="Returned & Refunded">Returned & Refunded</option>
                  <option value="Replaced / Exchanged">Replaced / Exchanged</option>
                  <option value="Cancelled">Cancelled</option>
                  <option value="In Transit / Arriving">In Transit</option>
                </select>
              </th>
              <th style="min-width:110px">
                <div class="sortable-hdr" onclick="sortOrdersBy('city')">
                  <span>LOCATION</span> <span id="sortOrdIcon_city">&#x21C5;</span>
                </div>
                <select id="ordColCity" class="col-filter-sel" onchange="applyColFilters()">
                  <option value="">All Locations</option>
                </select>
              </th>
              <th style="min-width:90px; text-align:right; padding-right:14px">
                <div class="sortable-hdr justify-end" onclick="sortOrdersBy('discount')">
                  <span>SAVINGS</span> <span id="sortOrdIcon_discount">&#x21C5;</span>
                </div>
                <select id="ordColDiscount" class="col-filter-sel" onchange="applyColFilters()">
                  <option value="">All</option>
                  <option value="discounted">With Discounts</option>
                </select>
              </th>
            </tr>
          </thead>
          <tbody id="tblOrdersMaster"></tbody>
        </table>
      </div>
      <!-- Pagination Controls -->
      <div class="p-3 border-t border-[var(--border)] flex items-center justify-center gap-2" id="divPagination"></div>
    </div>
  </main>

  <!-- TAB 8: STRATEGIC ANALYST INSIGHTS -->
  <main id="tab-insights" class="tab-pane hidden">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
      <div class="chart-card">
        <p class="sec-title">&#x1F3C6; Key Behavioral & Spending Observations</p>
        <p class="sec-sub">Dynamically calculated behavioral insights across your order history</p>
        <div id="lstBehavioralInsights" class="space-y-3 mt-1 text-xs leading-relaxed text-[var(--muted-foreground)]"></div>
      </div>
      <div class="chart-card">
        <p class="sec-title">&#x1F4CA; Seasonality, Geography & Lifecycle Patterns</p>
        <p class="sec-sub">Longitudinal patterns across timeline, locations, and return resolutions</p>
        <div id="lstSeasonalityInsights" class="space-y-3 mt-1 text-xs leading-relaxed text-[var(--muted-foreground)]"></div>
      </div>
    </div>
  </main>

  <!-- Embedded Datasets and Client Application Logic -->
  <script>
    const MASTER_ORDERS = {orders_json};
    const MASTER_ANALYTICS = {analytics_json};

    // Client State
    let filteredOrders = [...MASTER_ORDERS];
    let currentPage = 1;
    const PAGE_SIZE = 20;
    const activeCharts = {{}};

    // Orders Ledger Sorting & Column Filter State
    let ordersSortCol = 'date';
    let ordersSortDir = 'desc';
    const colFilters = {{
      date: '',
      orderId: '',
      item: '',
      category: '',
      amount: '',
      status: '',
      city: '',
      discount: '',
      weekday: null,
      priceTier: null,
      hour: null,
      carrier: null
    }};

    // Returns Ledger Sorting & Column Filter State
    let returnsSortCol = 'date';
    let returnsSortDir = 'desc';
    const returnsFilters = {{
      date: '',
      orderId: '',
      product: '',
      category: '',
      reason: '',
      resolution: '',
      amount: ''
    }};

    // Clean Indian Rupee Currency Formatter
    const fmt = n => '₹' + Math.round(n || 0).toLocaleString('en-IN');
    const fmtK = n => {{
      n = Math.round(n || 0);
      if (n >= 100000) return '₹' + (n / 100000).toFixed(1) + 'L';
      if (n >= 1000) return '₹' + (n / 1000).toFixed(1) + 'K';
      return '₹' + n;
    }};
    const formatYearMonth = ym => {{
      if (!ym) return '';
      const parts = String(ym).split('-');
      if (parts.length === 2) {{
        const yr = parseInt(parts[0], 10);
        const mo = parseInt(parts[1], 10);
        if (!isNaN(yr) && !isNaN(mo) && mo >= 1 && mo <= 12) {{
          const dt = new Date(yr, mo - 1, 1);
          return dt.toLocaleDateString('en-US', {{ month: 'long', year: 'numeric' }});
        }}
      }}
      return String(ym);
    }};

    // Theme color helper
    const isLight = () => document.documentElement.classList.contains('light');
    const getGridColor = () => isLight() ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.06)';
    const getTextColor = () => isLight() ? '#64748b' : '#94a3b8';

    // Color definitions
    const COLORS = ['#f59e0b', '#3b82f6', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'];
    const CAT_COLORS = {{
      'PC Hardware & Gaming': '#3b82f6',
      'Utilities & Recharges': '#f59e0b',
      'General Merchandise': '#94a3b8',
      'Home & Office Furniture': '#10b981',
      'Mobile & Smart Devices': '#06b6d4',
      'Digital Services & Subscriptions': '#8b5cf6',
      'Appliances & Utilities': '#f97316',
      'DIY Electronics & Maker': '#ec4899',
      'Personal Care & Grooming': '#ef4444',
      'Apparel & Fashion': '#6366f1',
      'Smart Home & Networking': '#14b8a6',
      'Kitchen & Dining': '#84cc16',
      'Books & Media': '#eab308',
      'Automotive & Safety': '#64748b',
    }};

    // Dynamic Chart Manager with explicit sizing and pointer cursor
    function renderOrUpdateChart(canvasId, config) {{
      const canvas = document.getElementById(canvasId);
      if (!canvas) return null;
      if (activeCharts[canvasId]) {{
        activeCharts[canvasId].destroy();
        delete activeCharts[canvasId];
      }}

      if (!config.options) config.options = {{}};
      config.options.responsive = true;
      config.options.maintainAspectRatio = false;
      config.options.resizeDelay = 20;
      config.options.animation = {{ duration: 350 }};

      // Ensure cursor changes to pointer on hover over interactive elements
      const origOnHover = config.options.onHover;
      config.options.onHover = (event, elements, chart) => {{
        if (event && event.native && event.native.target) {{
          event.native.target.style.cursor = (elements && elements.length) ? 'pointer' : 'default';
        }}
        if (origOnHover) origOnHover(event, elements, chart);
      }};

      try {{
        activeCharts[canvasId] = new Chart(canvas, config);
        return activeCharts[canvasId];
      }} catch (err) {{
        console.error('Error rendering chart ' + canvasId + ':', err);
        return null;
      }}
    }}

    // Filter Toast Notification
    function showFilterToast(msg) {{
      let toast = document.getElementById('filterToast');
      if (!toast) {{
        toast = document.createElement('div');
        toast.id = 'filterToast';
        toast.className = 'fixed bottom-5 right-5 z-50 bg-[#1e293b] text-white px-4 py-2.5 rounded-lg shadow-2xl border border-[#f59e0b] text-xs font-semibold flex items-center gap-2 transition-all duration-300 transform translate-y-10 opacity-0 pointer-events-none';
        document.body.appendChild(toast);
      }}
      toast.innerHTML = `<span class="text-[#f59e0b] text-base">&#x26A1;</span> <span>${{msg}}</span>`;
      toast.classList.remove('translate-y-10', 'opacity-0', 'pointer-events-none');
      if (window._toastTimer) clearTimeout(window._toastTimer);
      window._toastTimer = setTimeout(() => {{
        toast.classList.add('translate-y-10', 'opacity-0', 'pointer-events-none');
      }}, 3200);
    }}

    // Initialization
    function init() {{
      const elTotal = document.getElementById('hdrTotalOrders');
      if (elTotal) elTotal.textContent = MASTER_ORDERS.length;
      const elSpan = document.getElementById('hdrDateSpan');
      const optAllYears = document.getElementById('optAllYears');
      const titleWaterfall = document.getElementById('titleAnnualWaterfall');
      const yrs = [...new Set(MASTER_ORDERS.map(o => o.orderDate ? o.orderDate.slice(0, 4) : '').filter(Boolean))].sort();
      if (yrs.length) {{
        const spanText = yrs.length === 1 ? yrs[0] : `${{yrs[0]}} - ${{yrs[yrs.length - 1]}}`;
        if (elSpan) elSpan.textContent = spanText;
        if (optAllYears) optAllYears.textContent = `All Years (${{spanText}})`;
        if (titleWaterfall) titleWaterfall.innerHTML = `&#x1F4C5; Annual Spending Trajectory (${{spanText}})`;
      }} else {{
        if (elSpan) elSpan.textContent = 'No Dates';
      }}
      populateDropdowns();
      applyFilters();
    }}

    function populateDropdowns() {{
      const years = [...new Set(MASTER_ORDERS.map(o => o.orderDate ? o.orderDate.slice(0, 4) : '').filter(Boolean))].sort().reverse();
      const selYear = document.getElementById('fYear');
      years.forEach(y => {{
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = 'Year: ' + y;
        selYear.appendChild(opt);
      }});

      const cats = [...new Set(MASTER_ORDERS.map(o => o.category).filter(Boolean))].sort();
      const selCat = document.getElementById('fCategory');
      const ordColCat = document.getElementById('ordColCategory');
      const retColCat = document.getElementById('retColCategory');

      cats.forEach(c => {{
        const o1 = document.createElement('option');
        o1.value = c; o1.textContent = c;
        selCat.appendChild(o1);

        const o2 = document.createElement('option');
        o2.value = c; o2.textContent = c;
        ordColCat.appendChild(o2);

        const o3 = document.createElement('option');
        o3.value = c; o3.textContent = c;
        retColCat.appendChild(o3);
      }});

      const cities = [...new Set(MASTER_ORDERS.map(o => o.city).filter(c => c && c !== 'Not Available' && c !== 'Digital'))].sort();
      const selCity = document.getElementById('fCity');
      const ordColCity = document.getElementById('ordColCity');
      cities.forEach(c => {{
        const o1 = document.createElement('option');
        o1.value = c; o1.textContent = c;
        selCity.appendChild(o1);

        const o2 = document.createElement('option');
        o2.value = c; o2.textContent = c;
        ordColCity.appendChild(o2);
      }});

      // Populate Return Reasons
      const retRecords = (MASTER_ANALYTICS.returns && MASTER_ANALYTICS.returns.returnRecords) || [];
      const distinctReasons = [...new Set(retRecords.map(r => r.reason).filter(Boolean))].sort();
      const retColReason = document.getElementById('retColReason');
      distinctReasons.forEach(r => {{
        const opt = document.createElement('option');
        opt.value = r; opt.textContent = r;
        retColReason.appendChild(opt);
      }});
    }}

    function onGlobalFilterChange() {{
      applyFilters();
    }}

    function applyFilters() {{
      const q = (document.getElementById('fSearch').value || '').toLowerCase().trim();
      const y = document.getElementById('fYear').value;
      const c = document.getElementById('fCategory').value;
      const t = document.getElementById('fType').value;
      const s = document.getElementById('fStatus').value;
      const city = document.getElementById('fCity').value;

      filteredOrders = MASTER_ORDERS.filter(o => {{
        if (y && (!o.orderDate || !o.orderDate.startsWith(y))) return false;
        if (c && o.category !== c) return false;
        if (t && o.orderType !== t) return false;
        if (s && o.status !== s) return false;
        if (city && o.city !== city) return false;
        if (q) {{
          const inId = (o.orderId || '').toLowerCase().includes(q);
          const inCat = (o.category || '').toLowerCase().includes(q);
          const inTrack = (o.trackingNumber || '').toLowerCase().includes(q);
          const inItem = (o.items || []).some(it => (it.title || '').toLowerCase().includes(q) || (it.asin || '').toLowerCase().includes(q));
          if (!inId && !inCat && !inTrack && !inItem) return false;
        }}

        // Additional chart-click / column constraints
        if (colFilters.weekday !== null) {{
          if (!o.orderDate) return false;
          const dow = (new Date(o.orderDate).getDay() + 6) % 7;
          if (dow !== colFilters.weekday) return false;
        }}
        if (colFilters.hour !== null) {{
          if (!o.orderDate || o.orderDate.length < 13) return false;
          const hr = parseInt(o.orderDate.slice(11, 13));
          if (hr !== colFilters.hour) return false;
        }}
        if (colFilters.priceTier) {{
          const amt = o.totalAmount;
          if (colFilters.priceTier === '<₹200' && amt >= 200) return false;
          if (colFilters.priceTier === '₹200-500' && (amt < 200 || amt >= 500)) return false;
          if (colFilters.priceTier === '₹500-1K' && (amt < 500 || amt >= 1000)) return false;
          if (colFilters.priceTier === '₹1K-2.5K' && (amt < 1000 || amt >= 2500)) return false;
          if (colFilters.priceTier === '₹2.5K-5K' && (amt < 2500 || amt >= 5000)) return false;
          if (colFilters.priceTier === '₹5K-10K' && (amt < 5000 || amt >= 10000)) return false;
          if (colFilters.priceTier === '>₹10K' && amt < 10000) return false;
        }}
        if (colFilters.carrier) {{
          if (o.carrier !== colFilters.carrier) return false;
        }}

        // Inline Column Filters for Orders Master
        if (colFilters.date && (!o.orderDate || !o.orderDate.includes(colFilters.date))) return false;
        if (colFilters.orderId && (!o.orderId || !o.orderId.toLowerCase().includes(colFilters.orderId))) return false;
        if (colFilters.item) {{
          const matchItem = (o.items || []).some(it => (it.title || '').toLowerCase().includes(colFilters.item) || (it.asin || '').toLowerCase().includes(colFilters.item));
          if (!matchItem) return false;
        }}
        if (colFilters.category && o.category !== colFilters.category) return false;
        if (colFilters.status && o.status !== colFilters.status) return false;
        if (colFilters.city && o.city !== colFilters.city) return false;
        if (colFilters.discount === 'discounted' && (!o.discount || o.discount <= 0)) return false;
        if (colFilters.amount) {{
          const amt = o.totalAmount;
          if (colFilters.amount === '0-500' && amt >= 500) return false;
          if (colFilters.amount === '500-2000' && (amt < 500 || amt >= 2000)) return false;
          if (colFilters.amount === '2000-10000' && (amt < 2000 || amt >= 10000)) return false;
          if (colFilters.amount === '10000+' && amt < 10000) return false;
        }}

        return true;
      }});

      currentPage = 1;
      updateHeaderKPIs();
      renderOrdersActiveFilterChips();
      renderActiveTab();
    }}

    function resetAllGlobalFilters() {{
      document.getElementById('fSearch').value = '';
      document.getElementById('fYear').value = '';
      document.getElementById('fCategory').value = '';
      document.getElementById('fType').value = '';
      document.getElementById('fStatus').value = '';
      document.getElementById('fCity').value = '';
      resetColFilters(false);
      resetReturnsFilters();
      applyFilters();
      showFilterToast('All filters have been reset');
    }}

    // Column Filters in Master Orders Table
    function applyColFilters() {{
      colFilters.date = (document.getElementById('ordColDate').value || '').trim();
      colFilters.orderId = (document.getElementById('ordColOrderId').value || '').toLowerCase().trim();
      colFilters.item = (document.getElementById('ordColItem').value || '').toLowerCase().trim();
      colFilters.category = document.getElementById('ordColCategory').value;
      colFilters.amount = document.getElementById('ordColAmount').value;
      colFilters.status = document.getElementById('ordColStatus').value;
      colFilters.city = document.getElementById('ordColCity').value;
      colFilters.discount = document.getElementById('ordColDiscount').value;
      applyFilters();
    }}

    function resetColFilters(triggerApply = true) {{
      colFilters.date = '';
      colFilters.orderId = '';
      colFilters.item = '';
      colFilters.category = '';
      colFilters.amount = '';
      colFilters.status = '';
      colFilters.city = '';
      colFilters.discount = '';
      colFilters.weekday = null;
      colFilters.priceTier = null;
      colFilters.hour = null;
      colFilters.carrier = null;

      const setVal = (id, val) => {{ const el = document.getElementById(id); if (el) el.value = val; }};
      setVal('ordColDate', '');
      setVal('ordColOrderId', '');
      setVal('ordColItem', '');
      setVal('ordColCategory', '');
      setVal('ordColAmount', '');
      setVal('ordColStatus', '');
      setVal('ordColCity', '');
      setVal('ordColDiscount', '');

      if (triggerApply) {{
        applyFilters();
        showFilterToast('Column filters cleared');
      }}
    }}

    function removeSingleOrderFilter(key) {{
      if (key === 'year') {{ document.getElementById('fYear').value = ''; }}
      else if (key === 'category') {{ document.getElementById('fCategory').value = ''; colFilters.category = ''; document.getElementById('ordColCategory').value = ''; }}
      else if (key === 'status') {{ document.getElementById('fStatus').value = ''; colFilters.status = ''; document.getElementById('ordColStatus').value = ''; }}
      else if (key === 'city') {{ document.getElementById('fCity').value = ''; colFilters.city = ''; document.getElementById('ordColCity').value = ''; }}
      else if (key === 'type') {{ document.getElementById('fType').value = ''; }}
      else if (key === 'weekday') {{ colFilters.weekday = null; }}
      else if (key === 'priceTier') {{ colFilters.priceTier = null; }}
      else if (key === 'hour') {{ colFilters.hour = null; }}
      else if (key === 'carrier') {{ colFilters.carrier = null; }}
      else if (key === 'search') {{ document.getElementById('fSearch').value = ''; }}
      else if (key === 'ordDate') {{ colFilters.date = ''; document.getElementById('ordColDate').value = ''; }}
      else if (key === 'ordId') {{ colFilters.orderId = ''; document.getElementById('ordColOrderId').value = ''; }}
      else if (key === 'ordItem') {{ colFilters.item = ''; document.getElementById('ordColItem').value = ''; }}
      else if (key === 'ordAmount') {{ colFilters.amount = ''; document.getElementById('ordColAmount').value = ''; }}
      else if (key === 'ordDiscount') {{ colFilters.discount = ''; document.getElementById('ordColDiscount').value = ''; }}
      applyFilters();
    }}

    function renderOrdersActiveFilterChips() {{
      const container = document.getElementById('ordersChipsContainer');
      const bar = document.getElementById('ordersActiveChips');
      if (!container || !bar) return;

      const chips = [];
      const y = document.getElementById('fYear').value;
      if (y) chips.push({{ key: 'year', label: `Year: ${{y}}` }});

      const cat = document.getElementById('fCategory').value || colFilters.category;
      if (cat) chips.push({{ key: 'category', label: `Category: ${{cat}}` }});

      const st = document.getElementById('fStatus').value || colFilters.status;
      if (st) chips.push({{ key: 'status', label: `Status: ${{st}}` }});

      const cty = document.getElementById('fCity').value || colFilters.city;
      if (cty) chips.push({{ key: 'city', label: `Location: ${{cty}}` }});

      const tp = document.getElementById('fType').value;
      if (tp) chips.push({{ key: 'type', label: `Type: ${{tp}}` }});

      if (colFilters.weekday !== null) {{
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        chips.push({{ key: 'weekday', label: `Day: ${{days[colFilters.weekday]}}` }});
      }}
      if (colFilters.priceTier) {{
        chips.push({{ key: 'priceTier', label: `Price Tier: ${{colFilters.priceTier}}` }});
      }}
      if (colFilters.hour !== null) {{
        chips.push({{ key: 'hour', label: `Hour: ${{colFilters.hour}}:00 IST` }});
      }}
      if (colFilters.carrier) {{
        chips.push({{ key: 'carrier', label: `Carrier: ${{colFilters.carrier}}` }});
      }}
      if (colFilters.date) chips.push({{ key: 'ordDate', label: `Date Match: "${{colFilters.date}}"` }});
      if (colFilters.orderId) chips.push({{ key: 'ordId', label: `ID: "${{colFilters.orderId}}"` }});
      if (colFilters.item) chips.push({{ key: 'ordItem', label: `Item: "${{colFilters.item}}"` }});
      if (colFilters.amount) chips.push({{ key: 'ordAmount', label: `Amount: ${{colFilters.amount}}` }});
      if (colFilters.discount) chips.push({{ key: 'ordDiscount', label: `Has Discounts` }});

      const q = document.getElementById('fSearch').value.trim();
      if (q) chips.push({{ key: 'search', label: `Search: "${{q}}"` }});

      if (chips.length === 0) {{
        bar.classList.add('hidden');
        container.innerHTML = '';
      }} else {{
        bar.classList.remove('hidden');
        container.innerHTML = chips.map(c => `
          <span class="filter-chip">
            <span>${{c.label}}</span>
            <button onclick="removeSingleOrderFilter('${{c.key}}')" title="Remove filter">&times;</button>
          </span>
        `).join('') + `
          <button onclick="resetColFilters()" class="text-[11px] text-[var(--muted-foreground)] hover:text-[var(--danger)] underline ml-2 cursor-pointer">Clear Table Filters</button>
        `;
      }}
    }}

    // Direct Chart-to-Orders Filter Navigator
    function filterAndJumpToOrders(params, toastMsg) {{
      if (params.year !== undefined) {{
        document.getElementById('fYear').value = params.year;
      }}
      if (params.category !== undefined) {{
        document.getElementById('fCategory').value = params.category;
        colFilters.category = params.category;
        const ordCat = document.getElementById('ordColCategory');
        if (ordCat) ordCat.value = params.category;
      }}
      if (params.status !== undefined) {{
        document.getElementById('fStatus').value = params.status;
        colFilters.status = params.status;
        const ordSt = document.getElementById('ordColStatus');
        if (ordSt) ordSt.value = params.status;
      }}
      if (params.type !== undefined) {{
        document.getElementById('fType').value = params.type;
      }}
      if (params.city !== undefined) {{
        document.getElementById('fCity').value = params.city;
        colFilters.city = params.city;
        const ordCity = document.getElementById('ordColCity');
        if (ordCity) ordCity.value = params.city;
      }}
      if (params.ordId !== undefined) {{
        colFilters.orderId = params.ordId.toLowerCase();
        const ordIdInput = document.getElementById('ordColOrderId');
        if (ordIdInput) ordIdInput.value = params.ordId;
      }}
      if (params.weekday !== undefined) {{
        const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        if (typeof params.weekday === 'string') {{
          const di = dayNames.indexOf(params.weekday);
          colFilters.weekday = di !== -1 ? di : null;
        }} else {{
          colFilters.weekday = params.weekday;
        }}
      }}
      if (params.priceTier !== undefined) {{
        colFilters.priceTier = params.priceTier;
      }}
      if (params.hour !== undefined) {{
        colFilters.hour = params.hour;
      }}
      if (params.carrier !== undefined) {{
        colFilters.carrier = params.carrier;
      }}
      if (params.dateMonth !== undefined) {{
        colFilters.date = params.dateMonth;
        const el = document.getElementById('ordColDate');
        if (el) el.value = params.dateMonth;
      }}

      applyFilters();
      switchTab('orders');
      if (toastMsg) showFilterToast(toastMsg);
    }}

    function updateHeaderKPIs() {{
      const gross = filteredOrders.reduce((s, o) => s + o.totalAmount, 0);
      const cancelled = filteredOrders.filter(o => o.status === 'Cancelled');
      const cancSpend = cancelled.reduce((s, o) => s + o.totalAmount, 0);
      const refunded = filteredOrders.filter(o => o.status === 'Returned & Refunded');
      const refAmt = refunded.reduce((s, o) => s + (o.returnInfo ? o.returnInfo.refundAmount : o.totalAmount), 0);
      const net = gross - cancSpend - refAmt;
      const validOrders = filteredOrders.filter(o => o.status !== 'Cancelled');
      const aov = validOrders.length ? (gross - cancSpend) / validOrders.length : 0;
      const discounts = filteredOrders.reduce((s, o) => s + o.discount, 0);
      const shipping = filteredOrders.reduce((s, o) => s + o.shippingCharge, 0);

      document.getElementById('lblFilteredCount').textContent = filteredOrders.length;
      document.getElementById('lblFilteredSpend').textContent = fmt(gross);

      document.getElementById('kpiGross').textContent = fmt(gross);
      document.getElementById('kpiGrossSub').textContent = filteredOrders.length + ' orders';

      document.getElementById('kpiNet').textContent = fmt(net);
      document.getElementById('kpiNetSub').textContent = validOrders.length + ' delivered/in-flight';

      document.getElementById('kpiOrders').textContent = filteredOrders.length;
      document.getElementById('kpiOrdersSub').textContent = cancelled.length + ' cancelled';

      document.getElementById('kpiAOV').textContent = fmt(aov);
      document.getElementById('kpiAOVSub').textContent = 'Per realized order';

      document.getElementById('kpiDiscounts').textContent = fmt(discounts);
      document.getElementById('kpiDiscountsSub').textContent = discounts > 0 ? (((discounts / (gross + discounts)) * 100).toFixed(1) + '% rate') : 'None recorded';

      document.getElementById('kpiRefunds').textContent = fmt(refAmt);
      document.getElementById('kpiRefundsSub').textContent = refunded.length + ' returns';

      document.getElementById('kpiShipping').textContent = fmt(shipping);
      document.getElementById('kpiShippingSub').textContent = filteredOrders.filter(o => o.shippingCharge > 0).length + ' paid shipments';
    }}

    let currentTab = 'overview';
    function switchTab(tabId) {{
      currentTab = tabId;
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
      const activePane = document.getElementById('tab-' + tabId);
      if (activePane) activePane.classList.remove('hidden');

      document.querySelectorAll('.tab-btn').forEach(btn => {{
        const isActive = btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(tabId);
        btn.classList.toggle('active', isActive);
      }});

      requestAnimationFrame(() => {{
        renderActiveTab();
        Object.values(activeCharts).forEach(ch => {{
          if (ch && typeof ch.resize === 'function') ch.resize();
        }});
      }});
    }}

    function renderActiveTab() {{
      if (currentTab === 'overview') renderOverviewTab();
      else if (currentTab === 'trends') renderTrendsTab();
      else if (currentTab === 'categories') renderCategoriesTab();
      else if (currentTab === 'logistics') renderLogisticsTab();
      else if (currentTab === 'returns') renderReturnsTab();
      else if (currentTab === 'digital') renderDigitalTab();
      else if (currentTab === 'orders') renderOrdersTable();
      else if (currentTab === 'insights') renderInsightsTab();
    }}

    // TAB 1: OVERVIEW
    function renderOverviewTab() {{
      // Yearly Waterfall Bar Chart
      const yrMap = {{}};
      const yrNetMap = {{}};
      const yrOrdersMap = {{}};
      filteredOrders.forEach(o => {{
        const y = o.orderDate ? o.orderDate.slice(0, 4) : '';
        if (!y) return;
        yrMap[y] = (yrMap[y] || 0) + o.totalAmount;
        yrOrdersMap[y] = (yrOrdersMap[y] || 0) + 1;
        if (o.status !== 'Cancelled') {{
          const ref = (o.status === 'Returned & Refunded' && o.returnInfo) ? o.returnInfo.refundAmount : 0;
          yrNetMap[y] = (yrNetMap[y] || 0) + (o.totalAmount - ref);
        }}
      }});
      const years = Object.keys(yrMap).sort();

      renderOrUpdateChart('chartYearly', {{
        type: 'bar',
        data: {{
          labels: years,
          datasets: [
            {{
              label: 'Gross Spend',
              data: years.map(y => Math.round(yrMap[y] || 0)),
              backgroundColor: '#f59e0b',
              borderRadius: 6,
              yAxisID: 'y',
            }},
            {{
              label: 'Net Spend',
              data: years.map(y => Math.round(yrNetMap[y] || 0)),
              backgroundColor: '#10b981',
              borderRadius: 6,
              yAxisID: 'y',
            }},
            {{
              type: 'line',
              label: 'Orders Count',
              data: years.map(y => yrOrdersMap[y] || 0),
              borderColor: '#3b82f6',
              backgroundColor: '#3b82f6',
              pointRadius: 4,
              borderWidth: 2,
              tension: 0.2,
              yAxisID: 'y1',
            }}
          ]
        }},
        options: {{
          interaction: {{ mode: 'index', intersect: false }},
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedYear = chart.data.labels[elements[0].index];
            filterAndJumpToOrders({{ year: clickedYear }}, `Filtered orders for Year: ${{clickedYear}}`);
          }},
          plugins: {{
            legend: {{ labels: {{ color: getTextColor(), font: {{ size: 11 }} }} }},
            tooltip: {{
              callbacks: {{
                label: ctx => {{
                  if (ctx.dataset.type === 'line') return `${{ctx.dataset.label}}: ${{ctx.parsed.y}} orders`;
                  return `${{ctx.dataset.label}}: ${{fmt(ctx.parsed.y)}}`;
                }},
                afterBody: () => ['(Click bar to view filtered orders)']
              }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{ display: false }},
              ticks: {{ color: getTextColor() }}
            }},
            y: {{
              type: 'linear',
              position: 'left',
              beginAtZero: true,
              grace: '10%',
              grid: {{ color: getGridColor() }},
              ticks: {{
                color: getTextColor(),
                callback: val => fmtK(val)
              }}
            }},
            y1: {{
              type: 'linear',
              position: 'right',
              beginAtZero: true,
              grace: '15%',
              grid: {{ display: false }},
              ticks: {{
                color: '#3b82f6',
                stepSize: 10,
                callback: val => Math.round(val)
              }}
            }}
          }}
        }}
      }});

      // Status Donut
      const stMap = {{}};
      filteredOrders.forEach(o => {{ stMap[o.status] = (stMap[o.status] || 0) + 1; }});
      const statuses = Object.keys(stMap);
      const stColors = {{
        'Delivered': '#10b981',
        'Returned & Refunded': '#8b5cf6',
        'Replaced / Exchanged': '#f59e0b',
        'Cancelled': '#ef4444',
        'In Transit / Arriving': '#3b82f6',
      }};

      renderOrUpdateChart('chartStatus', {{
        type: 'doughnut',
        data: {{
          labels: statuses,
          datasets: [{{
            data: statuses.map(s => stMap[s]),
            backgroundColor: statuses.map(s => stColors[s] || '#94a3b8'),
            borderWidth: 0,
            hoverOffset: 6
          }}]
        }},
        options: {{
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedStatus = chart.data.labels[elements[0].index];
            filterAndJumpToOrders({{ status: clickedStatus }}, `Filtered orders by Status: ${{clickedStatus}}`);
          }},
          plugins: {{
            legend: {{
              position: 'right',
              labels: {{ color: getTextColor(), font: {{ size: 11 }}, boxWidth: 12, padding: 14 }}
            }},
            tooltip: {{
              callbacks: {{
                label: ctx => {{
                  const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                  const pct = ((ctx.parsed / total) * 100).toFixed(1);
                  return `${{ctx.label}}: ${{ctx.parsed}} orders (${{pct}}%)`;
                }},
                afterBody: () => ['(Click slice to filter orders)']
              }}
            }}
          }}
        }}
      }});

      // Category Share Donut
      const catMap = {{}};
      filteredOrders.forEach(o => {{ catMap[o.category] = (catMap[o.category] || 0) + o.totalAmount; }});
      const topCats = Object.keys(catMap).sort((a, b) => catMap[b] - catMap[a]).slice(0, 7);

      renderOrUpdateChart('chartCategoryShare', {{
        type: 'doughnut',
        data: {{
          labels: topCats,
          datasets: [{{
            data: topCats.map(c => Math.round(catMap[c])),
            backgroundColor: topCats.map(c => CAT_COLORS[c] || '#94a3b8'),
            borderWidth: 0,
            hoverOffset: 6
          }}]
        }},
        options: {{
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedCat = chart.data.labels[elements[0].index];
            filterAndJumpToOrders({{ category: clickedCat }}, `Filtered orders for: ${{clickedCat}}`);
          }},
          plugins: {{
            legend: {{
              position: 'right',
              labels: {{ color: getTextColor(), font: {{ size: 11 }}, boxWidth: 12, padding: 12 }}
            }},
            tooltip: {{
              callbacks: {{
                label: ctx => {{
                  const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                  const pct = ((ctx.parsed / total) * 100).toFixed(1);
                  return `${{ctx.label}}: ${{fmt(ctx.parsed)}} (${{pct}}%)`;
                }},
                afterBody: () => ['(Click slice to filter orders)']
              }}
            }}
          }}
        }}
      }});

      // Order Type Donut
      const typeMap = {{}};
      filteredOrders.forEach(o => {{ typeMap[o.orderType] = (typeMap[o.orderType] || 0) + o.totalAmount; }});
      const types = Object.keys(typeMap);

      renderOrUpdateChart('chartOrderType', {{
        type: 'doughnut',
        data: {{
          labels: types,
          datasets: [{{
            data: types.map(t => Math.round(typeMap[t])),
            backgroundColor: ['#3b82f6', '#f59e0b', '#8b5cf6', '#10b981'],
            borderWidth: 0,
            hoverOffset: 6
          }}]
        }},
        options: {{
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedType = chart.data.labels[elements[0].index];
            filterAndJumpToOrders({{ type: clickedType }}, `Filtered orders by Type: ${{clickedType}}`);
          }},
          plugins: {{
            legend: {{
              position: 'right',
              labels: {{ color: getTextColor(), font: {{ size: 11 }}, boxWidth: 12, padding: 14 }}
            }},
            tooltip: {{
              callbacks: {{
                label: ctx => {{
                  const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                  const pct = ((ctx.parsed / total) * 100).toFixed(1);
                  return `${{ctx.label}}: ${{fmt(ctx.parsed)}} (${{pct}}%)`;
                }},
                afterBody: () => ['(Click slice to filter orders)']
              }}
            }}
          }}
        }}
      }});
    }}

    // TAB 2: FINANCIAL TRENDS
    function renderTrendsTab() {{
      const gran = document.getElementById('tTrendGranularity').value;
      const pMap = {{}};
      const pOrders = {{}};
      filteredOrders.forEach(o => {{
        if (!o.orderDate) return;
        let key = o.orderDate.slice(0, 7);
        if (gran === 'year') key = o.orderDate.slice(0, 4);
        else if (gran === 'quarter') {{
          const m = parseInt(o.orderDate.slice(5, 7));
          key = o.orderDate.slice(0, 4) + ' Q' + Math.ceil(m / 3);
        }}
        pMap[key] = (pMap[key] || 0) + o.totalAmount;
        pOrders[key] = (pOrders[key] || 0) + 1;
      }});
      const periods = Object.keys(pMap).sort();

      renderOrUpdateChart('chartTimeSeries', {{
        type: 'line',
        data: {{
          labels: periods,
          datasets: [{{
            label: 'Total Spend',
            data: periods.map(p => Math.round(pMap[p])),
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.12)',
            fill: true,
            tension: 0.25,
            pointRadius: periods.length > 30 ? 2 : 4,
            pointHoverRadius: 6,
            borderWidth: 2,
          }}]
        }},
        options: {{
          interaction: {{ mode: 'index', intersect: false }},
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedPeriod = chart.data.labels[elements[0].index];
            if (gran === 'year') {{
              filterAndJumpToOrders({{ year: clickedPeriod }}, `Filtered orders for Year: ${{clickedPeriod}}`);
            }} else if (gran === 'month') {{
              filterAndJumpToOrders({{ dateMonth: clickedPeriod }}, `Filtered orders for Month: ${{clickedPeriod}}`);
            }}
          }},
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: ctx => `Spend: ${{fmt(ctx.parsed.y)}} (${{pOrders[ctx.label] || 0}} orders)`,
                afterBody: () => ['(Click point to view orders)']
              }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{ display: false }},
              ticks: {{
                color: getTextColor(),
                maxTicksLimit: 14,
                font: {{ size: 10 }}
              }}
            }},
            y: {{
              beginAtZero: true,
              grace: '10%',
              grid: {{ color: getGridColor() }},
              ticks: {{
                color: getTextColor(),
                callback: val => fmtK(val)
              }}
            }}
          }}
        }}
      }});

      // Day of Week
      const dowCounts = [0, 0, 0, 0, 0, 0, 0];
      const dowSpends = [0, 0, 0, 0, 0, 0, 0];
      filteredOrders.forEach(o => {{
        if (o.orderDate) {{
          const d = new Date(o.orderDate);
          const dow = (d.getDay() + 6) % 7;
          dowCounts[dow]++;
          dowSpends[dow] += o.totalAmount;
        }}
      }});
      const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

      renderOrUpdateChart('chartDayOfWeek', {{
        type: 'bar',
        data: {{
          labels: days.map(d => d.slice(0, 3)),
          datasets: [{{
            label: 'Orders',
            data: dowCounts,
            backgroundColor: '#3b82f6',
            borderRadius: 6
          }}]
        }},
        options: {{
          onClick: (event, elements) => {{
            if (!elements || !elements.length) return;
            const idx = elements[0].index;
            filterAndJumpToOrders({{ weekday: idx }}, `Filtered orders placed on ${{days[idx]}}s`);
          }},
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: ctx => `${{ctx.parsed.y}} orders (${{fmt(dowSpends[ctx.dataIndex])}})`,
                afterBody: () => ['(Click to filter by this day)']
              }}
            }}
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: getTextColor() }} }},
            y: {{
              beginAtZero: true,
              grace: '12%',
              grid: {{ color: getGridColor() }},
              ticks: {{ color: getTextColor(), stepSize: 10 }}
            }}
          }}
        }}
      }});

      // Hour of Day
      const hodCounts = Array(24).fill(0);
      filteredOrders.forEach(o => {{
        if (o.orderDate && o.orderDate.length >= 13) {{
          const hr = parseInt(o.orderDate.slice(11, 13));
          if (!isNaN(hr)) hodCounts[hr]++;
        }}
      }});
      const hours = Array.from({{ length: 24 }}, (_, i) => `${{String(i).padStart(2, '0')}}h`);

      renderOrUpdateChart('chartHourOfDay', {{
        type: 'bar',
        data: {{
          labels: hours,
          datasets: [{{
            label: 'Orders',
            data: hodCounts,
            backgroundColor: '#10b981',
            borderRadius: 4
          }}]
        }},
        options: {{
          onClick: (event, elements) => {{
            if (!elements || !elements.length) return;
            const hr = elements[0].index;
            filterAndJumpToOrders({{ hour: hr }}, `Filtered orders placed around ${{hr}}:00 IST`);
          }},
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: ctx => `${{ctx.parsed.y}} orders placed around ${{ctx.label}}`,
                afterBody: () => ['(Click to filter by this hour)']
              }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{ display: false }},
              ticks: {{ color: getTextColor(), maxTicksLimit: 12, font: {{ size: 10 }} }}
            }},
            y: {{
              beginAtZero: true,
              grace: '15%',
              grid: {{ color: getGridColor() }},
              ticks: {{ color: getTextColor(), stepSize: 5 }}
            }}
          }}
        }}
      }});
    }}

    // TAB 3: CATEGORIES
    function renderCategoriesTab() {{
      const cm = {{}};
      filteredOrders.forEach(o => {{
        if (!cm[o.category]) cm[o.category] = {{ spend: 0, count: 0, items: 0, cancelled: 0, returned: 0 }};
        cm[o.category].spend += o.totalAmount;
        cm[o.category].count += 1;
        cm[o.category].items += o.itemCount;
        if (o.status === 'Cancelled') cm[o.category].cancelled++;
        if (o.status.includes('Returned') || o.status.includes('Replaced')) cm[o.category].returned++;
      }});
      const catsSorted = Object.keys(cm).sort((a, b) => cm[b].spend - cm[a].spend);
      const totalSpend = Object.values(cm).reduce((s, v) => s + v.spend, 0);

      renderOrUpdateChart('chartCategoryBars', {{
        type: 'bar',
        data: {{
          labels: catsSorted,
          datasets: [{{
            label: 'Spend',
            data: catsSorted.map(c => Math.round(cm[c].spend)),
            backgroundColor: catsSorted.map(c => CAT_COLORS[c] || '#94a3b8'),
            borderRadius: 4
          }}]
        }},
        options: {{
          indexAxis: 'y',
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedCat = chart.data.labels[elements[0].index];
            filterAndJumpToOrders({{ category: clickedCat }}, `Filtered orders for: ${{clickedCat}}`);
          }},
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: ctx => `${{fmt(ctx.parsed.x)}} (${{cm[ctx.label].count}} orders)`,
                afterBody: () => ['(Click bar to view filtered orders)']
              }}
            }}
          }},
          scales: {{
            x: {{
              beginAtZero: true,
              grace: '10%',
              grid: {{ color: getGridColor() }},
              ticks: {{ color: getTextColor(), callback: val => fmtK(val) }}
            }},
            y: {{
              grid: {{ display: false }},
              ticks: {{ color: getTextColor(), font: {{ size: 11 }} }}
            }}
          }}
        }}
      }});

      // Category Table
      const tb = document.getElementById('tblCategoryMetrics');
      tb.innerHTML = '';
      catsSorted.forEach(cat => {{
        const d = cm[cat];
        const aov = d.count ? d.spend / d.count : 0;
        const pct = totalSpend ? ((d.spend / totalSpend) * 100).toFixed(1) : 0;
        const co = CAT_COLORS[cat] || '#94a3b8';

        const tr = document.createElement('tr');
        tr.className = 'cursor-pointer';
        tr.onclick = () => {{
          filterAndJumpToOrders({{ category: cat }}, `Filtered orders for: ${{cat}}`);
        }};
        tr.innerHTML = `
          <td style="padding-left:14px">
            <span class="inline-flex items-center gap-2">
              <span style="width:10px;height:10px;border-radius:2px;background:${{co}}"></span>
              <strong>${{cat}}</strong>
            </span>
          </td>
          <td>${{d.count}}</td>
          <td>${{d.items}}</td>
          <td><strong>${{fmt(d.spend)}}</strong></td>
          <td>${{fmt(aov)}}</td>
          <td>
            <div class="flex items-center gap-2">
              <div style="height:6px;border-radius:3px;background:${{co}};width:${{Math.round(+pct * 1.5)}}px;min-width:2px"></div>
              <span>${{pct}}%</span>
            </div>
          </td>
          <td>${{d.returned > 0 ? `<span class="badge b-purple">${{d.returned}}</span>` : '0'}}</td>
          <td>${{d.cancelled > 0 ? `<span class="badge b-red">${{d.cancelled}}</span>` : '0'}}</td>
        `;
        tb.appendChild(tr);
      }});

      // Top Splurges
      const splurges = [...filteredOrders].sort((a, b) => b.totalAmount - a.totalAmount).slice(0, 15);
      const divSplurges = document.getElementById('lstTopSplurges');
      divSplurges.innerHTML = splurges.map((o, i) => {{
        const title = (o.items[0] && o.items[0].title) || o.orderId;
        const short = title.length > 60 ? title.slice(0, 59) + '...' : title;
        const link = o.detailsUrl ? `<a href="${{o.detailsUrl}}" target="_blank" class="hover:underline text-[var(--foreground)]">${{short}}</a>` : short;
        const co = CAT_COLORS[o.category] || '#94a3b8';
        return `
          <div class="flex items-start gap-3 py-2 border-b border-[var(--border)] text-xs">
            <span class="font-bold text-[var(--muted-foreground)] min-w-[24px]">#${{i + 1}}</span>
            <div class="flex-1">
              <p class="font-medium">${{link}}</p>
              <div class="flex items-center gap-2 mt-1 text-[11px]">
                <span style="color:${{co}}" class="font-semibold cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ category: '${{o.category}}' }}, 'Filtered: ${{o.category}}')">${{o.category}}</span>
                <span class="text-[var(--muted-foreground)]">&bull;</span>
                <span class="text-[var(--muted-foreground)]">${{o.orderDate ? o.orderDate.slice(0, 10) : ''}}</span>
              </div>
            </div>
            <span class="font-bold whitespace-nowrap text-[var(--primary)]">${{fmt(o.totalAmount)}}</span>
          </div>
        `;
      }}).join('');

      // Repeat Purchases (Realized deliveries with cancellation & refund badges)
      const repeatItems = MASTER_ANALYTICS.repeat_purchases || [];
      const divRepeat = document.getElementById('lstRepeatPurchases');
      if (divRepeat) {{
        if (repeatItems.length === 0) {{
          divRepeat.innerHTML = '<p class="text-xs text-[var(--muted-foreground)] py-4 text-center">No repurchased items found.</p>';
        }} else {{
          divRepeat.innerHTML = repeatItems.slice(0, 10).map(rp => {{
            const shortTitle = rp.title.length > 55 ? rp.title.slice(0, 54) + '...' : rp.title;
            const searchKeyword = rp.title.slice(0, 28).replace(/'/g, "\\'").replace(/"/g, '');
            return `
              <div class="flex items-center justify-between py-2 border-b border-[var(--border)] text-xs hover:bg-[var(--accent)] px-1.5 rounded cursor-pointer transition-colors" onclick="filterAndJumpToOrders({{ item: '${{searchKeyword}}' }}, 'Viewing orders for: ${{shortTitle.replace(/'/g, "\\'")}}')">
                <div class="flex-1 pr-3">
                  <p class="font-medium text-[var(--foreground)]">${{shortTitle}}</p>
                  <p class="text-[11px] text-[var(--muted-foreground)] mt-0.5 flex items-center gap-1.5 flex-wrap">
                    <span class="text-[#10b981] font-semibold">&#x2714; Delivered ${{rp.count}} time${{rp.count > 1 ? 's' : ''}}</span>
                    ${{rp.refundedCount > 0 ? `<span class="badge b-purple">&#x21BA; ${{rp.refundedCount}} returned & refunded</span>` : ''}}
                    ${{rp.replacedCount > 0 ? `<span class="badge b-yellow">&#x26A1; ${{rp.replacedCount}} replaced</span>` : ''}}
                    ${{rp.cancelledCount > 0 ? `<span class="badge b-red">&#x2716; ${{rp.cancelledCount}} cancelled</span>` : ''}}
                  </p>
                </div>
                <div class="text-right">
                  <span class="font-bold whitespace-nowrap text-[var(--primary)] block">${{fmt(rp.totalSpend)}}</span>
                  <span class="text-[10px] text-[var(--muted-foreground)]">${{rp.refundAmount > 0 ? `net (${{fmt(rp.refundAmount)}} refunded)` : 'net realized'}}</span>
                </div>
              </div>
            `;
          }}).join('');
        }}
      }}

      // Price Brackets
      const brackets = [
        {{ label: '<₹200', max: 200 }},
        {{ label: '₹200-500', max: 500 }},
        {{ label: '₹500-1K', max: 1000 }},
        {{ label: '₹1K-2.5K', max: 2500 }},
        {{ label: '₹2.5K-5K', max: 5000 }},
        {{ label: '₹5K-10K', max: 10000 }},
        {{ label: '>₹10K', max: Infinity }},
      ];
      const bCounts = Array(brackets.length).fill(0);
      filteredOrders.forEach(o => {{
        for (let i = 0; i < brackets.length; i++) {{
          if (o.totalAmount < brackets[i].max) {{
            bCounts[i]++;
            break;
          }}
        }}
      }});

      renderOrUpdateChart('chartPriceBrackets', {{
        type: 'bar',
        data: {{
          labels: brackets.map(b => b.label),
          datasets: [{{
            label: 'Orders',
            data: bCounts,
            backgroundColor: '#8b5cf6',
            borderRadius: 6
          }}]
        }},
        options: {{
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedTier = chart.data.labels[elements[0].index];
            filterAndJumpToOrders({{ priceTier: clickedTier }}, `Filtered orders in price tier: ${{clickedTier}}`);
          }},
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: ctx => `${{ctx.parsed.y}} orders in this price tier`,
                afterBody: () => ['(Click bar to view filtered orders)']
              }}
            }}
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: getTextColor() }} }},
            y: {{
              beginAtZero: true,
              grace: '10%',
              grid: {{ color: getGridColor() }},
              ticks: {{ color: getTextColor(), stepSize: 20 }}
            }}
          }}
        }}
      }});
    }}

    // TAB 4: LOGISTICS & GEOGRAPHY
    function renderLogisticsTab() {{
      const carMap = {{}};
      filteredOrders.forEach(o => {{
        if (o.orderType === 'Physical Retail') {{
          carMap[o.carrier] = (carMap[o.carrier] || 0) + 1;
        }}
      }});
      const carriers = Object.keys(carMap).sort((a, b) => carMap[b] - carMap[a]);

      renderOrUpdateChart('chartCarriers', {{
        type: 'doughnut',
        data: {{
          labels: carriers.slice(0, 5),
          datasets: [{{
            data: carriers.slice(0, 5).map(c => carMap[c]),
            backgroundColor: COLORS,
            borderWidth: 0,
            hoverOffset: 6
          }}]
        }},
        options: {{
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedCarrier = chart.data.labels[elements[0].index];
            filterAndJumpToOrders({{ carrier: clickedCarrier }}, `Filtered physical orders by Carrier: ${{clickedCarrier}}`);
          }},
          plugins: {{
            legend: {{
              position: 'right',
              labels: {{ color: getTextColor(), font: {{ size: 11 }}, boxWidth: 12, padding: 14 }}
            }},
            tooltip: {{
              callbacks: {{
                label: ctx => `${{ctx.label}}: ${{ctx.parsed}} shipments`,
                afterBody: () => ['(Click slice to filter orders)']
              }}
            }}
          }}
        }}
      }});

      // Carrier Table
      const tb = document.getElementById('tblCarriers');
      const totalCar = Object.values(carMap).reduce((a, b) => a + b, 0);
      tb.innerHTML = carriers.map(c => {{
        const cnt = carMap[c];
        const pct = totalCar ? ((cnt / totalCar) * 100).toFixed(1) : 0;
        return `
          <tr class="cursor-pointer" onclick="filterAndJumpToOrders({{ carrier: '${{c}}' }}, 'Filtered: ${{c}}')">
            <td style="padding-left:14px"><strong>${{c}}</strong></td>
            <td>${{cnt}} shipments</td>
            <td>${{pct}}%</td>
          </tr>
        `;
      }}).join('');

      // City Timeline
      const cityData = MASTER_ANALYTICS.geography || [];
      const divCity = document.getElementById('lstCityTimeline');
      divCity.innerHTML = cityData.map(cd => `
        <div class="py-2.5 border-b border-[var(--border)] text-xs cursor-pointer hover:bg-[var(--accent)] px-2 rounded" onclick="filterAndJumpToOrders({{ city: '${{cd.city}}' }}, 'Filtered City: ${{cd.city}}')">
          <div class="flex justify-between items-center mb-1">
            <strong class="text-sm">${{cd.city}}</strong>
            <span class="font-bold text-[var(--primary)]">${{fmt(cd.spend)}}</span>
          </div>
          <p class="text-[var(--muted-foreground)]">${{cd.orderCount}} orders &bull; ${{cd.firstOrder}} to ${{cd.lastOrder}}</p>
        </div>
      `).join('');
    }}

    // TAB 5: RETURNS & REFUNDS (WITH COLUMN FILTERS & CHART CLICKS)
    function renderReturnsTab() {{
      const retAnalytics = MASTER_ANALYTICS.returns || {{}};
      const reasons = retAnalytics.reasons || [];
      const resols = retAnalytics.resolutions || [];

      renderOrUpdateChart('chartReturnReasons', {{
        type: 'doughnut',
        data: {{
          labels: reasons.slice(0, 5).map(r => r.reason),
          datasets: [{{
            data: reasons.slice(0, 5).map(r => r.count),
            backgroundColor: COLORS,
            borderWidth: 0,
            hoverOffset: 6
          }}]
        }},
        options: {{
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedReason = chart.data.labels[elements[0].index];
            returnsFilters.reason = clickedReason;
            const el = document.getElementById('retColReason');
            if (el) el.value = clickedReason;
            applyReturnsFilters();
            document.getElementById('tblReturnsLedgerCard').scrollIntoView({{ behavior: 'smooth' }});
            showFilterToast(`Returns filtered by Reason: ${{clickedReason}}`);
          }},
          plugins: {{
            legend: {{
              position: 'bottom',
              labels: {{ color: getTextColor(), font: {{ size: 10 }}, boxWidth: 10, padding: 8 }}
            }},
            tooltip: {{
              callbacks: {{
                afterBody: () => ['(Click slice to filter table)']
              }}
            }}
          }}
        }}
      }});

      renderOrUpdateChart('chartReturnResolutions', {{
        type: 'doughnut',
        data: {{
          labels: resols.map(r => r.resolution),
          datasets: [{{
            data: resols.map(r => r.count),
            backgroundColor: ['#8b5cf6', '#f59e0b'],
            borderWidth: 0,
            hoverOffset: 6
          }}]
        }},
        options: {{
          onClick: (event, elements, chart) => {{
            if (!elements || !elements.length) return;
            const clickedResol = chart.data.labels[elements[0].index];
            returnsFilters.resolution = clickedResol;
            const el = document.getElementById('retColResolution');
            if (el) el.value = clickedResol;
            applyReturnsFilters();
            document.getElementById('tblReturnsLedgerCard').scrollIntoView({{ behavior: 'smooth' }});
            showFilterToast(`Returns filtered by Resolution: ${{clickedResol}}`);
          }},
          plugins: {{
            legend: {{
              position: 'bottom',
              labels: {{ color: getTextColor(), font: {{ size: 11 }}, boxWidth: 12 }}
            }},
            tooltip: {{
              callbacks: {{
                afterBody: () => ['(Click slice to filter table)']
              }}
            }}
          }}
        }}
      }});

      // Replacement Links
      const repLinks = retAnalytics.replacementLinks || [];
      const divRep = document.getElementById('lstReplacementLinks');
      divRep.innerHTML = repLinks.map(rl => `
        <div class="p-2.5 mb-2 rounded bg-[var(--accent)] border border-[var(--border)]">
          <p class="font-semibold">${{rl.itemTitle.slice(0, 45)}}...</p>
          <p class="text-[var(--muted-foreground)] mt-1">
            Orig: <span class="font-mono text-[var(--foreground)] hover:underline cursor-pointer" onclick="filterAndJumpToOrders({{ ordId: '${{rl.originalOrderId}}' }}, 'Orig: ${{rl.originalOrderId}}')">${{rl.originalOrderId}}</span> 
            &rarr; 
            <span class="text-[var(--primary)] font-mono hover:underline cursor-pointer" onclick="filterAndJumpToOrders({{ ordId: '${{rl.replacementOrderId}}' }}, 'Repl: ${{rl.replacementOrderId}}')">Repl: ${{rl.replacementOrderId}}</span>
          </p>
          <p class="text-[11px] text-[var(--info)] mt-0.5">Reason: ${{rl.reason}}</p>
        </div>
      `).join('');

      renderReturnsTable();
    }}

    function applyReturnsFilters() {{
      returnsFilters.date = (document.getElementById('retColDate').value || '').trim().toLowerCase();
      returnsFilters.orderId = (document.getElementById('retColOrderId').value || '').trim().toLowerCase();
      returnsFilters.product = (document.getElementById('retColProduct').value || '').trim().toLowerCase();
      returnsFilters.category = document.getElementById('retColCategory').value;
      returnsFilters.reason = document.getElementById('retColReason').value;
      returnsFilters.resolution = document.getElementById('retColResolution').value;
      returnsFilters.amount = document.getElementById('retColAmount').value;

      renderReturnsTable();
    }}

    function resetReturnsFilters() {{
      returnsFilters.date = '';
      returnsFilters.orderId = '';
      returnsFilters.product = '';
      returnsFilters.category = '';
      returnsFilters.reason = '';
      returnsFilters.resolution = '';
      returnsFilters.amount = '';

      const setVal = (id, val) => {{ const el = document.getElementById(id); if (el) el.value = val; }};
      setVal('retColDate', '');
      setVal('retColOrderId', '');
      setVal('retColProduct', '');
      setVal('retColCategory', '');
      setVal('retColReason', '');
      setVal('retColResolution', '');
      setVal('retColAmount', '');

      renderReturnsTable();
      showFilterToast('Returns filters cleared');
    }}

    function sortReturnsBy(col) {{
      if (returnsSortCol === col) {{
        returnsSortDir = (returnsSortDir === 'asc') ? 'desc' : 'asc';
      }} else {{
        returnsSortCol = col;
        returnsSortDir = (col === 'refundAmount') ? 'desc' : 'asc';
      }}
      renderReturnsTable();
    }}

    function renderReturnsTable() {{
      const retRecords = (MASTER_ANALYTICS.returns && MASTER_ANALYTICS.returns.returnRecords) || [];

      // Filter
      const filtered = retRecords.filter(r => {{
        if (returnsFilters.date && !r.date.toLowerCase().includes(returnsFilters.date)) return false;
        if (returnsFilters.orderId && !r.orderId.toLowerCase().includes(returnsFilters.orderId)) return false;
        if (returnsFilters.product && !r.itemTitle.toLowerCase().includes(returnsFilters.product)) return false;
        if (returnsFilters.category && r.category !== returnsFilters.category) return false;
        if (returnsFilters.reason && r.reason !== returnsFilters.reason) return false;
        if (returnsFilters.resolution && r.resolution !== returnsFilters.resolution) return false;
        if (returnsFilters.amount === 'refund' && (!r.refundAmount || r.refundAmount <= 0)) return false;
        if (returnsFilters.amount === 'exchange' && r.resolution !== 'Exchange') return false;
        return true;
      }});

      // Sort
      filtered.sort((a, b) => {{
        let cmp = 0;
        if (returnsSortCol === 'date') cmp = a.date.localeCompare(b.date);
        else if (returnsSortCol === 'orderId') cmp = a.orderId.localeCompare(b.orderId);
        else if (returnsSortCol === 'itemTitle') cmp = a.itemTitle.localeCompare(b.itemTitle);
        else if (returnsSortCol === 'category') cmp = a.category.localeCompare(b.category);
        else if (returnsSortCol === 'reason') cmp = a.reason.localeCompare(b.reason);
        else if (returnsSortCol === 'resolution') cmp = a.resolution.localeCompare(b.resolution);
        else if (returnsSortCol === 'refundAmount') cmp = a.refundAmount - b.refundAmount;
        return returnsSortDir === 'asc' ? cmp : -cmp;
      }});

      // Update sort icons
      ['date', 'orderId', 'itemTitle', 'category', 'reason', 'resolution', 'refundAmount'].forEach(c => {{
        const icon = document.getElementById('sortRetIcon_' + c);
        if (icon) {{
          if (returnsSortCol === c) icon.innerHTML = returnsSortDir === 'asc' ? '&#x25B2;' : '&#x25BC;';
          else icon.innerHTML = '&#x21C5;';
        }}
      }});

      // Update chips & count
      const sumRefund = filtered.reduce((s, r) => s + (r.refundAmount || 0), 0);
      document.getElementById('lblReturnsCount').textContent = filtered.length;
      document.getElementById('lblReturnsSum').textContent = fmt(sumRefund);

      const chipsBar = document.getElementById('returnsActiveChips');
      const chipsCont = document.getElementById('returnsChipsContainer');
      const activeChips = [];
      if (returnsFilters.date) activeChips.push(`Date: "${{returnsFilters.date}}"`);
      if (returnsFilters.orderId) activeChips.push(`ID: "${{returnsFilters.orderId}}"`);
      if (returnsFilters.product) activeChips.push(`Product: "${{returnsFilters.product}}"`);
      if (returnsFilters.category) activeChips.push(`Cat: ${{returnsFilters.category}}`);
      if (returnsFilters.reason) activeChips.push(`Reason: ${{returnsFilters.reason}}`);
      if (returnsFilters.resolution) activeChips.push(`Resol: ${{returnsFilters.resolution}}`);
      if (returnsFilters.amount) activeChips.push(`Amt: ${{returnsFilters.amount}}`);

      if (activeChips.length > 0) {{
        chipsBar.classList.remove('hidden');
        chipsCont.innerHTML = activeChips.map(c => `<span class="filter-chip"><span>${{c}}</span></span>`).join('');
      }} else {{
        chipsBar.classList.add('hidden');
        chipsCont.innerHTML = '';
      }}

      // Render Rows
      const tb = document.getElementById('tblReturnsLedger');
      tb.innerHTML = filtered.map(rr => `
        <tr>
          <td style="padding-left:14px; white-space:nowrap">${{rr.date}}</td>
          <td>
            <span class="font-mono text-[11px] text-[var(--primary)] hover:underline cursor-pointer" onclick="filterAndJumpToOrders({{ ordId: '${{rr.orderId}}' }}, 'Jumped to Order: ${{rr.orderId}}')">${{rr.orderId}}</span>
          </td>
          <td>${{rr.itemTitle.length > 50 ? rr.itemTitle.slice(0, 49) + '...' : rr.itemTitle}}</td>
          <td><span class="badge b-gray">${{rr.category}}</span></td>
          <td>${{rr.reason}}</td>
          <td><span class="badge ${{rr.resolution === 'Exchange' ? 'b-yellow' : 'b-purple'}}">${{rr.resolution}}</span></td>
          <td class="font-bold text-right" style="padding-right:14px">${{rr.refundAmount > 0 ? fmt(rr.refundAmount) : '<span class="text-[var(--muted-foreground)]">Exchange</span>'}}</td>
        </tr>
      `).join('');
    }}

    // TAB 6: DIGITAL & UTILITIES
    function renderDigitalTab() {{
      const utilityOrders = MASTER_ORDERS.filter(o => o.orderType === 'Utility & Recharge');
      const digitalOrders = MASTER_ORDERS.filter(o => o.orderType === 'Digital Subscription' || o.orderType === 'Digital Content');

      document.getElementById('lstUtilitySummary').innerHTML = `
        <strong>${{utilityOrders.length}}</strong> total utility transactions totaling 
        <strong class="text-[var(--primary)]">${{fmt(utilityOrders.reduce((s, o) => s + o.totalAmount, 0))}}</strong>
      `;
      document.getElementById('lstDigitalSummary').innerHTML = `
        <strong>${{digitalOrders.length}}</strong> digital orders & subscriptions totaling 
        <strong class="text-[var(--primary)]">${{fmt(digitalOrders.reduce((s, o) => s + o.totalAmount, 0))}}</strong>
      `;

      // Utility Table
      document.getElementById('tblUtilityLedger').innerHTML = utilityOrders.slice(0, 30).map(o => `
        <tr class="cursor-pointer" onclick="filterAndJumpToOrders({{ ordId: '${{o.orderId}}' }}, 'Order: ${{o.orderId}}')">
          <td style="padding-left:14px">${{o.orderDate ? o.orderDate.slice(0, 10) : ''}}</td>
          <td class="font-mono text-[11px] text-[var(--primary)]">${{o.orderId}}</td>
          <td>${{o.primaryTitle}}</td>
          <td class="font-bold text-right">${{fmt(o.totalAmount)}}</td>
        </tr>
      `).join('');

      // Digital Table
      document.getElementById('tblDigitalLedger').innerHTML = digitalOrders.slice(0, 30).map(o => `
        <tr class="cursor-pointer" onclick="filterAndJumpToOrders({{ ordId: '${{o.orderId}}' }}, 'Order: ${{o.orderId}}')">
          <td style="padding-left:14px">${{o.orderDate ? o.orderDate.slice(0, 10) : ''}}</td>
          <td>${{o.primaryTitle}}</td>
          <td><span class="badge b-purple">${{o.orderType}}</span></td>
          <td class="font-bold text-right">${{fmt(o.totalAmount)}}</td>
        </tr>
      `).join('');
    }}

    // TAB 7: MASTER ORDERS TABLE (WITH COLUMN FILTERS & SORTING)
    function sortOrdersBy(col) {{
      if (ordersSortCol === col) {{
        ordersSortDir = (ordersSortDir === 'asc') ? 'desc' : 'asc';
      }} else {{
        ordersSortCol = col;
        ordersSortDir = (col === 'amount' || col === 'discount') ? 'desc' : 'asc';
      }}
      renderOrdersTable();
    }}

    function renderOrdersTable() {{
      // Sort
      const sorted = [...filteredOrders].sort((a, b) => {{
        let cmp = 0;
        if (ordersSortCol === 'date') cmp = (a.orderDate || '').localeCompare(b.orderDate || '');
        else if (ordersSortCol === 'orderId') cmp = (a.orderId || '').localeCompare(b.orderId || '');
        else if (ordersSortCol === 'item') {{
          const tA = (a.items && a.items[0]) ? a.items[0].title : a.orderId;
          const tB = (b.items && b.items[0]) ? b.items[0].title : b.orderId;
          cmp = tA.localeCompare(tB);
        }}
        else if (ordersSortCol === 'category') cmp = (a.category || '').localeCompare(b.category || '');
        else if (ordersSortCol === 'amount') cmp = a.totalAmount - b.totalAmount;
        else if (ordersSortCol === 'status') cmp = (a.status || '').localeCompare(b.status || '');
        else if (ordersSortCol === 'city') cmp = (a.city || '').localeCompare(b.city || '');
        else if (ordersSortCol === 'discount') cmp = a.discount - b.discount;
        return ordersSortDir === 'asc' ? cmp : -cmp;
      }});

      // Update sort icons
      ['date', 'orderId', 'item', 'category', 'amount', 'status', 'city', 'discount'].forEach(c => {{
        const icon = document.getElementById('sortOrdIcon_' + c);
        if (icon) {{
          if (ordersSortCol === c) icon.innerHTML = ordersSortDir === 'asc' ? '&#x25B2;' : '&#x25BC;';
          else icon.innerHTML = '&#x21C5;';
        }}
      }});

      const totalPages = Math.ceil(sorted.length / PAGE_SIZE) || 1;
      if (currentPage > totalPages) currentPage = 1;
      const pageSlice = sorted.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

      document.getElementById('lblCurrentPage').textContent = currentPage;
      document.getElementById('lblTotalPages').textContent = totalPages;

      const badgeCls = s => {{
        if (s === 'Delivered') return 'b-green';
        if (s === 'Cancelled') return 'b-red';
        if (s.includes('Returned')) return 'b-purple';
        if (s.includes('Replaced')) return 'b-yellow';
        return 'b-blue';
      }};

      const tb = document.getElementById('tblOrdersMaster');
      tb.innerHTML = pageSlice.map((o, idx) => {{
        const title = (o.items && o.items[0]) ? o.items[0].title : o.orderId;
        const short = title.length > 55 ? title.slice(0, 54) + '...' : title;
        const link = o.detailsUrl ? `<a href="${{o.detailsUrl}}" target="_blank" class="hover:underline text-[var(--primary)] font-mono">${{o.orderId}}</a>` : `<span class="font-mono text-[var(--muted-foreground)]">${{o.orderId}}</span>`;
        const co = CAT_COLORS[o.category] || '#94a3b8';
        const drawerId = 'drawer-' + idx;

        const hasMultiple = (o.items && o.items.length > 1);
        const toggleBtn = hasMultiple ? `<button onclick="toggleDrawer('${{drawerId}}')" class="text-[10px] text-[var(--primary)] ml-1 hover:underline cursor-pointer">(+${{o.items.length - 1}} more)</button>` : '';

        return `
          <tr>
            <td style="padding-left:14px;white-space:nowrap">${{o.orderDate ? o.orderDate.slice(0, 10) : ''}}</td>
            <td>${{link}}</td>
            <td>
              <div>${{short}} ${{toggleBtn}}</div>
              ${{hasMultiple ? `
                <div id="${{drawerId}}" class="item-drawer">
                  ${{o.items.map(it => `<div class="text-[11px] text-[var(--muted-foreground)] py-0.5">&bull; ${{it.title}} (Qty: ${{it.quantity}}, ${{fmt(it.unitPrice)}})</div>`).join('')}}
                </div>
              ` : ''}}
            </td>
            <td><span style="color:${{co}}" class="font-medium">${{o.category}}</span></td>
            <td class="font-bold text-right">${{fmt(o.totalAmount)}}</td>
            <td><span class="badge ${{badgeCls(o.status)}}">${{o.status}}</span></td>
            <td class="text-[11px] text-[var(--muted-foreground)]">${{o.city}}</td>
            <td class="text-right text-[#10b981] font-medium" style="padding-right:14px">${{o.discount > 0 ? fmt(o.discount) : '—'}}</td>
          </tr>
        `;
      }}).join('');

      // Pagination Controls
      const divPag = document.getElementById('divPagination');
      divPag.innerHTML = '';
      if (totalPages > 1) {{
        const mkBtn = (lbl, pg, dis, act) => {{
          const b = document.createElement('button');
          b.innerHTML = lbl;
          b.className = `px-3 py-1 text-xs rounded border border-[var(--border)] ${{act ? 'bg-[var(--primary)] text-[var(--primary-foreground)] font-bold' : 'bg-[var(--card)] text-[var(--foreground)]'}} ${{dis ? 'opacity-40 cursor-not-allowed' : 'hover:bg-[var(--accent)] cursor-pointer'}}`;
          if (!dis) b.onclick = () => {{ currentPage = pg; renderOrdersTable(); }};
          return b;
        }};
        divPag.appendChild(mkBtn('&laquo;', currentPage - 1, currentPage === 1, false));
        const start = Math.max(1, currentPage - 2);
        const end = Math.min(totalPages, start + 4);
        for (let p = start; p <= end; p++) {{
          divPag.appendChild(mkBtn(p, p, false, p === currentPage));
        }}
        divPag.appendChild(mkBtn('&raquo;', currentPage + 1, currentPage === totalPages, false));
      }}
    }}

    // TAB 8: DYNAMIC STRATEGIC ANALYST INSIGHTS
    function renderInsightsTab() {{
      const topCat = (MASTER_ANALYTICS.categories && MASTER_ANALYTICS.categories[0]) || null;
      const topSplurges = MASTER_ANALYTICS.top_splurges || MASTER_ANALYTICS.topSplurges || [];
      const topSplurge = (topSplurges && topSplurges[0]) || null;
      const utilityOrders = MASTER_ORDERS.filter(o => o.orderType === 'Utility & Recharge');
      const utilSpend = utilityOrders.reduce((s, o) => s + o.totalAmount, 0);
      const logistics = MASTER_ANALYTICS.logistics || {{}};
      const primaryCarrier = logistics.primaryCarrier || 'Standard Carrier';
      const totalPhysical = logistics.totalPhysicalShipments || 0;
      const carrierTop = (logistics.carriers && logistics.carriers[0]) || null;
      const carrierShare = (carrierTop && totalPhysical > 0) ? ((carrierTop.count / totalPhysical) * 100).toFixed(0) : '0';

      const timePatterns = MASTER_ANALYTICS.time_patterns || MASTER_ANALYTICS.timePatterns || {{}};
      const maxStreak = timePatterns.longestDayStreak || 1;
      const activeDays = timePatterns.activeShoppingDays || 0;
      const peakDay = timePatterns.peakDay || 'Sunday';
      const peakHour = timePatterns.peakHour || '18:00';

      const geo = MASTER_ANALYTICS.geography || [];
      const topCities = geo.slice(0, 3);

      const returns = MASTER_ANALYTICS.returns || {{}};
      const totalReturns = returns.totalReturns || 0;
      const refundRecovered = returns.totalRefundAmount || 0;
      const replacementCount = (returns.replacementLinks || []).length;

      let monthly = MASTER_ANALYTICS.monthly || [];
      if (!monthly.length && MASTER_ORDERS.length) {{
        const mSpend = {{}};
        const mCount = {{}};
        MASTER_ORDERS.forEach(o => {{
          if (!o.orderDate) return;
          const ym = o.orderDate.slice(0, 7);
          mSpend[ym] = (mSpend[ym] || 0) + o.totalAmount;
          mCount[ym] = (mCount[ym] || 0) + 1;
        }});
        monthly = Object.keys(mSpend).map(ym => ({{
          yearMonth: ym,
          month: ym,
          spend: mSpend[ym],
          totalSpend: mSpend[ym],
          orderCount: mCount[ym]
        }}));
      }}

      const getSpend = m => (m ? (m.spend !== undefined ? m.spend : (m.totalSpend !== undefined ? m.totalSpend : 0)) : 0);
      const getMonthStr = m => (m ? (m.yearMonth || m.month || '') : '');
      const getOrderCount = m => (m ? (m.orderCount !== undefined ? m.orderCount : (m.ordersCount !== undefined ? m.ordersCount : (m.orders || 0))) : 0);

      const peakMonth = monthly.length ? [...monthly].sort((a, b) => getSpend(b) - getSpend(a))[0] : null;
      const peakSpend = peakMonth ? getSpend(peakMonth) : 0;
      const peakMonthStr = peakMonth ? getMonthStr(peakMonth) : '';
      const peakMonthLabel = formatYearMonth(peakMonthStr) || peakMonthStr || 'Unknown Month';
      const peakOrderCount = peakMonth ? getOrderCount(peakMonth) : 0;

      const topCatOrders = topCat ? MASTER_ORDERS.filter(o => o.category === topCat.category) : [];
      const sampleItems = [...new Set(topCatOrders.map(o => (o.items && o.items[0] && o.items[0].title) ? o.items[0].title.slice(0, 45) : '').filter(Boolean))].slice(0, 3);

      const divBehavior = document.getElementById('lstBehavioralInsights');
      if (divBehavior) {{
        const topCatName = topCat ? topCat.category : 'General Retail';
        const splurgeTitle = topSplurge ? (topSplurge.title ? (topSplurge.title.length > 65 ? topSplurge.title.slice(0, 65) + '...' : topSplurge.title) : 'High-Value Order') : '';

        divBehavior.innerHTML = `
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F4CA; Dominant Category: ${{topCatName}}</strong>
            ${{topCat ? `
              <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ category: this.dataset.cat }}, 'Filtered orders for Category: ' + this.dataset.cat)" data-cat="${{topCat.category}}" title="Click to filter orders for ${{topCat.category}}">${{topCat.category}}</strong> is the #1 expenditure category, capturing <span class="text-[var(--foreground)] font-semibold">${{fmt(topCat.spend)}} (${{topCat.spendSharePct}}%)</span> across ${{topCat.orderCount}} orders.${{sampleItems.length ? ` Key purchases include: ${{sampleItems.join(', ')}}...` : ''}}
            ` : 'No category data recorded.'}}
          </div>
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F3C5; Highest-Value Single Investment</strong>
            ${{topSplurge ? `
              Largest single order was <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ ordId: this.dataset.ord }}, 'Order: ' + this.dataset.ord)" data-ord="${{topSplurge.orderId}}" title="Click to filter order ${{topSplurge.orderId}}">${{splurgeTitle}}</strong> purchased for <span class="text-[var(--primary)] font-bold">${{fmt(topSplurge.amount)}}</span> on ${{topSplurge.date}} (${{topSplurge.category}}).
            ` : 'No purchase records available.'}}
          </div>
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F4B3; Amazon Pay & Utility Ecosystem</strong>
            ${{utilityOrders.length > 0 ? `
              <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ type: 'Utility & Recharge' }}, 'Filtered for Utility & Recharge orders')" title="Click to filter Utility & Recharge orders">${{utilityOrders.length}} utility transactions</strong> totaling <span class="text-[var(--foreground)] font-semibold">${{fmt(utilSpend)}}</span> were processed through Amazon for electricity, mobile recharges, or bill payments.
            ` : 'No utility orders recorded in this portfolio.'}}
          </div>
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F69A; Primary Courier Network</strong>
            ${{carrierTop && totalPhysical > 0 ? `
              <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ carrier: this.dataset.car }}, 'Filtered orders for Carrier: ' + this.dataset.car)" data-car="${{primaryCarrier}}" title="Click to filter carrier orders">${{primaryCarrier}}</strong> is your leading courier partner, handling <span class="text-[var(--foreground)] font-semibold">${{carrierShare}}%</span> of physical retail shipments (${{carrierTop.count}} shipments).
            ` : 'No physical retail shipments recorded.'}}
          </div>
        `;
      }}

      const divSeason = document.getElementById('lstSeasonalityInsights');
      if (divSeason) {{
        divSeason.innerHTML = `
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F4C6; Purchasing Streaks & Rhythms</strong>
            ${{activeDays > 0 ? `
              Your longest consecutive-day shopping streak was <strong class="text-[var(--foreground)]">${{maxStreak}} day(s)</strong>, while orders were placed across <strong class="text-[var(--foreground)]">${{activeDays}} unique days</strong>. Peak ordering occurred on <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ weekday: this.dataset.day }}, 'Filtered orders for Weekday: ' + this.dataset.day)" data-day="${{peakDay}}" title="Click to filter by weekday">${{peakDay}}s</strong> around <strong class="text-[var(--foreground)]">${{peakHour}} IST</strong>.
            ` : 'No chronological ordering rhythm data recorded.'}}
          </div>
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F6D2; Highest Spending Velocity</strong>
            ${{peakMonth && peakSpend > 0 ? `
              Highest single-month spend surged in <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ dateMonth: this.dataset.month }}, 'Filtered orders for Month: ' + this.dataset.label)" data-month="${{peakMonthStr}}" data-label="${{peakMonthLabel}}" title="Click to filter orders for ${{peakMonthLabel}}">${{peakMonthLabel}}</strong> with <span class="text-[var(--primary)] font-bold">${{fmt(peakSpend)}}</span> recorded across ${{peakOrderCount}} orders.
            ` : (peakMonth && peakOrderCount > 0 ? `
              Highest single-month activity occurred in <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ dateMonth: this.dataset.month }}, 'Filtered orders for Month: ' + this.dataset.label)" data-month="${{peakMonthStr}}" data-label="${{peakMonthLabel}}" title="Click to filter orders for ${{peakMonthLabel}}">${{peakMonthLabel}}</strong> with <span class="text-[var(--primary)] font-bold">${{peakOrderCount}} orders</span> recorded.
            ` : 'No longitudinal monthly trends available.')}}
          </div>
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F4CD; Geographic Delivery Profile</strong>
            ${{topCities.length > 0 ? `
              Deliveries spanned <strong>${{geo.length}} unique location(s)</strong>. Primary destination was <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ city: this.dataset.city }}, 'Filtered orders for City: ' + this.dataset.city)" data-city="${{topCities[0].city}}" title="Click to filter orders for ${{topCities[0].city}}">${{topCities[0].city}}</strong> (${{topCities[0].orderCount}} orders, ${{fmt(topCities[0].spend)}})${{topCities[0].firstOrder && topCities[0].lastOrder ? `, active from ${{topCities[0].firstOrder}} to ${{topCities[0].lastOrder}}` : ''}}${{topCities.length > 1 ? `, followed by <span class="cursor-pointer hover:underline" onclick="filterAndJumpToOrders({{ city: this.dataset.city }}, 'Filtered orders for City: ' + this.dataset.city)" data-city="${{topCities[1].city}}">${{topCities[1].city}}</span> (${{topCities[1].orderCount}} orders)` : ''}}.
            ` : 'No geographic delivery records available.'}}
          </div>
          <div class="p-3 rounded-lg bg-[var(--accent)] border border-[var(--border)]">
            <strong class="text-[var(--foreground)] block text-sm mb-1">&#x1F4B0; Returns & Recovery Efficiency</strong>
            ${{totalReturns > 0 ? `
              Across <strong class="text-[var(--foreground)] cursor-pointer hover:underline" onclick="switchTab('returns')" title="Click to view Returns & Exchanges">${{totalReturns}} initiated returns</strong>, you recovered <span class="text-[var(--foreground)] font-semibold">${{fmt(refundRecovered)}}</span> in cash refunds, with ${{replacementCount}} defective item(s) resolved via direct replacement shipments.
            ` : 'No return requests or defective item claims recorded in this portfolio (100% order retention).'}}
          </div>
        `;
      }}
    }}

    function toggleDrawer(drawerId) {{
      const el = document.getElementById(drawerId);
      if (el) {{
        el.style.display = (el.style.display === 'block') ? 'none' : 'block';
      }}
    }}

    function toggleTheme() {{
      const html = document.documentElement;
      const isL = html.classList.toggle('light');
      document.getElementById('themeIcon').textContent = isL ? '🌙' : '☀️';
      document.getElementById('themeLabel').textContent = isL ? 'Dark' : 'Light';
      renderActiveTab();
    }}

    function exportCSV() {{
      const headers = ['Order ID', 'Order Date', 'Order Type', 'Category', 'Subcategory', 'Total Amount', 'Status', 'City', 'Carrier', 'Tracking Number', 'Discount'];
      const rows = filteredOrders.map(o => [
        `"${{o.orderId}}"`,
        `"${{o.orderDate}}"`,
        `"${{o.orderType}}"`,
        `"${{o.category}}"`,
        `"${{o.subcategory}}"`,
        o.totalAmount,
        `"${{o.status}}"`,
        `"${{o.city}}"`,
        `"${{o.carrier}}"`,
        `"${{o.trackingNumber}}"`,
        o.discount
      ]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', 'amazon_orders_filtered.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}

    // Boot
    window.addEventListener('DOMContentLoaded', () => {{
      setTimeout(init, 50);
    }});
    window.addEventListener('resize', () => {{
      renderActiveTab();
    }});
  </script>
</body>
</html>"""
