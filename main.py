#!/usr/bin/env python3
"""Amazon Order Analysis & Insights Executive Suite.

CLI entrypoint for data discovery, analytics computation, dashboard generation,
and local dashboard hosting.
"""

import argparse
from datetime import datetime
import http.server
import json
import logging
from pathlib import Path
import socketserver
import sys
import webbrowser

from src.analyzer import OrderAnalyzer
from src.config import OUTPUT_DASHBOARD, OUTPUT_JSON, WORKSPACE_DIR, YOUR_ORDERS_DIR
from src.exporter import DashboardExporter
from src.loaders import UnifiedDataLoader

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("amazon_analytics")


def format_currency(val: float) -> str:
    """Format currency in Indian Rupee format."""
    return f"₹{val:,.2f}"


def print_executive_terminal_summary(kpis: dict, yearly: list, categories: list, returns: dict):
    """Print high-density executive analytics summary in the terminal."""
    w = 78
    print("\n" + "=" * w)
    print(" 📦 AMAZON ORDER ANALYSIS — EXECUTIVE PORTFOLIO SUMMARY".center(w))
    print("=" * w)
    
    start_d = kpis.get("dateRangeStart", "")
    end_d = kpis.get("dateRangeEnd", "")
    years_span = kpis.get("yearsSpanned", 0)
    print(f" Portfolio Date Range:   {start_d} to {end_d} ({years_span} years spanned)")
    print(f" Total Unified Orders:   {kpis.get('totalOrders', 0)} orders ({kpis.get('totalItems', 0)} items purchased)")
    print(f" Total Gross Spend:      {format_currency(kpis.get('grossSpend', 0))}")
    print(f" Realized Net Spend:     {format_currency(kpis.get('netSpend', 0))} (after returns & refunds)")
    print(f" Average Order Value:    {format_currency(kpis.get('averageOrderValue', 0))}")
    print(f" Monthly Run Rate:       {format_currency(kpis.get('spendPerMonth', 0))} / month")
    print(f" Total Discounts Saved:  {format_currency(kpis.get('totalDiscountsCaptured', 0))} ({kpis.get('discountSavingsRatePct', 0)}% captured savings)")
    print(f" Shipping Fees Paid:     {format_currency(kpis.get('totalShippingPaid', 0))}")
    print(f" Returns & Refunds:      {returns.get('totalReturns', 0)} returns ({returns.get('returnRatePct', 0)}% rate) -> {format_currency(returns.get('totalRefundAmount', 0))} recovered")
    
    print("\n" + "-" * w)
    print(" 📅 ANNUAL SPENDING TRAJECTORY".center(w))
    print("-" * w)
    print(f" {'Year':<6} {'Orders':<8} {'Gross Spend':<16} {'Net Spend':<16} {'AOV':<12} {'Returns':<8}")
    print(" " + "-" * (w - 2))
    for y in yearly:
        print(f" {y['year']:<6} {y['orderCount']:<8} {format_currency(y['grossSpend']):<16} {format_currency(y['netSpend']):<16} {format_currency(y['aov']):<12} {y['returnedCount']:<8}")

    print("\n" + "-" * w)
    print(" 🗂 TOP CATEGORIES BY SPEND SHARE".center(w))
    print("-" * w)
    print(f" {'Category':<32} {'Orders':<8} {'Spend':<16} {'Share %':<10}")
    print(" " + "-" * (w - 2))
    for c in categories[:8]:
        print(f" {c['category']:<32} {c['orderCount']:<8} {format_currency(c['spend']):<16} {c['spendSharePct']:>6.1f}%")

    print("\n" + "=" * w)
    print(f" 🚀 Interactive Dashboard generated at: {OUTPUT_DASHBOARD.name}")
    print(f" 📄 Master JSON dataset exported at:   {OUTPUT_JSON.name}")
    print("=" * w + "\n")


import os

def run_pipeline(data_dir: Path = None, export_json_only: bool = False, taxonomy_file: Path = None):
    """Run data ingestion, analytics calculation, and artifact export."""
    from src.config import load_taxonomy
    if taxonomy_file:
        load_taxonomy(taxonomy_file)

    # Auto-discover data directory if none specified
    target_data_dir = data_dir
    if not target_data_dir:
        if YOUR_ORDERS_DIR.exists():
            target_data_dir = YOUR_ORDERS_DIR
        else:
            target_data_dir = WORKSPACE_DIR

    loader = UnifiedDataLoader(target_data_dir)
    orders = loader.load_all()
    if not orders:
        logger.error(f"No orders found or parsed in {target_data_dir}! Please check input directory.")
        return None, None
    
    order_list = list(orders.values())
    analyzer = OrderAnalyzer(order_list)
    analytics = analyzer.compute_all()
    
    exporter = DashboardExporter(order_list, analytics)
    json_path = exporter.export_json(OUTPUT_JSON)
    html_path = None
    if not export_json_only:
        html_path = exporter.export_html_dashboard(OUTPUT_DASHBOARD)
        # Sync to environment-provided artifact directory if configured
        env_artifact_dir = os.environ.get("ANTIGRAVITY_ARTIFACT_DIR")
        if env_artifact_dir and Path(env_artifact_dir).exists():
            try:
                import shutil
                shutil.copy2(html_path, Path(env_artifact_dir) / "amazon-dashboard.html")
            except Exception as e:
                logger.debug(f"Could not copy to artifact dir: {e}")
                
    print_executive_terminal_summary(
        analytics.get("summary", {}),
        analytics.get("yearly", []),
        analytics.get("categories", []),
        analytics.get("returns", {}),
    )
    return orders, analytics


def serve_dashboard(port: int = 8000):
    """Serve the interactive dashboard via local HTTP server."""
    class DashboardHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(WORKSPACE_DIR), **kwargs)

    url = f"http://localhost:{port}/dashboard.html"
    print(f"\n🌐 Starting Amazon Order Analytics server at {url}")
    print("Press Ctrl+C to stop the server.\n")
    try:
        with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
            webbrowser.open(url)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


def inspect_order(order_id: str, orders_dict: dict):
    """Inspect specific order details."""
    o = orders_dict.get(order_id)
    if not o:
        print(f"Order ID '{order_id}' not found.")
        return
    print(f"\nOrder Details: {o.order_id}")
    print(f"Date:          {o.order_date}")
    print(f"Type:          {o.order_type} ({o.status})")
    print(f"Total Amount:  {format_currency(o.total_amount)}")
    print(f"Carrier:       {o.carrier} (Tracking: {o.tracking_number or 'N/A'})")
    print(f"City/Address:  {o.city} - {o.shipping_address}")
    print("Items:")
    for it in o.items:
        print(f"  - [{it.asin}] {it.title} | Qty: {it.quantity} | {format_currency(it.unit_price)}")
    if o.return_info:
        r = o.return_info
        print(f"Return:        Reason={r.reason}, Resolution={r.resolution}, Refund={format_currency(r.refund_amount)}")
        if r.replacement_order_id:
            print(f"Replacement:   Order ID {r.replacement_order_id}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Amazon Order Analysis & Insights Suite")
    parser.add_argument("--serve", action="store_true", help="Launch local HTTP server to view the dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port for local HTTP server (default: 8000)")
    parser.add_argument("--export-json-only", action="store_true", help="Export JSON dataset without regenerating HTML")
    parser.add_argument("--inspect", type=str, help="Inspect detailed records for an Order ID")
    parser.add_argument("--data-dir", type=str, help="Custom data directory to scan for Amazon CSV/JSON orders")
    parser.add_argument("--taxonomy", type=str, help="Custom taxonomy JSON file for category classification")

    args = parser.parse_args()
    custom_dir = Path(args.data_dir) if args.data_dir else None
    taxonomy_file = Path(args.taxonomy) if args.taxonomy else None
    
    orders, analytics = run_pipeline(
        data_dir=custom_dir,
        export_json_only=args.export_json_only,
        taxonomy_file=taxonomy_file
    )
    
    if args.inspect and orders:
        inspect_order(args.inspect, orders)
    elif args.serve:
        serve_dashboard(port=args.port)


if __name__ == "__main__":
    main()
