"""Modular data loaders for discovering, fingerprinting, and parsing Amazon order data files."""

import csv
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .cleaners import (
    classify_product,
    clean_amount,
    extract_city,
    parse_carrier,
    parse_datetime_ist,
    standardize_status,
)
from .config import FILE_SIGNATURES, WORKSPACE_DIR, YOUR_ORDERS_DIR
from .models import LineItem, Order, ReturnRecord

logger = logging.getLogger(__name__)


def fingerprint_csv(path: Path) -> Optional[str]:
    """Detect CSV file type based on column signatures."""
    try:
        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                return None
            
            # Clean header names (strip BOM, quotes, whitespace)
            cols = {re_clean(col): col for col in header}
            
            # Check signatures
            for file_type, sig in FILE_SIGNATURES.items():
                reqs = [re_clean(r) for r in sig["required_columns"]]
                if all(r in cols for r in reqs):
                    return file_type
    except Exception as e:
        logger.warning(f"Error fingerprinting {path}: {e}")
    return None


def re_clean(name: str) -> str:
    """Normalize column name for robust matching."""
    return "".join(c.lower() for c in name if c.isalnum())


class ReturnsAndRefundsLoader:
    """Loads and aggregates return requests, return status, refunds, and replacements."""

    def __init__(self):
        self.returns_by_order: Dict[str, ReturnRecord] = {}

    def load_returns_status(self, path: Path):
        """Parse Returns Status.csv."""
        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = row.get("Order ID", "").strip()
                if not order_id:
                    continue
                
                dt = parse_datetime_ist(row.get("Date of Return") or row.get("Return Creation Date"))
                reason = row.get("Return Reason", "").strip() or "Not Specified"
                res = row.get("Return Resolution", "").strip() or "Refund"
                amt = clean_amount(row.get("Return Amount"))
                track = row.get("Carrier Tracking ID", "").strip() or row.get("Return Receivable Tracking ID", "").strip()
                
                if order_id not in self.returns_by_order:
                    self.returns_by_order[order_id] = ReturnRecord(
                        order_id=order_id,
                        return_date=dt,
                        reason=reason,
                        resolution=res,
                        refund_amount=amt,
                        tracking_id=track if track != "Not Applicable" else "",
                    )
                else:
                    rec = self.returns_by_order[order_id]
                    if not rec.return_date and dt:
                        rec.return_date = dt
                    if rec.reason in ("Not Specified", "Unknown Reason") and reason:
                        rec.reason = reason
                    if amt > rec.refund_amount:
                        rec.refund_amount = amt

    def load_refund_details(self, path: Path):
        """Parse Refund Details.csv."""
        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = row.get("Order ID", "").strip()
                if not order_id:
                    continue
                
                dt = parse_datetime_ist(row.get("Creation Date") or row.get("Refund Date"))
                reason = row.get("Reversal Reason", "").strip()
                amt = clean_amount(row.get("Refund Amount"))
                
                if order_id not in self.returns_by_order:
                    self.returns_by_order[order_id] = ReturnRecord(
                        order_id=order_id,
                        return_date=dt,
                        reason=reason if reason else "Refund Processed",
                        resolution="Refund",
                        refund_amount=amt,
                    )
                else:
                    rec = self.returns_by_order[order_id]
                    if amt > 0 and rec.refund_amount == 0:
                        rec.refund_amount = amt
                    if reason and rec.reason in ("Not Specified", "Refund Processed"):
                        rec.reason = reason

    def load_replacement_orders(self, path: Path):
        """Parse Replacement Orders.csv linking original order to replacement order ID."""
        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Header might have quotes or BOM
                clean_row = {k.strip(' \ufeff"'): v for k, v in row.items() if k}
                order_id = clean_row.get("Order ID", "").strip()
                rep_id = clean_row.get("Replacement Order ID", "").strip()
                if order_id and rep_id and rep_id != "No Replacement Order ID":
                    if order_id in self.returns_by_order:
                        self.returns_by_order[order_id].replacement_order_id = rep_id
                        self.returns_by_order[order_id].resolution = "Exchange"
                    else:
                        self.returns_by_order[order_id] = ReturnRecord(
                            order_id=order_id,
                            reason="Replacement Order Placed",
                            resolution="Exchange",
                            replacement_order_id=rep_id,
                        )

    def load_return_requests(self, path: Path):
        """Parse Return Requests.csv."""
        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = row.get("Order ID", "").strip()
                reason_code = row.get("Return Reason Code", "").strip()
                if order_id and reason_code:
                    clean_reason = reason_code.replace("CR-", "").replace("_", " ").title()
                    if order_id in self.returns_by_order:
                        rec = self.returns_by_order[order_id]
                        if rec.reason in ("Not Specified", "Refund Processed"):
                            rec.reason = clean_reason
                    else:
                        self.returns_by_order[order_id] = ReturnRecord(
                            order_id=order_id,
                            reason=clean_reason,
                            resolution="Refund",
                        )


class UnifiedDataLoader:
    """Discovers, parses, and harmonizes all Amazon data files across directories."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or YOUR_ORDERS_DIR
        self.returns_loader = ReturnsAndRefundsLoader()
        self.orders: Dict[str, Order] = {}
        self.discovered_files: List[Tuple[Path, str]] = []
        self.invoice_files: List[Path] = []

    def discover_files(self) -> List[Tuple[Path, str]]:
        """Walk data directory to identify all official Amazon order data sources."""
        self.discovered_files.clear()
        self.invoice_files.clear()
        
        # Scan data directory
        scan_dirs = [self.data_dir]
        scanned_paths: Set[Path] = set()
        
        for s_dir in scan_dirs:
            if not s_dir.exists():
                continue
            for p in s_dir.rglob("*"):
                if p in scanned_paths or not p.is_file():
                    continue
                scanned_paths.add(p)
                
                # Check for PDF invoices
                if p.suffix.lower() == ".pdf" and "TransactionalInvoicing" in p.name:
                    self.invoice_files.append(p)
                    continue
                
                # Check for CSV files
                if p.suffix.lower() == ".csv":
                    ftype = fingerprint_csv(p)
                    if ftype:
                        self.discovered_files.append((p, ftype))
        
        return self.discovered_files

    def load_all(self) -> Dict[str, Order]:
        """Execute full modular loading pipeline on official Amazon CSV exports."""
        self.discover_files()
        
        # 1. First pass: load all returns and refunds metadata
        for path, ftype in self.discovered_files:
            if ftype == "returns_status":
                self.returns_loader.load_returns_status(path)
            elif ftype == "refund_details":
                self.returns_loader.load_refund_details(path)
            elif ftype == "replacement_orders":
                self.returns_loader.load_replacement_orders(path)
            elif ftype == "return_requests":
                self.returns_loader.load_return_requests(path)

        # 2. Second pass: load Order History (Physical Orders & Utility Recharges)
        for path, ftype in self.discovered_files:
            if ftype == "order_history":
                self._load_order_history(path)

        # 3. Third pass: load Digital Content Orders
        for path, ftype in self.discovered_files:
            if ftype == "digital_orders":
                self._load_digital_orders(path)

        logger.info(f"Loaded {len(self.orders)} total unified orders from {len(self.discovered_files)} files.")
        return self.orders

    def _load_order_history(self, path: Path):
        """Parse Order History.csv rows into Order and LineItem models."""
        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = row.get("Order ID", "").strip()
                if not order_id:
                    continue
                
                order_date = parse_datetime_ist(row.get("Order Date"))
                if not order_date:
                    continue
                
                title = row.get("Product Name", "").strip() or "Amazon Retail Item"
                macro_cat, sub_cat = classify_product(title)
                
                # Determine order type
                addr = row.get("Shipping Address", "").strip()
                city = extract_city(addr)
                if macro_cat == "Utilities & Recharges":
                    order_type = "Utility & Recharge"
                elif macro_cat == "Digital Services & Subscriptions":
                    order_type = "Digital Subscription"
                else:
                    order_type = "Physical Retail"
                
                unit_price = clean_amount(row.get("Unit Price"))
                tax = clean_amount(row.get("Unit Price Tax"))
                total_amt = clean_amount(row.get("Total Amount"))
                subtotal = clean_amount(row.get("Shipment Item Subtotal"))
                shipping = clean_amount(row.get("Shipping Charge"))
                discount = abs(clean_amount(row.get("Total Discounts")))
                
                try:
                    qty = int(clean_amount(row.get("Original Quantity")))
                    if qty <= 0:
                        qty = 1
                except Exception:
                    qty = 1
                
                asin = row.get("ASIN", "").strip()
                carrier_raw = row.get("Carrier Name & Tracking Number", "")
                carrier_name, tracking_no = parse_carrier(carrier_raw)
                payment_method = row.get("Payment Method Type", "").strip() or "Not Available"
                order_stat = row.get("Order Status", "")
                ship_stat = row.get("Shipment Status", "")
                
                ret_info = self.returns_loader.returns_by_order.get(order_id)
                final_status = standardize_status(order_stat, ship_stat, ret_info.__dict__ if ret_info else None)
                
                # Details URL from JSON if available
                details_url = ""
                # Official Amazon Order Details link
                details_url = f"https://www.amazon.in/gp/your-account/order-details?orderID={order_id}"
                item_url = f"https://www.amazon.in/dp/{asin}" if asin and asin != "Not Available" else ""
                
                line_item = LineItem(
                    asin=asin,
                    title=title,
                    macro_category=macro_cat,
                    subcategory=sub_cat,
                    quantity=qty,
                    unit_price=unit_price,
                    tax=tax,
                    discount=discount,
                    item_url=item_url,
                    condition=row.get("Product Condition", "New") or "New",
                )
                
                if order_id not in self.orders:
                    self.orders[order_id] = Order(
                        order_id=order_id,
                        order_date=order_date,
                        order_type=order_type,
                        status=final_status,
                        currency=row.get("Currency", "INR") or "INR",
                        total_amount=total_amt,
                        subtotal=subtotal if subtotal > 0 else unit_price * qty,
                        tax=tax,
                        shipping_charge=shipping,
                        discount=discount,
                        payment_method=payment_method,
                        carrier=carrier_name,
                        tracking_number=tracking_no,
                        shipping_address=addr if addr != "Not Available" else "",
                        city=city,
                        details_url=details_url,
                        items=[line_item],
                        return_info=ret_info,
                        source_file=path.name,
                    )
                else:
                    # Multi-item order: append line item and accumulate subtotal/tax
                    existing = self.orders[order_id]
                    existing.items.append(line_item)
                    if subtotal > 0:
                        existing.subtotal += subtotal
                    if tax > 0:
                        existing.tax += tax
                    if discount > 0:
                        existing.discount += discount
                    if total_amt > existing.total_amount:
                        existing.total_amount = total_amt

    def _load_digital_orders(self, path: Path):
        """Parse Digital Content Orders.csv into Order and LineItem models."""
        with open(path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_id = row.get("Order ID", "").strip()
                if not order_id:
                    continue
                
                # If already loaded from Order History with full info, skip to prevent double counting
                if order_id in self.orders:
                    continue
                
                order_date = parse_datetime_ist(row.get("Order Date"))
                if not order_date:
                    continue
                
                title = row.get("Product Name", "").strip() or "Amazon Digital Content"
                macro_cat, sub_cat = classify_product(title)
                price = clean_amount(row.get("Price"))
                tax = clean_amount(row.get("Price Tax"))
                tx_amt = clean_amount(row.get("Transaction Amount"))
                total = tx_amt if tx_amt > 0 else price
                
                asin = row.get("ASIN", "").strip()
                item_url = f"https://www.amazon.in/dp/{asin}" if asin and asin != "Not Available" else ""
                
                line_item = LineItem(
                    asin=asin,
                    title=title,
                    macro_category=macro_cat,
                    subcategory=sub_cat,
                    quantity=1,
                    unit_price=price,
                    tax=tax,
                    discount=0.0,
                    item_url=item_url,
                )
                
                ret_info = self.returns_loader.returns_by_order.get(order_id)
                final_status = "Returned & Refunded" if ret_info else "Delivered"
                
                self.orders[order_id] = Order(
                    order_id=order_id,
                    order_date=order_date,
                    order_type="Digital Content",
                    status=final_status,
                    currency="INR",
                    total_amount=total,
                    subtotal=price,
                    tax=tax,
                    shipping_charge=0.0,
                    discount=0.0,
                    payment_method="Digital Payment",
                    carrier="Digital Delivery",
                    tracking_number="",
                    shipping_address="Digital Delivery",
                    city="Digital",
                    details_url=f"https://www.amazon.in/gp/your-account/order-details?orderID={order_id}",
                    items=[line_item],
                    return_info=ret_info,
                    source_file=path.name,
                )

