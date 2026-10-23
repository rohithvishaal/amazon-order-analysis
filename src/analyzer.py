"""Comprehensive analytical engine computing KPIs, time series, categories, logistics, and returns."""

from collections import Counter, defaultdict
from datetime import datetime
import math
from typing import Any, Dict, List
from .models import Order


class OrderAnalyzer:
    """Computes multidimensional analytics and insights across unified orders."""

    def __init__(self, orders: List[Order]):
        self.orders = orders

    def compute_all(self) -> Dict[str, Any]:
        """Run all analytics modules and return consolidated dictionary."""
        return {
            "summary": self.compute_kpis(),
            "yearly": self.compute_yearly_trends(),
            "monthly": self.compute_monthly_trends(),
            "time_patterns": self.compute_time_patterns(),
            "categories": self.compute_category_analytics(),
            "logistics": self.compute_logistics_analytics(),
            "returns": self.compute_returns_analytics(),
            "geography": self.compute_geographic_analytics(),
            "top_splurges": self.compute_top_splurges(),
            "repeat_purchases": self.compute_repeat_purchases(),
            "price_brackets": self.compute_price_brackets(),
        }

    def compute_kpis(self) -> Dict[str, Any]:
        """Compute top-level executive KPIs."""
        total_orders = len(self.orders)
        if total_orders == 0:
            return {}
        
        gross_spend = sum(o.total_amount for o in self.orders)
        cancelled_orders = [o for o in self.orders if o.status == "Cancelled"]
        cancelled_spend = sum(o.total_amount for o in cancelled_orders)
        
        delivered_orders = [o for o in self.orders if o.status in ("Delivered", "In Transit / Arriving")]
        delivered_spend = sum(o.total_amount for o in delivered_orders)
        
        refunded_orders = [o for o in self.orders if o.status in ("Returned & Refunded", "Replaced / Exchanged")]
        refunded_spend = sum(o.total_amount for o in refunded_orders)
        
        total_refund_amount = sum(
            (o.return_info.refund_amount if o.return_info and o.return_info.refund_amount > 0 else o.total_amount)
            for o in self.orders
            if o.status == "Returned & Refunded"
        )
        
        # Net spend: delivered spend + in-transit spend (minus refunds)
        net_spend = gross_spend - cancelled_spend - total_refund_amount
        
        total_discounts = sum(o.discount for o in self.orders)
        total_shipping_charges = sum(o.shipping_charge for o in self.orders)
        total_items = sum(o.item_count for o in self.orders)
        
        # Effective order count excluding cancelled
        valid_orders = [o for o in self.orders if o.status != "Cancelled"]
        aov = (gross_spend - cancelled_spend) / len(valid_orders) if valid_orders else 0.0
        
        dates = [o.order_date for o in self.orders if o.order_date]
        min_date = min(dates) if dates else None
        max_date = max(dates) if dates else None
        
        days_span = (max_date - min_date).days if min_date and max_date else 1
        years_span = max(1, days_span / 365.25)
        spend_per_month = net_spend / (years_span * 12)
        
        return {
            "totalOrders": total_orders,
            "totalItems": total_items,
            "grossSpend": round(gross_spend, 2),
            "netSpend": round(net_spend, 2),
            "cancelledSpend": round(cancelled_spend, 2),
            "cancelledCount": len(cancelled_orders),
            "deliveredCount": len(delivered_orders),
            "deliveredSpend": round(delivered_spend, 2),
            "returnedCount": len(refunded_orders),
            "totalRefundRecovered": round(total_refund_amount, 2),
            "totalDiscountsCaptured": round(total_discounts, 2),
            "discountSavingsRatePct": round((total_discounts / (gross_spend + total_discounts) * 100), 2) if (gross_spend + total_discounts) > 0 else 0.0,
            "totalShippingPaid": round(total_shipping_charges, 2),
            "averageOrderValue": round(aov, 2),
            "dateRangeStart": min_date.strftime("%Y-%m-%d") if min_date else "",
            "dateRangeEnd": max_date.strftime("%Y-%m-%d") if max_date else "",
            "yearsSpanned": round(years_span, 1),
            "spendPerMonth": round(spend_per_month, 2),
        }

    def compute_yearly_trends(self) -> List[Dict[str, Any]]:
        """Compute annual financial and operational performance metrics."""
        yearly_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "year": "",
            "orderCount": 0,
            "grossSpend": 0.0,
            "netSpend": 0.0,
            "cancelledCount": 0,
            "cancelledSpend": 0.0,
            "returnedCount": 0,
            "refundedAmount": 0.0,
            "discounts": 0.0,
            "shippingPaid": 0.0,
            "itemsCount": 0,
        })
        
        for o in self.orders:
            yr = o.order_date.strftime("%Y") if o.order_date else "Unknown"
            y = yearly_map[yr]
            y["year"] = yr
            y["orderCount"] += 1
            y["grossSpend"] += o.total_amount
            y["discounts"] += o.discount
            y["shippingPaid"] += o.shipping_charge
            y["itemsCount"] += o.item_count
            
            if o.status == "Cancelled":
                y["cancelledCount"] += 1
                y["cancelledSpend"] += o.total_amount
            elif o.status == "Returned & Refunded":
                y["returnedCount"] += 1
                ref_amt = o.return_info.refund_amount if o.return_info and o.return_info.refund_amount > 0 else o.total_amount
                y["refundedAmount"] += ref_amt
            elif o.status == "Replaced / Exchanged":
                y["returnedCount"] += 1
        
        results = []
        for yr in sorted(yearly_map.keys()):
            y = yearly_map[yr]
            valid_count = y["orderCount"] - y["cancelledCount"]
            net = y["grossSpend"] - y["cancelledSpend"] - y["refundedAmount"]
            aov = (y["grossSpend"] - y["cancelledSpend"]) / valid_count if valid_count > 0 else 0.0
            results.append({
                "year": yr,
                "orderCount": y["orderCount"],
                "grossSpend": round(y["grossSpend"], 2),
                "netSpend": round(net, 2),
                "aov": round(aov, 2),
                "cancelledCount": y["cancelledCount"],
                "cancelledSpend": round(y["cancelledSpend"], 2),
                "returnedCount": y["returnedCount"],
                "refundedAmount": round(y["refundedAmount"], 2),
                "discounts": round(y["discounts"], 2),
                "shippingPaid": round(y["shippingPaid"], 2),
                "itemsCount": y["itemsCount"],
            })
        return results

    def compute_monthly_trends(self) -> List[Dict[str, Any]]:
        """Compute continuous month-by-month spend and order volume."""
        monthly_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "yearMonth": "",
            "spend": 0.0,
            "orderCount": 0,
            "itemsCount": 0,
        })
        
        for o in self.orders:
            if not o.order_date:
                continue
            ym = o.order_date.strftime("%Y-%m")
            m = monthly_map[ym]
            m["yearMonth"] = ym
            m["spend"] += o.total_amount
            m["orderCount"] += 1
            m["itemsCount"] += o.item_count
            
        results = []
        for ym in sorted(monthly_map.keys()):
            m = monthly_map[ym]
            results.append({
                "yearMonth": ym,
                "spend": round(m["spend"], 2),
                "orderCount": m["orderCount"],
                "itemsCount": m["itemsCount"],
            })
        return results

    def compute_time_patterns(self) -> Dict[str, Any]:
        """Compute day-of-week and hour-of-day purchase distributions."""
        dow_counts = [0] * 7  # 0=Monday, 6=Sunday
        dow_spends = [0.0] * 7
        hod_counts = [0] * 24
        hod_spends = [0.0] * 24
        
        dates_set = set()
        for o in self.orders:
            if not o.order_date:
                continue
            dt = o.order_date
            dow = dt.weekday()
            hod = dt.hour
            dates_set.add(dt.date())
            
            dow_counts[dow] += 1
            dow_spends[dow] += o.total_amount
            hod_counts[hod] += 1
            hod_spends[hod] += o.total_amount
            
        days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_list = [
            {"day": days_names[i], "count": dow_counts[i], "spend": round(dow_spends[i], 2)}
            for i in range(7)
        ]
        hod_list = [
            {"hour": h, "label": f"{h:02d}:00", "count": hod_counts[h], "spend": round(hod_spends[h], 2)}
            for h in range(24)
        ]
        
        # Calculate streaks
        sorted_dates = sorted(list(dates_set))
        max_streak = 1
        current_streak = 1
        streak_start = sorted_dates[0] if sorted_dates else None
        best_streak_start = streak_start
        
        for i in range(1, len(sorted_dates)):
            diff = (sorted_dates[i] - sorted_dates[i - 1]).days
            if diff == 1:
                current_streak += 1
                if current_streak > max_streak:
                    max_streak = current_streak
                    best_streak_start = streak_start
            else:
                current_streak = 1
                streak_start = sorted_dates[i]
                
        return {
            "dayOfWeek": dow_list,
            "hourOfDay": hod_list,
            "peakDay": max(dow_list, key=lambda x: x["count"])["day"] if dow_list else "",
            "peakHour": max(hod_list, key=lambda x: x["count"])["label"] if hod_list else "",
            "longestDayStreak": max_streak,
            "streakStartDate": best_streak_start.strftime("%Y-%m-%d") if best_streak_start else "",
            "activeShoppingDays": len(sorted_dates),
        }

    def compute_category_analytics(self) -> List[Dict[str, Any]]:
        """Compute spend and volume aggregations by macro-category and subcategory."""
        cat_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "category": "",
            "spend": 0.0,
            "orderCount": 0,
            "itemCount": 0,
            "subcategories": Counter(),
            "cancelledCount": 0,
            "returnedCount": 0,
        })
        
        total_spend = sum(o.total_amount for o in self.orders)
        for o in self.orders:
            cat = o.primary_category
            m = cat_map[cat]
            m["category"] = cat
            m["spend"] += o.total_amount
            m["orderCount"] += 1
            m["itemCount"] += o.item_count
            m["subcategories"][o.primary_subcategory] += 1
            if o.status == "Cancelled":
                m["cancelledCount"] += 1
            elif o.status in ("Returned & Refunded", "Replaced / Exchanged"):
                m["returnedCount"] += 1
                
        results = []
        for cat, data in sorted(cat_map.items(), key=lambda x: x[1]["spend"], reverse=True):
            pct = (data["spend"] / total_spend * 100) if total_spend > 0 else 0.0
            avg_order = data["spend"] / data["orderCount"] if data["orderCount"] > 0 else 0.0
            subs = [{"subcategory": s, "count": c} for s, c in data["subcategories"].most_common()]
            results.append({
                "category": cat,
                "spend": round(data["spend"], 2),
                "orderCount": data["orderCount"],
                "itemCount": data["itemCount"],
                "averageOrderValue": round(avg_order, 2),
                "spendSharePct": round(pct, 2),
                "cancelledCount": data["cancelledCount"],
                "returnedCount": data["returnedCount"],
                "topSubcategories": subs,
            })
        return results

    def compute_logistics_analytics(self) -> Dict[str, Any]:
        """Analyze shipping carriers, lead times, and fulfillment options."""
        carrier_counts = Counter()
        carrier_spends = defaultdict(float)
        lead_times = []
        shipping_options = Counter()
        
        for o in self.orders:
            if o.order_type == "Physical Retail":
                carrier_counts[o.carrier] += 1
                carrier_spends[o.carrier] += o.total_amount
                
        carriers_list = [
            {"carrier": c, "count": cnt, "spend": round(carrier_spends[c], 2)}
            for c, cnt in carrier_counts.most_common()
        ]
        
        return {
            "carriers": carriers_list,
            "primaryCarrier": carriers_list[0]["carrier"] if carriers_list else "Unknown",
            "totalPhysicalShipments": sum(carrier_counts.values()),
        }

    def compute_returns_analytics(self) -> Dict[str, Any]:
        """Analyze returns, refund recovery rates, reasons, and replacements."""
        return_reasons = Counter()
        resolutions = Counter()
        total_refund_amount = 0.0
        returned_orders = []
        replacement_links = []
        
        for o in self.orders:
            if o.return_info:
                rec = o.return_info
                return_reasons[rec.reason] += 1
                resolutions[rec.resolution] += 1
                total_refund_amount += rec.refund_amount
                returned_orders.append({
                    "orderId": o.order_id,
                    "date": rec.return_date.strftime("%Y-%m-%d") if rec.return_date else o.order_date.strftime("%Y-%m-%d"),
                    "itemTitle": o.primary_title,
                    "category": o.primary_category,
                    "reason": rec.reason,
                    "resolution": rec.resolution,
                    "refundAmount": round(rec.refund_amount, 2),
                    "replacementOrderId": rec.replacement_order_id,
                    "trackingId": rec.tracking_id,
                })
                if rec.replacement_order_id:
                    replacement_links.append({
                        "originalOrderId": o.order_id,
                        "replacementOrderId": rec.replacement_order_id,
                        "itemTitle": o.primary_title,
                        "reason": rec.reason,
                    })
                    
        physical_delivered = sum(1 for o in self.orders if o.order_type == "Physical Retail" and o.status != "Cancelled")
        return_rate_pct = (len(returned_orders) / physical_delivered * 100) if physical_delivered > 0 else 0.0
        
        return {
            "totalReturns": len(returned_orders),
            "returnRatePct": round(return_rate_pct, 2),
            "totalRefundAmount": round(total_refund_amount, 2),
            "reasons": [{"reason": r, "count": c} for r, c in return_reasons.most_common()],
            "resolutions": [{"resolution": res, "count": c} for res, c in resolutions.most_common()],
            "replacementLinks": replacement_links,
            "returnRecords": returned_orders,
        }

    def compute_geographic_analytics(self) -> List[Dict[str, Any]]:
        """Compute timeline and spend by recipient city/location."""
        city_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "city": "",
            "orderCount": 0,
            "spend": 0.0,
            "firstDate": None,
            "lastDate": None,
        })
        
        for o in self.orders:
            city = o.city
            if city in ("Not Available", "Digital"):
                continue
            m = city_map[city]
            m["city"] = city
            m["orderCount"] += 1
            m["spend"] += o.total_amount
            dt = o.order_date
            if dt:
                if not m["firstDate"] or dt < m["firstDate"]:
                    m["firstDate"] = dt
                if not m["lastDate"] or dt > m["lastDate"]:
                    m["lastDate"] = dt
                    
        results = []
        for city, data in sorted(city_map.items(), key=lambda x: x[1]["orderCount"], reverse=True):
            results.append({
                "city": city,
                "orderCount": data["orderCount"],
                "spend": round(data["spend"], 2),
                "firstOrder": data["firstDate"].strftime("%Y-%m-%d") if data["firstDate"] else "",
                "lastOrder": data["lastDate"].strftime("%Y-%m-%d") if data["lastDate"] else "",
            })
        return results

    def compute_top_splurges(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Extract top highest-value realized orders (excluding cancellations)."""
        realized_orders = [o for o in self.orders if o.status != "Cancelled"]
        sorted_orders = sorted(realized_orders, key=lambda x: x.total_amount, reverse=True)
        results = []
        for o in sorted_orders[:limit]:
            results.append({
                "orderId": o.order_id,
                "date": o.order_date.strftime("%Y-%m-%d") if o.order_date else "",
                "amount": round(o.total_amount, 2),
                "title": o.primary_title,
                "category": o.primary_category,
                "subcategory": o.primary_subcategory,
                "status": o.status,
                "detailsUrl": o.details_url,
                "itemUrl": o.items[0].item_url if o.items else "",
            })
        return results

    def compute_repeat_purchases(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Identify items purchased multiple times, accurately accounting for delivered, returned, and cancelled orders."""
        item_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "title": "",
            "asin": "",
            "totalAttempts": 0,
            "deliveredCount": 0,
            "cancelledCount": 0,
            "refundedCount": 0,
            "replacedCount": 0,
            "keptCount": 0,
            "deliveredQty": 0,
            "grossSpend": 0.0,
            "refundAmount": 0.0,
        })
        
        for o in self.orders:
            total_val = sum(it.unit_price * it.quantity for it in o.items)
            n_items = len(o.items) or 1
            for item in o.items:
                if not item.title:
                    continue
                t = item.title.strip()
                s = item_stats[t]
                s["title"] = t
                if item.asin:
                    s["asin"] = item.asin
                s["totalAttempts"] += 1
                
                if o.status == "Cancelled":
                    s["cancelledCount"] += 1
                else:
                    s["deliveredCount"] += 1
                    s["deliveredQty"] += item.quantity
                    
                    # Compute apportioned order gross and refund for this item
                    item_share = ((item.unit_price * item.quantity) / total_val) if total_val > 0 else (1.0 / n_items)
                    order_gross = o.total_amount if o.total_amount > 0 else (item.unit_price * item.quantity)
                    s["grossSpend"] += (order_gross * item_share)
                    
                    if o.status == "Returned & Refunded":
                        s["refundedCount"] += 1
                        ref = (o.return_info.refund_amount if (o.return_info and o.return_info.refund_amount > 0) else order_gross)
                        s["refundAmount"] += (ref * item_share)
                    elif o.status == "Replaced / Exchanged":
                        s["replacedCount"] += 1
                    else:
                        s["keptCount"] += 1
                        
        # Only items with at least 2 delivered orders qualify as repeat purchases
        repeats = []
        for t, data in item_stats.items():
            if data["deliveredCount"] >= 2:
                net_spend = max(0.0, data["grossSpend"] - data["refundAmount"])
                repeats.append({
                    "title": data["title"],
                    "asin": data["asin"],
                    "count": data["deliveredCount"],            # Total times delivered
                    "deliveredQty": data["deliveredQty"],        # Actual units delivered
                    "keptCount": data["keptCount"],              # Units retained without return
                    "refundedCount": data["refundedCount"],      # Orders returned & refunded
                    "replacedCount": data["replacedCount"],      # Orders replaced / exchanged
                    "cancelledCount": data["cancelledCount"],    # Orders cancelled
                    "totalAttempts": data["totalAttempts"],      # Total order attempts
                    "grossSpend": round(data["grossSpend"], 2),  # Total gross invoiced
                    "refundAmount": round(data["refundAmount"], 2), # Cash refunded
                    "totalSpend": round(net_spend, 2),          # Net realized spend
                })
                
        # Rank by delivered count descending, then net spend descending
        repeats.sort(key=lambda x: (x["count"], x["totalSpend"]), reverse=True)
        return repeats[:limit]

    def compute_price_brackets(self) -> List[Dict[str, Any]]:
        """Distribution of orders across price brackets."""
        brackets = [
            ("Under ₹200", 0, 200),
            ("₹200 - ₹500", 200, 500),
            ("₹500 - ₹1,000", 500, 1000),
            ("₹1,000 - ₹2,500", 1000, 2500),
            ("₹2,500 - ₹5,000", 2500, 5000),
            ("₹5,000 - ₹10,000", 5000, 10000),
            ("Above ₹10,000", 10000, float("inf")),
        ]
        bracket_counts = [0] * len(brackets)
        bracket_spends = [0.0] * len(brackets)
        
        for o in self.orders:
            amt = o.total_amount
            for i, (_, low, high) in enumerate(brackets):
                if low <= amt < high:
                    bracket_counts[i] += 1
                    bracket_spends[i] += amt
                    break
                    
        return [
            {"bracket": brackets[i][0], "count": bracket_counts[i], "spend": round(bracket_spends[i], 2)}
            for i in range(len(brackets))
        ]

