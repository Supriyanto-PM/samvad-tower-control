"""
Unit tests for KPI Engine and 120% Performance Tier calculation.
"""
import unittest
import os
from database.connection import init_db
from database.seed_data import seed_all_data
from services.kpi_engine import KPICalculator

class TestKPIEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "database/test_pmo.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        seed_all_data(cls.test_db)
        cls.engine = KPICalculator(db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_category_a_score(self):
        cat_a = self.engine.calculate_category_a_score()
        self.assertEqual(cat_a["weight"], 0.25)
        self.assertGreaterEqual(cat_a["raw_score"], 0.0)
        self.assertLessEqual(cat_a["raw_score"], 120.0)
        self.assertGreater(cat_a["shipment_count"], 0)

    def test_category_b_score(self):
        cat_b = self.engine.calculate_category_b_score()
        self.assertEqual(cat_b["weight"], 0.25)
        self.assertLessEqual(cat_b["sga_ratio_percent"], 12.0)
        self.assertGreaterEqual(cat_b["raw_score"], 100.0)

    def test_category_c_score(self):
        cat_c = self.engine.calculate_category_c_score()
        self.assertEqual(cat_c["weight"], 0.25)
        self.assertGreaterEqual(cat_c["average_uptime_percent"], 95.0)

    def test_category_d_score(self):
        cat_d = self.engine.calculate_category_d_score()
        self.assertEqual(cat_d["weight"], 0.25)
        self.assertGreaterEqual(cat_d["raw_score"], 90.0)

    def test_overall_kpi_tier(self):
        summary = self.engine.get_overall_kpi_summary()
        self.assertIn("overall_score", summary)
        self.assertGreaterEqual(summary["overall_score"], 95.0)
        self.assertIn("tier_label", summary)
        # Verify 4 categories present
        cats = summary["categories"]
        self.assertIn("category_a", cats)
        self.assertIn("category_b", cats)
        self.assertIn("category_c", cats)
        self.assertIn("category_d", cats)

if __name__ == '__main__':
    unittest.main()
