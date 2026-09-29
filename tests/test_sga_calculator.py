"""
Unit tests for SG&A Financial Sentinel and Manpower Optimizer.
"""
import unittest
import os
from database.seed_data import seed_all_data
from modules.module2_sga.sga_calculator import SGACalculator
from modules.module2_sga.manpower_optimizer import ManpowerOptimizer

class TestSGAAndManpower(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "database/test_sga.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        seed_all_data(cls.test_db)
        cls.sga_calc = SGACalculator(db_path=cls.test_db)
        cls.manpower_opt = ManpowerOptimizer(db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_sga_ratio_below_12_percent(self):
        summary = self.sga_calc.get_expenses_summary()
        ratio = summary["sga_ratio_pct"]
        ceiling = summary["sga_ceiling_pct"]
        self.assertEqual(ceiling, 12.0)
        self.assertLess(ratio, 12.0)
        self.assertIn("GREEN", summary["status"])

    def test_manpower_audit_flags_high_utilization(self):
        df_audit = self.manpower_opt.audit_engineer_utilization()
        self.assertFalse(df_audit.empty)
        # FE-001 has 18 visits, daily cost 45m vs retainer 38m -> should recommend conversion!
        fe001 = df_audit[df_audit["engineer_id"] == "FE-001"].iloc[0]
        self.assertEqual(fe001["status_flag"], "OVER_BUDGET_DAILY")
        self.assertGreater(fe001["potential_saving_idr"], 0)
        self.assertIn("CONVERT TO RETAINER", fe001["recommendation"])

if __name__ == '__main__':
    unittest.main()
