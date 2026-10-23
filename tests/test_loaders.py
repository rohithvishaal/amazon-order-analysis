"""Unit and integration tests for data loading and analytics computation."""

import unittest
from src.analyzer import OrderAnalyzer
from src.loaders import UnifiedDataLoader, fingerprint_csv
from src.config import YOUR_ORDERS_DIR


class TestLoadersAndAnalyzer(unittest.TestCase):
    def test_fingerprinting(self):
        oh_path = YOUR_ORDERS_DIR / "Your Amazon Orders" / "Order History.csv"
        self.assertTrue(oh_path.exists())
        ftype = fingerprint_csv(oh_path)
        self.assertEqual(ftype, "order_history")

        ret_path = YOUR_ORDERS_DIR / "Your Returns & Refunds" / "Returns Status.csv"
        self.assertTrue(ret_path.exists())
        self.assertEqual(fingerprint_csv(ret_path), "returns_status")

    def test_unified_loader_execution(self):
        loader = UnifiedDataLoader()
        orders = loader.load_all()
        self.assertGreaterEqual(len(orders), 330)

        # Check sample order structure
        sample = next(iter(orders.values()))
        self.assertTrue(hasattr(sample, "order_id"))
        self.assertTrue(hasattr(sample, "total_amount"))
        self.assertTrue(len(sample.items) >= 1)

    def test_analyzer_computation(self):
        loader = UnifiedDataLoader()
        orders = list(loader.load_all().values())
        analyzer = OrderAnalyzer(orders)
        res = analyzer.compute_all()

        self.assertIn("summary", res)
        self.assertIn("yearly", res)
        self.assertIn("categories", res)
        self.assertIn("returns", res)

        kpis = res["summary"]
        self.assertGreater(kpis["grossSpend"], 250000)
        self.assertGreater(kpis["netSpend"], 200000)
        self.assertGreaterEqual(kpis["totalOrders"], 330)


if __name__ == "__main__":
    unittest.main()

