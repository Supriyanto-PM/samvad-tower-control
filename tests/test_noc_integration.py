"""
Unit tests for Applied Energy NOC Integration Service.
Strictly enterprise, typography-focused, icon-free testing.
"""

import unittest
from unittest.mock import patch, MagicMock
from services.noc_integration_service import NocIntegrationService


class TestNocIntegrationService(unittest.TestCase):
    def setUp(self):
        self.service = NocIntegrationService()
        self.service.seed_initial_baseline_if_empty()

    def tearDown(self):
        self.service._record_sync_status(
            status="CONNECTED",
            site_count=6,
            alarm_count=1,
            uptime=100.0,
            error=None
        )

    def test_schema_and_baseline_seeding(self):
        status = self.service.get_sync_status()
        self.assertIsNotNone(status)
        self.assertEqual(status["portal_url"], "https://telkomceltl.appliedenergynoc.com")
        self.assertEqual(status["username"], "supriyanto")
        self.assertIn(status["status"], ["CONNECTED", "INITIALIZING", "FAILED", "ERROR"])

    def test_get_cached_sites(self):
        sites = self.service.get_cached_sites()
        self.assertGreaterEqual(len(sites), 2)
        site_ids = [s["site_id"] for s in sites]
        self.assertIn("BAU001", site_ids)
        self.assertIn("LAT001", site_ids)

    def test_get_cached_site_detail(self):
        detail = self.service.get_cached_site_detail("LAT001")
        self.assertIsNotNone(detail)
        self.assertEqual(detail["site_id"], "LAT001")
        self.assertEqual(detail["district"], "Lautem")
        self.assertIn("parsed_raw", detail)

    def test_get_cached_alarms(self):
        alarms = self.service.get_cached_alarms()
        self.assertIsInstance(alarms, list)
        if alarms:
            self.assertIn("alarm_name", alarms[0])
            self.assertIn("severity", alarms[0])

    @patch("requests.Session")
    def test_authenticate_success(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_r_chk = MagicMock()
        mock_r_chk.status_code = 200
        mock_r_chk.text = "true"

        mock_r_login = MagicMock()
        mock_r_login.status_code = 200
        mock_r_login.text = "4"

        mock_session.post.side_effect = [mock_r_chk, mock_r_login]
        mock_session.cookies.get_dict.return_value = {
            ".ASPXAUTH": "mock_auth_ticket_12345",
            "ASP.NET_SessionId": "mock_sess_abc"
        }

        ok, sess, meta = self.service.authenticate("supriyanto", "vmFz)AonLJ")
        self.assertTrue(ok)
        self.assertIsNotNone(sess)
        self.assertEqual(meta["username"], "supriyanto")
        self.assertEqual(meta["session_id"], "mock_sess_abc")

    @patch("requests.Session")
    def test_authenticate_failure(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_r_chk = MagicMock()
        mock_r_chk.status_code = 200
        mock_r_chk.text = "false"

        mock_session.post.return_value = mock_r_chk

        ok, sess, meta = self.service.authenticate("bad_user", "bad_pass")
        self.assertFalse(ok)
        self.assertIsNone(sess)
        self.assertIn("error", meta)

    def test_offline_resilience(self):
        with patch.object(self.service, "authenticate", return_value=(False, None, {"error": "Connection timed out"})):
            result = self.service.sync_live_portal()
            self.assertFalse(result["success"])
            self.assertIn("Authentication failed", result["message"])

            # Verify cached data remains intact and queryable
            sites = self.service.get_cached_sites()
            self.assertGreaterEqual(len(sites), 2)


if __name__ == "__main__":
    unittest.main()
