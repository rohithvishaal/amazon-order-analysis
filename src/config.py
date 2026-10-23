"""Configuration, taxonomy, and classification definitions for Amazon Order Analysis.

Designed to be universal, modular, and portable across different users and datasets.
"""

import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Base workspace paths (dynamically resolved)
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
YOUR_ORDERS_DIR = WORKSPACE_DIR / "Your Orders"
OUTPUT_DASHBOARD = WORKSPACE_DIR / "dashboard.html"
OUTPUT_JSON = WORKSPACE_DIR / "amazon_orders_master.json"

# Column signatures for dynamic file format detection
FILE_SIGNATURES = {
    "order_history": {
        "required_columns": ["Order ID", "Order Date", "Product Name", "Total Amount"],
        "optional_columns": ["ASIN", "Shipping Address", "Carrier Name & Tracking Number", "Shipping Charge"],
    },
    "digital_orders": {
        "required_columns": ["Order ID", "Product Name", "Price", "Order Date"],
        "optional_columns": ["Digital Order Item ID", "Delivery Status", "Transaction Amount"],
    },
    "returns_status": {
        "required_columns": ["Order ID", "Return Reason", "Return Resolution"],
        "optional_columns": ["Date of Return", "Return Amount", "Return Receivable State"],
    },
    "refund_details": {
        "required_columns": ["Order ID", "Refund Amount", "Disbursement Type"],
        "optional_columns": ["Creation Date", "Reversal Reason", "Reversal Status"],
    },
    "return_requests": {
        "required_columns": ["Order ID", "Return Reason Code"],
        "optional_columns": ["Product Name", "Return Shipping Method"],
    },
    "replacement_orders": {
        "required_columns": ["Order ID", "Replacement Order ID"],
        "optional_columns": [],
    },
    "digital_borrowed": {
        "required_columns": ["ASIN", "Product Name", "Loan Status", "Loan Program"],
        "optional_columns": ["Loan Creation Date", "End Date"],
    },
    "digital_returns": {
        "required_columns": ["ASIN", "Refund Amount", "Status"],
        "optional_columns": ["Order Date", "Transaction Amount"],
    },
}

# Universal Carrier Normalization
CARRIER_MAPPING: Dict[str, str] = {
    "ATS": "Amazon Transportation Services (ATS)",
    "AMZN": "Amazon Transportation Services (ATS)",
    "SVAFN": "Amazon Seller Fulfilled / AFN",
    "INGCFN": "Amazon In-Group Courier Network",
    "DLV": "Delhivery Express",
    "DELHIVERY": "Delhivery Express",
    "BLUEDART": "Blue Dart Express",
    "BLUE DART": "Blue Dart Express",
    "DTDC": "DTDC Express",
    "INDIA": "India Post",
    "INDIA POST": "India Post",
    "ECOM": "Ecom Express",
    "ECOM EXPRESS": "Ecom Express",
    "SHADOWFAX": "Shadowfax Technologies",
    "XPRESSBEES": "Xpressbees Logistics",
    "EKART": "Ekart Logistics",
    "FEDEX": "FedEx Express",
    "UPS": "UPS (United Parcel Service)",
    "USPS": "US Postal Service (USPS)",
    "DHL": "DHL Express",
    "ROYAL MAIL": "Royal Mail",
    "HERMES": "Evri / Hermes",
    "DPD": "DPD Group",
    "LDSH": "Local Delivery & Shipper",
}

# Exhaustive Indian States and Union Territories for address extraction
INDIAN_STATES: List[str] = [
    "ANDAMAN AND NICOBAR ISLANDS", "ANDHRA PRADESH", "ARUNACHAL PRADESH", "ASSAM", "BIHAR",
    "CHANDIGARH", "CHHATTISGARH", "DADRA AND NAGAR HAVELI", "DAMAN AND DIU", "DELHI",
    "GOA", "GUJARAT", "HARYANA", "HIMACHAL PRADESH", "JAMMU AND KASHMIR", "JHARKHAND",
    "KARNATAKA", "KERALA", "LADAKH", "LAKSHADWEEP", "MADHYA PRADESH", "MAHARASHTRA",
    "MANIPUR", "MEGHALAYA", "MIZORAM", "NAGALAND", "ODISHA", "PUDUCHERRY", "PUNJAB",
    "RAJASTHAN", "SIKKIM", "TAMIL NADU", "TELANGANA", "TRIPURA", "UTTAR PRADESH",
    "UTTARAKHAND", "WEST BENGAL"
]

# US States and Canadian Provinces for international Amazon exports
US_STATES: Dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia"
}

# Major Cities Catalog (India & International) for high-accuracy instant matching
POPULAR_CITIES: Dict[str, str] = {
    # Metro & Tier-1/2 India
    "mumbai": "Mumbai", "bombay": "Mumbai", "navi mumbai": "Navi Mumbai", "thane": "Thane",
    "delhi": "New Delhi", "new delhi": "New Delhi", "noida": "Noida", "greater noida": "Greater Noida",
    "gurgaon": "Gurugram", "gurugram": "Gurugram", "ghaziabad": "Ghaziabad", "faridabad": "Faridabad",
    "bengaluru": "Bengaluru", "bangalore": "Bengaluru", "mysore": "Mysuru", "mysuru": "Mysuru",
    "hyderabad": "Hyderabad", "secunderabad": "Secunderabad", "warangal": "Warangal", "khammam": "Khammam",
    "bhadrachalam": "Bhadrachalam", "karimnagar": "Karimnagar", "nizamabad": "Nizamabad",
    "chennai": "Chennai", "madras": "Chennai", "coimbatore": "Coimbatore", "madurai": "Madurai", "salem": "Salem",
    "kolkata": "Kolkata", "calcutta": "Kolkata", "howrah": "Howrah", "siliguri": "Siliguri",
    "pune": "Pune", "nagpur": "Nagpur", "nashik": "Nashik", "aurangabad": "Chhatrapati Sambhajinagar",
    "ahmedabad": "Ahmedabad", "surat": "Surat", "vadodara": "Vadodara", "rajkot": "Rajkot", "gandhinagar": "Gandhinagar",
    "jaipur": "Jaipur", "jodhpur": "Jodhpur", "udaipur": "Udaipur", "kota": "Kota", "ajmer": "Ajmer",
    "lucknow": "Lucknow", "kanpur": "Kanpur", "varanasi": "Varanasi", "agra": "Agra", "prayagraj": "Prayagraj", "allahabad": "Prayagraj",
    "chandigarh": "Chandigarh", "mohali": "Mohali", "panchkula": "Panchkula", "ludhiana": "Ludhiana", "amritsar": "Amritsar", "jalandhar": "Jalandhar",
    "bhopal": "Bhopal", "indore": "Indore", "gwalior": "Gwalior", "jabalpur": "Jabalpur",
    "patna": "Patna", "ranchi": "Ranchi", "jamshedpur": "Jamshedpur", "dhanbad": "Dhanbad",
    "bhubaneswar": "Bhubaneswar", "cuttack": "Cuttack", "puri": "Puri", "rourkela": "Rourkela",
    "guwahati": "Guwahati", "shillong": "Shillong", "dehradun": "Dehradun", "haridwar": "Haridwar",
    "kochi": "Kochi", "cochin": "Kochi", "thiruvananthapuram": "Thiruvananthapuram", "trivandrum": "Thiruvananthapuram", "kozhikode": "Kozhikode",
    "visakhapatnam": "Visakhapatnam", "vizag": "Visakhapatnam", "vijayawada": "Vijayawada", "guntur": "Guntur", "tirupati": "Tirupati",
    "raipur": "Raipur", "bhilai": "Bhilai", "bilaspur": "Bilaspur",
    "shimla": "Shimla", "jammu": "Jammu", "srinagar": "Srinagar", "panaji": "Panaji", "margao": "Margao",
    # Major Global Hubs
    "new york": "New York", "san francisco": "San Francisco", "seattle": "Seattle", "los angeles": "Los Angeles",
    "chicago": "Chicago", "austin": "Austin", "boston": "Boston", "london": "London", "toronto": "Toronto",
    "vancouver": "Vancouver", "sydney": "Sydney", "melbourne": "Melbourne", "berlin": "Berlin",
    "paris": "Paris", "singapore": "Singapore", "dubai": "Dubai", "tokyo": "Tokyo"
}

# Universal, comprehensive retail taxonomy with industry-standard classifications
DEFAULT_TAXONOMY_RULES: List[Tuple[str, str, List[str]]] = [
    # 1. Utilities, Bills & Recharge
    (
        "Utilities & Recharges",
        "Mobile & Utility Bills",
        [
            r"mobile prepaid recharge", r"prepaid recharge", r"electricity bill", r"water bill",
            r"bill payment", r"google play recharge", r"dth recharge", r"broadband bill",
            r"cylinder", r"piped gas", r"fastag", r"insurance premium", r"loan repayment"
        ],
    ),
    # 2. Digital Services & Subscriptions
    (
        "Digital Services & Subscriptions",
        "Memberships & Subscriptions",
        [
            r"prime \(yearly membership\)", r"prime membership", r"prime video", r"prime shopping edition",
            r"audible premium", r"audible membership", r"audible gold", r"kindle unlimited",
            r"amazon pay balance", r"amazon pay gift", r"egift card", r"gift card", r"voucher",
            r"credits", r"cash-load", r"play store card", r"xbox live", r"playstation plus"
        ],
    ),
    # 3. PC Hardware & Computing
    (
        "PC Hardware & Gaming",
        "Monitors & Displays",
        [
            r"monitor", r"gaming monitor", r"ips 180hz", r"144hz", r"165hz", r"240hz",
            r"curved monitor", r"ultrawide", r"oled display", r"4k display", r"hdr monitor"
        ],
    ),
    (
        "PC Hardware & Gaming",
        "Peripherals, Keyboards & Mice",
        [
            r"mechanical keyboard", r"gaming keyboard", r"wireless mouse", r"gaming mouse",
            r"mouse pad", r"gamepad", r"controller", r"joystick", r"flight stick", r"webcam",
            r"headset", r"gaming headset", r"soundbar", r"pc speaker", r"usb microphone"
        ],
    ),
    (
        "PC Hardware & Gaming",
        "Storage, Components & Networking",
        [
            r"nvme", r"internal ssd", r"portable ssd", r"external hard drive", r"hdd",
            r"ram ddr", r"motherboard", r"graphics card", r"gpu", r"processor", r"cpu",
            r"thermal paste", r"cpu cooler", r"cooling fan", r"power supply", r"psu",
            r"displayport", r"hdmi cable", r"usb-c hub", r"docking station", r"ethernet cable",
            r"wi-fi adapter", r"wifi dongle", r"pcie"
        ],
    ),
    # 4. Mobile & Smart Devices
    (
        "Mobile & Smart Devices",
        "Phones & Tablets",
        [
            r"smartphone", r"mobile phone", r"iphone", r"galaxy", r"ipad", r"tablet",
            r"smartwatch", r"fitness band", r"smart watch", r"wearable"
        ],
    ),
    (
        "Mobile & Smart Devices",
        "Cases & Mobile Accessories",
        [
            r"screen protector", r"tempered glass", r"back cover", r"phone case", r"flip cover",
            r"charging cable", r"type c cable", r"lightning cable", r"fast charger", r"power bank",
            r"car mount", r"mobile stand", r"stylus", r"apple pencil"
        ],
    ),
    # 5. Electronics & Maker
    (
        "DIY Electronics & Maker",
        "Modules, Prototyping & Batteries",
        [
            r"arduino", r"raspberry pi", r"esp32", r"microcontroller", r"breadboard",
            r"jumper wire", r"multimeter", r"soldering iron", r"solder wire", r"resistor",
            r"capacitor", r"sensor module", r"relay module", r"dc motor", r"servo",
            r"lithium battery", r"18650", r"lipo battery", r"rechargeable battery", r"tp4056",
            r"step-up", r"step-down", r"boost converter", r"buck converter", r"power supply module",
            r"voltage regulator", r"pcb board"
        ],
    ),
    # 6. Smart Home & Networking
    (
        "Smart Home & Networking",
        "Routers & Smart Home",
        [
            r"wi-fi router", r"mesh router", r"range extender", r"tp-link", r"netgear",
            r"smart plug", r"smart bulb", r"alexa", r"echo dot", r"echo show", r"fire tv",
            r"streaming stick", r"cctv", r"security camera", r"smart switch"
        ],
    ),
    # 7. Appliances & Utilities
    (
        "Appliances & Utilities",
        "Home Appliances & Climate",
        [
            r"water heater", r"geyser", r"ceiling fan", r"bldc fan", r"exhaust fan",
            r"voltage stabilizer", r"vacuum cleaner", r"air purifier", r"water purifier",
            r"iron box", r"washing machine", r"refrigerator", r"microwave oven", r"induction cooktop",
            r"room heater", r"air conditioner", r"water filter"
        ],
    ),
    # 8. Home & Office Furniture
    (
        "Home & Office Furniture",
        "Furniture, Desks & Storage",
        [
            r"office chair", r"ergonomic chair", r"study desk", r"computer table", r"office desk",
            r"wardrobe", r"closet", r"bookshelf", r"storage organizer", r"shoe rack",
            r"cable management", r"bedside table", r"wall clock", r"curtains", r"mattress",
            r"cushion", r"pillow", r"bedsheet", r"blanket", r"bean bag"
        ],
    ),
    # 9. Kitchen & Dining
    (
        "Kitchen & Dining",
        "Cookware, Cutlery & Storage",
        [
            r"cookware", r"frying pan", r"frypan", r"kadhai", r"saucepan", r"pressure cooker",
            r"casserole", r"chopping board", r"chef knife", r"cutlery", r"water bottle",
            r"flask", r"lunch box", r"glass container", r"kitchen scale", r"spatula",
            r"mixing bowl", r"toaster", r"coffee maker", r"electric kettle", r"blender"
        ],
    ),
    # 10. Apparel & Fashion
    (
        "Apparel & Fashion",
        "Clothing & Accessories",
        [
            r"t-shirt", r"shirt", r"trousers", r"jeans", r"chinos", r"jacket", r"hoodie",
            r"sweatshirt", r"sweater", r"kurta", r"dhoti", r"saree", r"lehenga", r"dress",
            r"shorts", r"track pants", r"innerwear", r"briefs", r"boxers", r"socks",
            r"formal shoes", r"running shoes", r"sneakers", r"sandals", r"slippers", r"wallet",
            r"wrist watch", r"sunglasses", r"backpack", r"duffle bag", r"trolley bag", r"luggage"
        ],
    ),
    # 11. Personal Care & Grooming
    (
        "Personal Care & Grooming",
        "Skincare, Haircare & Grooming",
        [
            r"facewash", r"facial cleanser", r"moisturizer", r"sunscreen", r"serum",
            r"shampoo", r"conditioner", r"hair oil", r"body lotion", r"body wash", r"soap",
            r"trimmer", r"shaver", r"razor", r"perfume", r"deodorant", r"toothpaste",
            r"toothbrush", r"dental floss", r"bath towel", r"hand wash"
        ],
    ),
    # 12. Books & Media
    (
        "Books & Media",
        "Books & Literature",
        [
            r"paperback", r"hardcover", r"novel", r"textbook", r"biography", r"fiction",
            r"non-fiction", r"manga", r"comic", r"poetry", r"handbook", r"guide book",
            r"board book", r"dictionary", r"encyclopedia", r"audiobook"
        ],
    ),
    # 13. Health, Fitness & Sports
    (
        "Health, Fitness & Sports",
        "Fitness Equipment & Supplements",
        [
            r"whey protein", r"creatine", r"multivitamin", r"omega 3", r"fish oil",
            r"gym gloves", r"resistance band", r"dumbbell", r"yoga mat", r"skipping rope",
            r"badminton", r"cricket bat", r"football", r"bicycle", r"cycling helmet"
        ],
    ),
    # 14. Automotive & Tools
    (
        "Automotive & Safety",
        "Riding Gear, Car Care & Tools",
        [
            r"helmet", r"riding gloves", r"car wash", r"microfiber cloth", r"tire inflator",
            r"air blower", r"drill machine", r"screwdriver", r"tool kit", r"socket set",
            r"anti-slip tape", r"dash cam", r"car charger", r"car air freshener"
        ],
    ),
    # 15. Groceries & Gourmet Food
    (
        "Food & Groceries",
        "Pantry, Snacks & Beverages",
        [
            r"green tea", r"coffee powder", r"coffee beans", r"almonds", r"cashews",
            r"walnuts", r"raisins", r"dry fruits", r"dark chocolate", r"biscuit", r"cookies",
            r"snack", r"chips", r"noodles", r"pasta", r"olive oil", r"peanut butter", r"spices"
        ],
    ),
    # 16. Toys, Baby & Kids
    (
        "Toys, Baby & Kids",
        "Baby Care & Toys",
        [
            r"diapers", r"baby wipes", r"baby lotion", r"feeding bottle", r"stroller",
            r"building blocks", r"lego", r"board game", r"puzzle", r"action figure",
            r"soft toy", r"rc car", r"educational toy"
        ],
    ),
]


def load_taxonomy(custom_path: Optional[Path] = None) -> List[Tuple[str, str, List[str]]]:
    """Load taxonomy rules, optionally merging custom user taxonomy from JSON or YAML."""
    taxonomy_file = custom_path or (WORKSPACE_DIR / "taxonomy.json")
    if taxonomy_file.exists():
        try:
            with open(taxonomy_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                custom_rules = []
                for entry in data:
                    cat = entry.get("category", "General Merchandise")
                    subcat = entry.get("subcategory", "General")
                    patterns = entry.get("patterns", [])
                    if patterns:
                        custom_rules.append((cat, subcat, patterns))
                if custom_rules:
                    logger.info(f"Loaded {len(custom_rules)} custom taxonomy rules from {taxonomy_file}")
                    # Prepend custom rules so user rules have precedence
                    return custom_rules + DEFAULT_TAXONOMY_RULES
        except Exception as e:
            logger.warning(f"Could not load custom taxonomy from {taxonomy_file}: {e}")
    return DEFAULT_TAXONOMY_RULES


# Active taxonomy rules (ready for runtime evaluation)
TAXONOMY_RULES = load_taxonomy()
