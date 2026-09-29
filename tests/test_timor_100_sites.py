"""
Unit tests for Timor-Leste 100-Site National Rollout & Operational Routing from Port Dili.
"""
import unittest
import os
from database.timor_sites_data import get_timor_100_sites_dataframe, seed_timor_100_sites, PORT_DILI_COORDS
from database.connection import query_df

class TestTimor100Sites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "database/test_timor.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        seed_timor_100_sites(cls.test_db)
        cls.df = query_df("SELECT * FROM timor_sites_100", db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_total_100_sites(self):
        self.assertEqual(len(self.df), 100, "Must contain exactly 100 sites as per Blueprint")

    def test_quadrant_breakdown(self):
        q1 = len(self.df[self.df["quadrant"] == "Q1-Critical"])
        q2 = len(self.df[self.df["quadrant"] == "Q2-High"])
        q3 = len(self.df[self.df["quadrant"] == "Q3-Modernized-Monitor"])
        q4 = len(self.df[self.df["quadrant"] == "Q4-LowPriority"])
        self.assertEqual(q1, 42, "Q1 Critical must be 42")
        self.assertEqual(q2, 14, "Q2 High must be 14")
        self.assertEqual(q3, 40, "Q3 Monitor must be 40")
        self.assertEqual(q4, 4, "Q4 LowPriority must be 4")

    def test_resilience_gaps(self):
        no_dg = len(self.df[self.df["has_dg"] == "No DG"])
        zero_bk = len(self.df[self.df["backup_hours"] == 0.0])
        self.assertEqual(no_dg, 57, "Sites without DG must be 57")
        self.assertEqual(zero_bk, 34, "Sites with 0h backup must be 34")

    def test_extreme_markers(self):
        extreme_rows = self.df[self.df["is_extreme"] == 1]
        self.assertEqual(len(extreme_rows), 4, "Must flag exactly 4 extreme sites")
        extreme_names = set(extreme_rows["site_name"].tolist())
        self.assertTrue({"LIARUKA", "Lauana", "Defause", "Ducurai"}.issubset(extreme_names))

    def test_accessible_route_distances_from_port_dili(self):
        # Atauro Island (ATU002) maritime crossing
        atauro = self.df[self.df["site_id"] == "ATU002"].iloc[0]
        self.assertEqual(atauro["accessible_route_km"], 36.5)
        self.assertIn("Maritime", atauro["transport_mode"])

        # Oecusse Lifau (PAN004) ferry route
        lifau = self.df[self.df["site_id"] == "PAN004"].iloc[0]
        self.assertGreater(lifau["accessible_route_km"], 140.0)
        self.assertEqual(lifau["assigned_forward_hub"], "Forward Hub Oecusse")

        # Baucau Gariuri (BAU008)
        gariuri = self.df[self.df["site_id"] == "BAU008"].iloc[0]
        self.assertGreater(gariuri["accessible_route_km"], 110.0)
        self.assertEqual(gariuri["assigned_forward_hub"], "Forward Hub Baucau")

        # Suai Airport (SUA006)
        suai = self.df[self.df["site_id"] == "SUA006"].iloc[0]
        self.assertGreater(suai["accessible_route_km"], 130.0)
        self.assertEqual(suai["assigned_forward_hub"], "Forward Hub Suai")

if __name__ == '__main__':
    unittest.main()
