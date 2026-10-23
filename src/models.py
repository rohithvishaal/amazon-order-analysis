"""Data models representing standardized orders, line items, returns, and analytics."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class LineItem:
    asin: str
    title: str
    macro_category: str
    subcategory: str
    quantity: int = 1
    unit_price: float = 0.0
    tax: float = 0.0
    discount: float = 0.0
    item_url: str = ""
    condition: str = "New"


@dataclass
class ReturnRecord:
    order_id: str
    return_date: Optional[datetime] = None
    reason: str = "Not Specified"
    resolution: str = "Refund"  # Refund, Exchange, Replacement
    refund_amount: float = 0.0
    replacement_order_id: Optional[str] = None
    tracking_id: Optional[str] = None
    status: str = "Completed"


@dataclass
class Order:
    order_id: str
    order_date: datetime
    order_type: str  # Physical Retail, Utility & Recharge, Digital Subscription, Digital Content, Borrowed
    status: str      # Delivered, Cancelled, In Transit / Arriving, Returned & Refunded, Replaced / Exchanged
    currency: str = "INR"
    total_amount: float = 0.0
    subtotal: float = 0.0
    tax: float = 0.0
    shipping_charge: float = 0.0
    discount: float = 0.0
    payment_method: str = "Not Available"
    carrier: str = "Not Available"
    tracking_number: str = ""
    shipping_address: str = ""
    city: str = "Not Available"
    details_url: str = ""
    items: List[LineItem] = field(default_factory=list)
    return_info: Optional[ReturnRecord] = None
    source_file: str = ""

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items) if self.items else 1

    @property
    def primary_category(self) -> str:
        return self.items[0].macro_category if self.items else "General Merchandise"

    @property
    def primary_subcategory(self) -> str:
        return self.items[0].subcategory if self.items else "Miscellaneous"

    @property
    def primary_title(self) -> str:
        return self.items[0].title if self.items else self.order_id

    def to_dict(self) -> Dict:
        """Serialize order to JSON-friendly dictionary."""
        return {
            "orderId": self.order_id,
            "orderDate": self.order_date.isoformat() if self.order_date else "",
            "orderType": self.order_type,
            "status": self.status,
            "currency": self.currency,
            "totalAmount": round(self.total_amount, 2),
            "subtotal": round(self.subtotal, 2),
            "tax": round(self.tax, 2),
            "shippingCharge": round(self.shipping_charge, 2),
            "discount": round(self.discount, 2),
            "paymentMethod": self.payment_method,
            "carrier": self.carrier,
            "trackingNumber": self.tracking_number,
            "shippingAddress": self.shipping_address,
            "city": self.city,
            "detailsUrl": self.details_url,
            "category": self.primary_category,
            "subcategory": self.primary_subcategory,
            "itemCount": self.item_count,
            "items": [
                {
                    "asin": item.asin,
                    "title": item.title,
                    "category": item.macro_category,
                    "subcategory": item.subcategory,
                    "quantity": item.quantity,
                    "unitPrice": round(item.unit_price, 2),
                    "tax": round(item.tax, 2),
                    "discount": round(item.discount, 2),
                    "itemUrl": item.item_url,
                    "condition": item.condition,
                }
                for item in self.items
            ],
            "returnInfo": {
                "returnDate": self.return_info.return_date.isoformat() if self.return_info and self.return_info.return_date else "",
                "reason": self.return_info.reason if self.return_info else "",
                "resolution": self.return_info.resolution if self.return_info else "",
                "refundAmount": round(self.return_info.refund_amount, 2) if self.return_info else 0.0,
                "replacementOrderId": self.return_info.replacement_order_id if self.return_info else None,
                "trackingId": self.return_info.tracking_id if self.return_info else "",
            } if self.return_info else None,
            "sourceFile": self.source_file,
        }

