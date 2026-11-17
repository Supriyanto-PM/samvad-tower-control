"""
Unit tests for Samvad Rollout Operations Governance Framework.
Tests:
1. Governed Stage Advancement (Quality Gates).
2. Blocker Escalation & Quarantine to Team Zeta.
3. Crew Reassignment & Workload Load Balancing.
4. Assigned Site Queue Prioritization.
"""
import unittest
from database.connection import get_connection, query_df
from services.rollout_operations_service import RolloutOperationsService


class TestRolloutGovernance(unittest.TestCase):
    def setUp(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM timor_sites_100 LIMIT 1")
        col_names = [d[0] for d in cur.description]
        row_vals = list(cur.fetchone())
        row_dict = dict(zip(col_names, row_vals))
        row_dict['id'] = 9999
        row_dict['no'] = 9999
        row_dict['site_id'] = 'TEST-GOV-01'
        row_dict['site_name'] = 'Test Governance Tower'
        row_dict['paas_status'] = '⚪ Staged / Delivery Ready'
        row_dict['readiness_gate'] = 'HOLD (Civil Dependency)'
        row_dict['assigned_team'] = None
        row_dict['updated_at'] = None
        row_dict['blocker_reason'] = None
        
        cols = ", ".join(row_dict.keys())
        placeholders = ", ".join(["?"] * len(row_dict))
        cur.execute(f"INSERT OR REPLACE INTO timor_sites_100 ({cols}) VALUES ({placeholders})", list(row_dict.values()))
        conn.commit()
        conn.close()

    def tearDown(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        conn.commit()
        conn.close()

    def test_next_stage_preview_sequence(self):
        next_st, next_gate, label = RolloutOperationsService.get_next_stage_preview('⚪ Staged / Delivery Ready')
        self.assertIn("Power I&C", next_st)
        self.assertIn("Ready for Installation", next_gate)

        next_st, next_gate, label = RolloutOperationsService.get_next_stage_preview('🟣 Power I&C Active')
        self.assertIn("Testing & QA", next_st)

        next_st, next_gate, label = RolloutOperationsService.get_next_stage_preview('🟡 Testing & QA')
        self.assertIn("Handover", next_st)

    def test_advance_site_stage_execution(self):
        res = RolloutOperationsService.advance_site_stage('TEST-GOV-01', operator_user="PMO Auditor")
        self.assertTrue(res.get("success"))
        self.assertIn("Power I&C", res.get("new_status"))

        df = query_df("SELECT paas_status, readiness_gate, last_updated_by FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertEqual(len(df), 1)
        self.assertIn("Power I&C", df.iloc[0]["paas_status"])
        self.assertEqual(df.iloc[0]["last_updated_by"], "PMO Auditor")

    def test_flag_site_blocker_quarantine(self):
        ok = RolloutOperationsService.flag_site_blocker(
            site_id='TEST-GOV-01',
            category='Landlord & Community Access',
            reason='Village land lease dispute under renegotiation',
            pic='Bernardo Ximenes'
        )
        self.assertTrue(ok)

        df = query_df("SELECT paas_status, readiness_gate, assigned_team, blocker_reason, last_updated_by FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertIn("Blocked", row["paas_status"])
        self.assertEqual(row["assigned_team"], "TEAM-ZETA")
        self.assertIn("Village land lease dispute", row["blocker_reason"])
        self.assertEqual(row["last_updated_by"], "Bernardo Ximenes")

    def test_reassign_site_crew_delegation(self):
        ok = RolloutOperationsService.reassign_site_crew('TEST-GOV-01', 'TEAM-GAMMA', pic_user="PMO Supervisor")
        self.assertTrue(ok)

        df = query_df("SELECT assigned_team, last_updated_by FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["assigned_team"], "TEAM-GAMMA")
        self.assertEqual(df.iloc[0]["last_updated_by"], "PMO Supervisor")

    def test_assign_site_to_team(self):
        ok = RolloutOperationsService.assign_site_to_team('TEST-GOV-01', 'TEAM-BETA', user="PMO Lead")
        self.assertTrue(ok)
        df = query_df("SELECT assigned_team, last_updated_by FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertEqual(df.iloc[0]["assigned_team"], "TEAM-BETA")
        self.assertEqual(df.iloc[0]["last_updated_by"], "PMO Lead")

    def test_update_site_lifecycle_status(self):
        ok = RolloutOperationsService.update_site_lifecycle_status('TEST-GOV-01', '🟣 Power I&C Active', user="Mateus Fernandes")
        self.assertTrue(ok)
        df = query_df("SELECT paas_status, readiness_gate, last_updated_by FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertIn("Power I&C", df.iloc[0]["paas_status"])
        self.assertIn("Ready for Installation", df.iloc[0]["readiness_gate"])
        self.assertEqual(df.iloc[0]["last_updated_by"], "Mateus Fernandes")

    def test_escalate_site_governance(self):
        # 1. Assign to team first
        RolloutOperationsService.assign_site_to_team('TEST-GOV-01', 'TEAM-ALPHA', user="PMO Lead")
        # 2. Escalate site
        ok = RolloutOperationsService.escalate_site(
            site_id='TEST-GOV-01',
            blocker_category='Extreme Terrain & Weather Access',
            blocker_note='Road cut off due to landslide',
            user='Adolfo Da Silva'
        )
        self.assertTrue(ok)
        df = query_df("SELECT paas_status, readiness_gate, assigned_team, blocker_reason, last_updated_by FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertIn("Blocked", df.iloc[0]["paas_status"])
        self.assertEqual(df.iloc[0]["readiness_gate"], "ESCALATE")
        # Remains with team
        self.assertEqual(df.iloc[0]["assigned_team"], "TEAM-ALPHA")
        self.assertIn("Extreme Terrain", df.iloc[0]["blocker_reason"])
        self.assertEqual(df.iloc[0]["last_updated_by"], "Adolfo Da Silva")

        # Verify it appears in operational summary
        op_sum = RolloutOperationsService.get_daily_operational_summary()
        esc_df = op_sum["escalated_sites_df"]
        self.assertIn("TEST-GOV-01", esc_df["site_id"].values)

    def test_drop_site_and_reactivate(self):
        # 1. Assign to team first
        RolloutOperationsService.assign_site_to_team('TEST-GOV-01', 'TEAM-BETA', user="PMO Lead")
        # 2. Drop site
        ok = RolloutOperationsService.drop_site(
            site_id='TEST-GOV-01',
            blocker_category='Landlord & Community Permit',
            drop_reason='Indefinite community dispute',
            user='Mateus Fernandes'
        )
        self.assertTrue(ok)
        df = query_df("SELECT paas_status, readiness_gate, assigned_team, blocker_reason FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertIn("Dropped", df.iloc[0]["paas_status"])
        self.assertEqual(df.iloc[0]["readiness_gate"], "DROPPED")
        self.assertTrue(df.iloc[0]["assigned_team"] is None or df.iloc[0]["assigned_team"] == "")

        # Verify it appears in dropped sites
        op_sum = RolloutOperationsService.get_daily_operational_summary()
        drp_df = op_sum["dropped_sites_df"]
        self.assertIn("TEST-GOV-01", drp_df["site_id"].values)

        # 3. Reactivate site to TEAM-GAMMA
        ok_react = RolloutOperationsService.reactivate_site('TEST-GOV-01', 'TEAM-GAMMA', user="PMO Reactivator")
        self.assertTrue(ok_react)
        df2 = query_df("SELECT paas_status, readiness_gate, assigned_team, blocker_reason FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertIn("Power I&C", df2.iloc[0]["paas_status"])
        self.assertEqual(df2.iloc[0]["assigned_team"], "TEAM-GAMMA")
        self.assertTrue(df2.iloc[0]["blocker_reason"] is None or df2.iloc[0]["blocker_reason"] == "")

    def test_dynamic_team_lifecycle(self):
        # 1. Add new field team
        ok_add, msg_add = RolloutOperationsService.add_field_team(
            team_name="Team Eta (Solar Hybrid Ops)",
            lead_name="Ronaldo Gusmao",
            specialization="Solar PV & Hybrid Rectifier I&C",
            crew_size=5,
            team_code="TEAM-ETA"
        )
        self.assertTrue(ok_add)
        self.assertIn("successfully added", msg_add)

        # 2. Verify team in get_field_teams_list
        teams = RolloutOperationsService.get_field_teams_list()
        codes = [t["team_code"] for t in teams]
        self.assertIn("TEAM-ETA", codes)

        # 3. Assign test site to TEAM-ETA
        ok_assign = RolloutOperationsService.assign_site_to_team('TEST-GOV-01', 'TEAM-ETA', user="PMO Lead")
        self.assertTrue(ok_assign)
        df = query_df("SELECT assigned_team FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertEqual(df.iloc[0]["assigned_team"], "TEAM-ETA")

        # 4. Verify operational summary includes TEAM-ETA with its assigned site
        op_sum = RolloutOperationsService.get_daily_operational_summary()
        eta_team = next((t for t in op_sum["field_teams"] if t["team_code"] == "TEAM-ETA"), None)
        self.assertIsNotNone(eta_team)
        self.assertEqual(len(eta_team["assigned_sites"]), 1)
        self.assertEqual(eta_team["assigned_sites"][0]["site_id"], "TEST-GOV-01")

        # 5. Remove TEAM-ETA with unassignment back to pool
        ok_rm, msg_rm = RolloutOperationsService.remove_field_team("TEAM-ETA")
        self.assertTrue(ok_rm)
        df_unassigned = query_df("SELECT assigned_team FROM timor_sites_100 WHERE site_id = 'TEST-GOV-01'")
        self.assertTrue(df_unassigned.iloc[0]["assigned_team"] is None or df_unassigned.iloc[0]["assigned_team"] == "")

    def test_clear_all_teams_and_build_from_scratch(self):
        """Tests removing all teams to 0, operating with 0 teams, and simulating fleet addition from zero."""
        existing_teams = query_df("SELECT * FROM paas_field_teams")
        existing_assigned = query_df("SELECT site_id, assigned_team FROM timor_sites_100 WHERE assigned_team IS NOT NULL")
        try:
            # 1. Clear all teams
            ok_clear, msg_clear = RolloutOperationsService.clear_all_field_teams(unassign_sites=True)
            self.assertTrue(ok_clear)
            self.assertIn("Successfully removed", msg_clear)

            teams_zero = RolloutOperationsService.get_field_teams_list()
            self.assertEqual(len(teams_zero), 0)

            # 2. Operational summary with 0 teams must execute without crash
            op_sum = RolloutOperationsService.get_daily_operational_summary()
            self.assertEqual(len(op_sum["field_teams"]), 0)
            self.assertEqual(op_sum["active_crews_count"], 0)

            # 3. Auto-distribute with 0 teams should return 0 safely
            allocated = RolloutOperationsService.auto_distribute_initial_baseline(limit_per_team=4)
            self.assertEqual(allocated, 0)

            # 4. Simulate adding first team from zero
            ok_new, _ = RolloutOperationsService.add_field_team(
                team_name="Simulated Team 1",
                lead_name="Carlos Test",
                specialization="DC Power & Rectifier I&C",
                crew_size=4,
                team_code="TEAM-SIM-01"
            )
            self.assertTrue(ok_new)
            teams_one = RolloutOperationsService.get_field_teams_list()
            self.assertEqual(len(teams_one), 1)

            # 5. Remove the last remaining team
            ok_rm_last, _ = RolloutOperationsService.remove_field_team("TEAM-SIM-01")
            self.assertTrue(ok_rm_last)
            self.assertEqual(len(RolloutOperationsService.get_field_teams_list()), 0)
        finally:
            # Restore previous teams and assignments if any existed
            if not existing_teams.empty:
                conn = get_connection()
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM paas_field_teams")
                    for _, r in existing_teams.iterrows():
                        cur.execute("""
                            INSERT INTO paas_field_teams (
                                team_code, team_name, lead_name, specialization, crew_size, contact_number,
                                status, created_at, updated_at, current_lat, current_lon, last_checkin_at,
                                last_checkin_site, checkin_status, battery_pct
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            r["team_code"], r["team_name"], r["lead_name"], r["specialization"],
                            r.get("crew_size", 4), r.get("contact_number"), r.get("status", "Active"),
                            r.get("created_at"), r.get("updated_at"), r.get("current_lat"),
                            r.get("current_lon"), r.get("last_checkin_at"), r.get("last_checkin_site"),
                            r.get("checkin_status"), r.get("battery_pct", 95)
                        ))
                    if not existing_assigned.empty:
                        for _, ar in existing_assigned.iterrows():
                            cur.execute("UPDATE timor_sites_100 SET assigned_team = ? WHERE site_id = ?", (ar["assigned_team"], ar["site_id"]))
                    conn.commit()
                finally:
                    conn.close()

    @classmethod
    def tearDownClass(cls):
        from database.connection import execute_write
        execute_write("DELETE FROM paas_field_teams WHERE team_code LIKE 'TEAM-SIM%' OR team_code LIKE 'TEST%' OR team_code = 'TEAM-ETA'")


if __name__ == '__main__':
    unittest.main()
