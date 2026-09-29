"""
Unit tests for Site Availability Uptime SLA and Emergency Outage triggers.
"""
import unittest
import os
from database.seed_data import seed_all_data
from modules.module3_site_ops.uptime_monitor import UptimeMonitor
from config.settings import OperationalThresholds

class TestUptimeSLA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "database/test_uptime.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        seed_all_data(cls.test_db)
        cls.monitor = UptimeMonitor(db_path=cls.test_db)
        cls.thresholds = OperationalThresholds()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_site_uptime_sla_threshold(self):
        summary = self.monitor.get_uptime_summary()
        self.assertGreaterEqual(summary["average_uptime"], self.thresholds.SITE_AVAILABILITY_MIN_PERCENT)
        self.assertTrue(summary["sla_compliant"])

    def test_emergency_outage_check(self):
        # We have an unresolved incident in seed data with duration 27 mins, but emergency_alert_sent is 1.
        # Let's verify active incidents query
        df_inc = self.monitor.get_active_incidents()
        self.assertFalse(df_inc.empty)
        # Verify emergency check runs safely
        dispatched = self.monitor.trigger_emergency_check()
        self.assertIsInstance(dispatched, list)

if __name__ == '__main__':
    unittest.main()
