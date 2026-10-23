"""Unit tests for cleaners and utility functions."""

import unittest
from src.cleaners import (
    classify_product,
    clean_amount,
    extract_city,
    parse_carrier,
    parse_datetime_ist,
    standardize_status,
)


class TestCleaners(unittest.TestCase):
    def test_clean_amount(self):
        self.assertEqual(clean_amount("2,499"), 2499.0)
        self.assertEqual(clean_amount("'-1,800'"), -1800.0)
        self.assertEqual(clean_amount("'-23.34'"), -23.34)
        self.assertEqual(clean_amount("370.48"), 370.48)
        self.assertEqual(clean_amount("0"), 0.0)
        self.assertEqual(clean_amount("Not Available"), 0.0)
        self.assertEqual(clean_amount("Not Applicable"), 0.0)
        self.assertEqual(clean_amount(None), 0.0)
        self.assertEqual(clean_amount(float("nan")), 0.0)

    def test_parse_datetime_ist(self):
        dt = parse_datetime_ist("2021-02-03T15:21:24Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2021)
        self.assertEqual(dt.month, 2, "Month should be February")
        # In IST (UTC+5:30), 15:21Z becomes 20:51 IST
        self.assertEqual(dt.hour, 20)
        self.assertEqual(dt.minute, 51)

        dt_fallback = parse_datetime_ist("2026-10-22")
        self.assertIsNotNone(dt_fallback)
        self.assertEqual(dt_fallback.year, 2026)

    def test_extract_city(self):
        # Hyderabad & Telangana regions
        self.assertEqual(extract_city("rohith vishaal HYDERABAD TELANGANA 501510 India"), "Hyderabad")
        self.assertEqual(extract_city("rohith vishaal SECUNDERABAD TELANGANA 500061 India"), "Secunderabad")
        self.assertEqual(extract_city("Rohith vishaal BHADRACHALAM TELANGANA 507111 India"), "Bhadrachalam")
        self.assertEqual(extract_city("Rahul kumar 9-7-136/6, KHAMMAM TELANGANA 507001 India"), "Khammam")
        
        # Universal Indian metros
        self.assertEqual(extract_city("Rahul Kumar Lakven Meadows BENGALURU KARNATAKA 560036 India"), "Bengaluru")
        self.assertEqual(extract_city("Amit Sharma Flat 302, Andheri West MUMBAI MAHARASHTRA 400053 India"), "Mumbai")
        self.assertEqual(extract_city("Pooja Verma D-14, Sector 62 NOIDA UTTAR PRADESH 201301 India"), "Noida")
        self.assertEqual(extract_city("Vikas Khanna Connaught Place NEW DELHI DELHI 110001 India"), "New Delhi")
        self.assertEqual(extract_city("Priya Sen Park Street KOLKATA WEST BENGAL 700016 India"), "Kolkata")
        
        # Dynamic uncatalogued city extraction
        self.assertEqual(extract_city("Citizen Main St SHIMOGA KARNATAKA 577201 India"), "Shimoga")
        
        # International addresses
        self.assertEqual(extract_city("John Doe 123 Main St, SEATTLE, WA 98101 United States"), "Seattle")
        self.assertEqual(extract_city("Not Available"), "Not Available")
        self.assertEqual(extract_city(None), "Not Available")

    def test_parse_carrier(self):
        name, tracking = parse_carrier("ATS(260752802370)")
        self.assertEqual(name, "Amazon Transportation Services (ATS)")
        self.assertEqual(tracking, "260752802370")

        name2, tracking2 = parse_carrier("SVAFN")
        self.assertEqual(name2, "Amazon Seller Fulfilled / AFN")
        self.assertEqual(tracking2, "")

    def test_classify_product(self):
        # Universal computing & displays
        cat1, sub1 = classify_product("Lenovo 27 Inch Gaming Monitor 180Hz")
        self.assertEqual(cat1, "PC Hardware & Gaming")

        # Universal DIY & batteries
        cat2, sub2 = classify_product("2 Pcs Charging Module for 18650 Lithium Battery")
        self.assertEqual(cat2, "DIY Electronics & Maker")

        # Universal utilities & recharges
        cat3, sub3 = classify_product("Mobile Prepaid Recharge")
        self.assertEqual(cat3, "Utilities & Recharges")

        # Universal digital memberships
        cat4, sub4 = classify_product("Amazon Prime (Yearly Membership)")
        self.assertEqual(cat4, "Digital Services & Subscriptions")

        # Universal retail categories
        cat5, sub5 = classify_product("Apple iPhone 15 Pro Max 256GB Smartphone")
        self.assertEqual(cat5, "Mobile & Smart Devices")

        cat6, sub6 = classify_product("Men's Regular Fit Cotton Casual T-Shirt")
        self.assertEqual(cat6, "Apparel & Fashion")

        cat7, sub7 = classify_product("Ergonomic Mesh High Back Office Chair")
        self.assertEqual(cat7, "Home & Office Furniture")

        cat8, sub8 = classify_product("Non-Stick Induction Frying Pan Cookware")
        self.assertEqual(cat8, "Kitchen & Dining")

    def test_standardize_status(self):
        self.assertEqual(standardize_status("Closed", "Shipped"), "Delivered")
        self.assertEqual(standardize_status("Cancelled", "Not Available"), "Cancelled")
        self.assertEqual(standardize_status("Closed", returns_info={"resolution": "Refund"}), "Returned & Refunded")
        self.assertEqual(standardize_status("Closed", returns_info={"resolution": "Exchange"}), "Replaced / Exchanged")


if __name__ == "__main__":
    unittest.main()

