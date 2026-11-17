"""
Unit tests for DataManagementService (data cleaning, resets, clean imports, and wiping).
"""

import unittest
import io
import pandas as pd
from database.connection import get_connection, query_df
from services.data_management_service import DataManagementService


class TestDataManagementService(unittest.TestCase):
    def setUp(self):
        # Ensure database is in a known test state
        DataManagementService.restore_factory_baseline()

    def test_database_summary(self):
        summary = DataManagementService.get_database_summary()
        self.assertGreaterEqual(summary["total_sites"], 100)
        self.assertIn("Telkomcel", summary["sites_by_operator"])

    def test_reset_all_site_statuses(self):
        ok, msg, affected = DataManagementService.reset_all_site_statuses(
            target_status="Shipping & Customs",
            operator="Telkomcel"
        )
        self.assertTrue(ok)
        self.assertEqual(affected, 100)

        df = query_df("SELECT DISTINCT paas_status FROM timor_sites_100 WHERE operator = 'Telkomcel'")
        self.assertEqual(list(df["paas_status"]), ["Shipping & Customs"])

    def test_clear_all_blockers(self):
        ok, msg, affected = DataManagementService.clear_all_blockers(operator="Telkomcel")
        self.assertTrue(ok)
        df = query_df("SELECT COUNT(*) as c FROM timor_sites_100 WHERE operator = 'Telkomcel' AND blocker_reason IS NOT NULL")
        self.assertEqual(df["c"].iloc[0], 0)

    def test_unassign_all_sites(self):
        ok, msg, affected = DataManagementService.unassign_all_sites(operator="Telkomcel")
        self.assertTrue(ok)
        df = query_df("SELECT COUNT(*) as c FROM timor_sites_100 WHERE operator = 'Telkomcel' AND assigned_team IS NOT NULL")
        self.assertEqual(df["c"].iloc[0], 0)

    def test_clean_import_from_csv(self):
        csv_data = """site_id,site_name,district,accessible_route_km,paas_status,operator
TEST_S01,Test Site 1,Dili,12.5,Shipping & Customs,Telkomcel
TEST_S02,Test Site 2,Baucau,120.0,Testing & QA,Telkomcel
"""
        csv_file = io.StringIO(csv_data)
        csv_file.name = "test_sites.csv"

        ok, msg, stats = DataManagementService.clean_import_from_file(
            csv_file,
            replace_mode=False,
            default_operator="Telkomcel"
        )
        self.assertTrue(ok)
        self.assertEqual(stats["inserted"], 2)

        df = query_df("SELECT site_name, accessible_route_km FROM timor_sites_100 WHERE site_id = 'TEST_S01'")
        self.assertEqual(len(df), 1)
        self.assertEqual(df["site_name"].iloc[0], "Test Site 1")
        self.assertEqual(df["accessible_route_km"].iloc[0], 12.5)

    def tearDown(self):
        # Restore factory baseline after testing
        DataManagementService.restore_factory_baseline()


if __name__ == '__main__':
    unittest.main()
