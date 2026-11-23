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
        self.assertEqual(len(self.df), 101, "Must contain exactly 101 sites as per Samvad_101_Site_Load_Final.xlsx")

    def test_electrical_load_summary(self):
        self.assertAlmostEqual(self.df["load_dc_kw"].sum(), 343.41, places=2)
        self.assertAlmostEqual(self.df["load_ac_total_kw"].sum(), 392.23, places=2)
        self.assertAlmostEqual(self.df["load_ac_kva"].sum(), 412.82, places=2)
        self.assertAlmostEqual(self.df["energy_kwh_day"].sum(), 8241.2, places=1)
        self.assertEqual(len(self.df[self.df["position"] == "OUTDOOR"]), 91)
        self.assertEqual(len(self.df[self.df["position"] == "INDOOR"]), 7)
        self.assertEqual(len(self.df[self.df["position"] == "ROOFTOP"]), 3)

    def test_resilience_gaps(self):
        no_dg = len(self.df[self.df["has_dg"] == "No DG"])
        with_dg = len(self.df[self.df["has_dg"] == "DG"])
        self.assertEqual(no_dg, 72, "Sites without DG must be 72 (71 No Genset + 1 PV)")
        self.assertEqual(with_dg, 29, "Sites with Genset must be 29")

    def test_extreme_markers(self):
        extreme_rows = self.df[self.df["is_extreme"] == 1]
        self.assertGreaterEqual(len(extreme_rows), 2, "Must flag extreme/off-grid sites")
        extreme_names = set(extreme_rows["site_name"].tolist())
        self.assertTrue({"Defause", "Ducurai"}.issubset(extreme_names))

    def test_accessible_route_distances_from_port_dili(self):
        # Atauro Island (ATU002 Hahipaan) maritime crossing
        atauro = self.df[self.df["site_id"] == "ATU002"].iloc[0]
        self.assertEqual(atauro["accessible_route_km"], 36.5)
        self.assertIn("Maritime", atauro["transport_mode"])

        # Oecusse Padiae (PAN006) ferry route
        padiae = self.df[self.df["site_id"] == "PAN006"].iloc[0]
        self.assertGreater(padiae["accessible_route_km"], 140.0)
        self.assertEqual(padiae["assigned_forward_hub"], "Forward Hub Oecusse")

        # Baucau Coast (BAU005)
        baucau = self.df[self.df["site_id"] == "BAU005"].iloc[0]
        self.assertGreater(baucau["accessible_route_km"], 80.0)
        self.assertEqual(baucau["assigned_forward_hub"], "Forward Hub Baucau")

        # Suai Loro (SUA003)
        suai = self.df[self.df["site_id"] == "SUA003"].iloc[0]
        self.assertGreater(suai["accessible_route_km"], 130.0)
        self.assertEqual(suai["assigned_forward_hub"], "Forward Hub Suai")

    def test_paas_status_breakdown(self):
        self.assertIn("paas_status", self.df.columns)
        handover = len(self.df[self.df["paas_status"] == "🟢 Handover Telkomcel"])
        testing = len(self.df[self.df["paas_status"] == "🟡 Testing & QA"])
        power = len(self.df[self.df["paas_status"] == "🟣 Power I&C Active"])
        staged = len(self.df[self.df["paas_status"].str.contains("Staged", na=False)])
        shipping = len(self.df[self.df["paas_status"] == "Shipping & Customs"])
        civil_deps = len(self.df[self.df["readiness_gate"].str.contains("Civil", na=False)])
        
        self.assertEqual(handover + testing + power + staged + shipping, 101)
        self.assertEqual(handover, 28)
        self.assertEqual(power, 22)
        self.assertEqual(testing, 16)
        self.assertEqual(staged, 26)  # 14 Dili Hub + 12 Staged awaiting Civil Plinth
        self.assertEqual(civil_deps, 12)  # 12 sites flagged with TowerCo Civil Dependency
        self.assertEqual(shipping, 9)

if __name__ == '__main__':
    unittest.main()

