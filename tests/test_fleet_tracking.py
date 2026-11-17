"""
Unit tests for FleetTrackingService.
"""

import unittest
from services.fleet_tracking_service import FleetTrackingService
from database.connection import query_df


class TestFleetTrackingService(unittest.TestCase):
    def test_get_fleet_kpis(self):
        kpis = FleetTrackingService.get_fleet_kpis()
        self.assertIn("total_teams", kpis)
        self.assertGreaterEqual(kpis["total_teams"], 0)

    def test_record_team_checkin(self):
        ok, msg = FleetTrackingService.record_team_checkin(
            team_code="TEAM-ALPHA",
            site_id="TLS001",
            lat=-8.5568,
            lon=125.5736,
            status="Confirmed - On-Site Active",
            notes="Load test in progress"
        )
        self.assertTrue(ok)
        self.assertIn("verified successfully", msg)

        df = query_df("SELECT current_lat, current_lon, checkin_status FROM paas_field_teams WHERE team_code = 'TEAM-ALPHA'")
        self.assertAlmostEqual(df["current_lat"].iloc[0], -8.5568, places=4)
        self.assertAlmostEqual(df["current_lon"].iloc[0], 125.5736, places=4)
        self.assertEqual(df["checkin_status"].iloc[0], "Confirmed - On-Site Active")

    def test_generate_checkin_url(self):
        url = FleetTrackingService.generate_checkin_url("TEAM-BETA", "BAU001")
        self.assertIn("checkin=TEAM-BETA", url)
        self.assertIn("site=BAU001", url)

    def test_work_order_payload_includes_checkin_url(self):
        from services.notification_service import NotificationDispatcher
        df_s = query_df("SELECT site_id FROM timor_sites_100 LIMIT 1")
        site_id = df_s["site_id"].iloc[0] if not df_s.empty else "BAG001"
        payload = NotificationDispatcher().generate_work_order_payload(site_id, "TEAM-ALPHA")
        self.assertIn("checkin_url", payload)
        self.assertIn("checkin=TEAM-ALPHA", payload["checkin_url"])
        self.assertIn(f"site={site_id}", payload["checkin_url"])
        # Verify text includes task confirmation link and has no emoji icons
        self.assertIn("Click to start check-in", payload["message_text"])
        # Ensure no standard alert/phone emojis
        self.assertNotIn("🚨", payload["message_text"])
        self.assertNotIn("📍", payload["message_text"])
        self.assertNotIn("📱", payload["message_text"])

    def test_calculate_geofence_status_in_radius(self):
        # Coordinates 0.5 km apart with "On-Site" status
        res = FleetTrackingService.calculate_geofence_status(
            team_lat=-8.5520,
            team_lon=125.5711,
            site_lat=-8.5550,
            site_lon=125.5730,
            checkin_status="Confirmed - On-Site Active"
        )
        self.assertFalse(res["is_out_of_area"])
        self.assertEqual(res["flag_type"], "IN_SITE_RADIUS")
        self.assertIn("IN RADIUS", res["flag_label"])
        self.assertLess(res["dist_km"], 2.5)

    def test_calculate_geofence_status_out_of_radius(self):
        # Coordinates 15 km apart with "On-Site" status -> breach!
        res = FleetTrackingService.calculate_geofence_status(
            team_lat=-8.5520,
            team_lon=125.5711,
            site_lat=-8.6800,
            site_lon=125.5730,
            checkin_status="Confirmed - On-Site Active"
        )
        self.assertTrue(res["is_out_of_area"])
        self.assertEqual(res["flag_type"], "OUT_OF_SITE_RADIUS")
        self.assertIn("FLAG: OUT OF RADIUS", res["flag_label"])
        self.assertGreater(res["dist_km"], 2.5)

    def test_calculate_geofence_status_in_corridor(self):
        # En route within allowable corridor
        res = FleetTrackingService.calculate_geofence_status(
            team_lat=-8.5520,
            team_lon=125.5711,
            site_lat=-8.6500,
            site_lon=125.6000,
            checkin_status="Confirmed - En Route",
            accessible_route_km=30.0
        )
        self.assertFalse(res["is_out_of_area"])
        self.assertEqual(res["flag_type"], "IN_CORRIDOR")
        self.assertIn("IN CORRIDOR", res["flag_label"])

    def test_calculate_geofence_status_out_of_corridor(self):
        # En route far outside corridor (e.g. 120 km away)
        res = FleetTrackingService.calculate_geofence_status(
            team_lat=-8.5520,
            team_lon=125.5711,
            site_lat=-9.3000,
            site_lon=126.5000,
            checkin_status="Confirmed - En Route",
            accessible_route_km=25.0
        )
        self.assertTrue(res["is_out_of_area"])
        self.assertEqual(res["flag_type"], "OUT_OF_AREA")
        self.assertIn("FLAG: OUT OF AREA", res["flag_label"])

    def test_auto_initialize_assigned_team_hub(self):
        # Create a team without GPS
        from database.connection import execute_write
        execute_write("INSERT OR REPLACE INTO paas_field_teams (team_code, team_name, lead_name, specialization, current_lat, current_lon) VALUES ('TEAM-TESTHUB', 'Test Crew', 'Lead PIC', 'Civil', NULL, NULL)")
        FleetTrackingService.auto_initialize_assigned_team_hub("TEAM-TESTHUB", "DAX001")
        df = query_df("SELECT current_lat, current_lon, checkin_status FROM paas_field_teams WHERE team_code = 'TEAM-TESTHUB'")
        self.assertIsNotNone(df["current_lat"].iloc[0])
        self.assertAlmostEqual(df["current_lat"].iloc[0], -8.5520, places=3)
        self.assertIn("Hub", df["checkin_status"].iloc[0])

    def test_multi_operator_assignment_places_team_at_regional_hub(self):
        from services.rollout_operations_service import RolloutOperationsService
        from database.connection import execute_write
        execute_write("UPDATE paas_field_teams SET current_lat = NULL, current_lon = NULL WHERE team_code = 'TEAM-ALPHA'")
        # Assign an XLSmart site to a team
        df_xls = query_df("SELECT site_id FROM timor_sites_100 WHERE operator = 'XLSmart' LIMIT 1")
        if not df_xls.empty:
            xls_site = df_xls["site_id"].iloc[0]
            ok = RolloutOperationsService.assign_site_to_team(xls_site, "TEAM-ALPHA", user="PMO Radar Test")
            self.assertTrue(ok)
            df_fleet = FleetTrackingService.get_fleet_tracking_dataframe()
            alpha_row = df_fleet[df_fleet["team_code"] == "TEAM-ALPHA"].iloc[0]
            # Must be placed at Pelabuhan Belawan (lat ~3.7845, lon ~98.6917)
            self.assertAlmostEqual(alpha_row["current_lat"], 3.7845, places=2)
            self.assertAlmostEqual(alpha_row["current_lon"], 98.6917, places=2)
            self.assertEqual(alpha_row["site_operator"], "XLSmart")
            self.assertEqual(alpha_row["assigned_site_id"], xls_site)

    def test_smartphone_live_gps_permission_checkin_updates_radar(self):
        # Simulate smartphone GPS check-in (technician clicking allow location on mobile)
        ok, msg = FleetTrackingService.record_team_checkin(
            team_code="TEAM-ALPHA",
            site_id="XLS001",
            lat=3.5952,
            lon=98.6722,
            status="Confirmed - En Route",
            accuracy_m=5.0,
            user_agent="Mobile Safari WhatsApp Geolocation"
        )
        self.assertTrue(ok)
        df_fleet = FleetTrackingService.get_fleet_tracking_dataframe()
        alpha_row = df_fleet[df_fleet["team_code"] == "TEAM-ALPHA"].iloc[0]
        self.assertAlmostEqual(alpha_row["current_lat"], 3.5952, places=4)
        self.assertAlmostEqual(alpha_row["current_lon"], 98.6722, places=4)
        self.assertEqual(alpha_row["checkin_status"], "Confirmed - En Route")

    def test_get_fleet_kpis_includes_out_of_area(self):
        kpis = FleetTrackingService.get_fleet_kpis()
        self.assertIn("out_of_area_count", kpis)

    def test_parse_location_string(self):
        # Google Maps URL
        coords = FleetTrackingService.parse_location_string("https://maps.google.com/?q=-7.2575,112.7521")
        self.assertIsNotNone(coords)
        self.assertAlmostEqual(coords[0], -7.2575, places=4)
        self.assertAlmostEqual(coords[1], 112.7521, places=4)

        # Standard lat, lon string
        coords2 = FleetTrackingService.parse_location_string("-6.2088, 106.8456")
        self.assertIsNotNone(coords2)
        self.assertAlmostEqual(coords2[0], -6.2088, places=4)
        self.assertAlmostEqual(coords2[1], 106.8456, places=4)

        # Invalid string
        self.assertIsNone(FleetTrackingService.parse_location_string("invalid text without coords"))

    def test_assignment_auth_token_generation_and_verification(self):
        token = FleetTrackingService.generate_assignment_auth_token("TEAM-SEC01", "SITE-A01", "+628123456789")
        self.assertEqual(len(token), 8)
        self.assertTrue(FleetTrackingService.verify_assignment_auth_token("TEAM-SEC01", "SITE-A01", token, "+628123456789"))
        # Invalid token or altered parameters must fail
        self.assertFalse(FleetTrackingService.verify_assignment_auth_token("TEAM-SEC01", "SITE-A01", "invalid1", "+628123456789"))
        self.assertFalse(FleetTrackingService.verify_assignment_auth_token("TEAM-SEC02", "SITE-A01", token, "+628123456789"))

    def test_device_binding_and_anti_share_lock(self):
        # 1. Reset any prior test bindings
        FleetTrackingService.reset_device_binding("TEAM-BIND01", "SITE-TEST01")

        # 2. First device connects -> Binds successfully
        is_ok, reason, info = FleetTrackingService.verify_or_bind_device(
            team_code="TEAM-BIND01",
            site_id="SITE-TEST01",
            device_id="device_uuid_pic_primary_12345"
        )
        self.assertTrue(is_ok)
        self.assertEqual(reason, "DEVICE_BOUND")
        self.assertTrue(info.get("is_authorized"))

        # 3. Same primary device transmits again -> Authorized
        is_ok2, reason2, info2 = FleetTrackingService.verify_or_bind_device(
            team_code="TEAM-BIND01",
            site_id="SITE-TEST01",
            device_id="device_uuid_pic_primary_12345"
        )
        self.assertTrue(is_ok2)
        self.assertEqual(reason2, "AUTHORIZED_DEVICE")

        # 4. Link forwarded to unauthorized phone B -> Blocked!
        is_ok3, reason3, info3 = FleetTrackingService.verify_or_bind_device(
            team_code="TEAM-BIND01",
            site_id="SITE-TEST01",
            device_id="device_uuid_stranger_forwarded_99999"
        )
        self.assertFalse(is_ok3)
        self.assertEqual(reason3, "DEVICE_MISMATCH")
        self.assertIn("ACCESS DENIED", info3.get("message", ""))

        # 5. Verify security audit log recorded
        df_audit = query_df("SELECT * FROM notification_audit_logs WHERE recipient = 'TEAM-BIND01' AND message_type = 'UNAUTHORIZED_SHARE_BLOCKED'")
        self.assertFalse(df_audit.empty)

        # 6. PMO Controller clears device lock -> New device authorized
        reset_ok = FleetTrackingService.reset_device_binding("TEAM-BIND01", "SITE-TEST01")
        self.assertTrue(reset_ok)

        # 7. Replacement device connects -> Binds as new authorized device
        is_ok4, reason4, _ = FleetTrackingService.verify_or_bind_device(
            team_code="TEAM-BIND01",
            site_id="SITE-TEST01",
            device_id="device_uuid_replacement_device_77777"
        )
        self.assertTrue(is_ok4)
        self.assertEqual(reason4, "DEVICE_BOUND")

    def test_reverse_geocode_and_caching(self):
        # Coordinates in Cileunyi / Bandung
        addr = FleetTrackingService.reverse_geocode(-6.91958, 107.74649)
        self.assertIsNotNone(addr)
        self.assertTrue(len(addr) > 5)

        # Second lookup must return exact cached address
        cached_addr = FleetTrackingService.reverse_geocode(-6.91958, 107.74649)
        self.assertEqual(addr, cached_addr)

        # Test invalid or missing coordinates
        self.assertEqual(FleetTrackingService.reverse_geocode(None, None), "No GPS fix")

    def test_calculate_road_routing(self):
        # 1. On-site coordinates (< 200m apart)
        res_site = FleetTrackingService.calculate_road_routing(-8.5520, 125.5711, -8.5525, 125.5715)
        self.assertEqual(res_site["route_source"], "ON_SITE")
        self.assertIn("At Site", res_site["eta_text"])
        self.assertLess(res_site["road_km"], 0.2)

        # 2. Road distance and ETA calculation
        res_route = FleetTrackingService.calculate_road_routing(-8.5520, 125.5711, -8.7230, 125.4310)
        self.assertIsNotNone(res_route["road_km"])
        self.assertGreater(res_route["road_km"], 0)
        self.assertIsNotNone(res_route["eta_text"])
        self.assertIn("route_source", res_route)

        # 3. Verify caching returns identical result instantly
        res_cached = FleetTrackingService.calculate_road_routing(-8.5520, 125.5711, -8.7230, 125.4310)
        self.assertEqual(res_route["road_km"], res_cached["road_km"])
        self.assertEqual(res_route["eta_text"], res_cached["eta_text"])

        # 4. Verify dataframe contains road routing fields
        df = FleetTrackingService.get_fleet_tracking_dataframe()
        self.assertIn("road_dist_km", df.columns)
        self.assertIn("air_dist_km", df.columns)
        self.assertIn("eta_to_site", df.columns)

    def test_effective_host_reads_tunnel_url(self):
        host = FleetTrackingService.get_effective_host()
        self.assertTrue(host.startswith("http"))
        self.assertIn("trycloudflare.com", host)

    def test_mobile_checkin_html_ui_specs(self):
        with open("services/mobile_checkin_handler.py", "r") as f:
            content = f.read()
        # Verify perm-banner is removed
        self.assertNotIn("perm-banner", content)
        # Verify black button TASK COMPLETED (TRACKING ENDED) is removed
        self.assertNotIn("TASK COMPLETED (TRACKING ENDED)", content)
        # Verify continuous telemetry and new button text
        self.assertIn("LIVE GPS TELEMETRY ACTIVE", content)
        self.assertIn("SESSION CONCLUDED BY PMO CONTROLLER", content)
        # Verify no emojis
        for emoji in ["🚨", "📍", "📱", "✅", "⚠️", "❌"]:
            self.assertNotIn(emoji, content)

    @classmethod
    def tearDownClass(cls):
        from database.connection import execute_write
        execute_write("DELETE FROM paas_field_teams WHERE team_code LIKE 'TEAM-TEST%' OR team_code IN ('TEAM-ALPHA', 'TEAM-BETA', 'TEAM-GAMMA', 'TEAM-BIND01', 'TEAM-SEC01', 'TEAM-SEC02')")
        execute_write("UPDATE timor_sites_100 SET assigned_team = NULL WHERE site_id LIKE 'TEST%' OR assigned_team LIKE 'TEAM-TEST%' OR assigned_team IN ('TEAM-ALPHA', 'TEAM-BETA', 'TEAM-GAMMA')")
        execute_write("DELETE FROM assignment_device_bindings WHERE team_code LIKE 'TEAM-TEST%' OR team_code IN ('TEAM-ALPHA', 'TEAM-BETA', 'TEAM-GAMMA', 'TEAM-BIND01', 'TEAM-SEC01', 'TEAM-SEC02')")


if __name__ == "__main__":
    unittest.main()

