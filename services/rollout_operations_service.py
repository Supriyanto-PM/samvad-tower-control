"""
Rollout Operations Service for Samvad PMO Command Center (PMO-CC).
Provides real-time business logic for:
1. Active Field Teams Deployment Board (Crews, PIC, Site Assignment, Activity, Status).
2. Daily Checkpoints & Run-Rate Velocity (Today's Targets vs Actual).
3. Root-Cause Blocker & Escalation Action Matrix.
4. 5-Stage Micro-Progress Workflow Pipeline.
5. Two-Way Synchronization with Main Dashboard and SQLite.
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from datetime import datetime, date
from database.connection import get_connection, query_df, execute_write


class RolloutOperationsService:
    @staticmethod
    def get_daily_operational_summary(selected_operator: str = "All") -> Dict[str, Any]:
        """
        Computes dynamic daily operational metrics and field team status
        integrated with timor_sites_100 in SQLite.
        """
        df_all = query_df("SELECT * FROM timor_sites_100 ORDER BY accessible_route_km ASC")
        if df_all.empty:
            return {}

        if selected_operator != "All":
            df_view = df_all[df_all["operator"] == selected_operator].copy()
        else:
            df_view = df_all.copy()

        total_sites = len(df_view)
        c_handover = len(df_view[df_view["paas_status"].str.contains("Handover", na=False)])
        c_testing = len(df_view[df_view["paas_status"].str.contains("Testing", na=False)])
        c_power = len(df_view[df_view["paas_status"].str.contains("Power", na=False)])
        c_civil = len(df_view[df_view["paas_status"].str.contains("Civil", na=False)])
        c_civil_dep = len(df_view[df_view["readiness_gate"].str.contains("Civil", na=False) | df_view["blocker_reason"].str.contains("Civil", na=False)])
        c_staged = len(df_view[df_view["paas_status"].str.contains("Staged", na=False)])
        c_shipping = len(df_view[df_view["paas_status"].str.contains("Shipping", na=False)])
        c_blocked = len(df_view[df_view["paas_status"].str.contains("Blocked|Issue", na=False)])

        # 1. Root-Cause Blocker & Escalation List
        df_blocked = df_view[
            df_view["paas_status"].str.contains("Blocked|Issue", na=False) |
            df_view["readiness_gate"].str.contains("HOLD|ESCALATE", na=False)
        ].copy()

        blockers: List[Dict[str, Any]] = []
        for _, row in df_blocked.iterrows():
            sid = row["site_id"]
            sname = row["site_name"]
            st = row["paas_status"]
            gate = row["readiness_gate"]
            dist = row["district"]
            op = row.get("operator", "Telkomcel")

            # Root cause categorization
            custom_blocker = row.get("blocker_reason")
            if custom_blocker and pd.notnull(custom_blocker):
                bl_str = str(custom_blocker)
                category = bl_str.split("]")[0].replace("[", "").strip() if "]" in bl_str else "Field Impediment"
                action = bl_str.split("]")[1].strip() if "]" in bl_str else bl_str
                impact = "Deployment Quarantined • Escalation Active"
                pic = row.get("last_updated_by") or "Bernardo Ximenes (Resolution PIC)"
                target_date = "Within 48h SLA"
                severity = "CRITICAL"
            elif "Blocked" in str(st):
                category = "Landlord & Community Access"
                impact = "High Risk • Deployment Paused"
                action = "Renegotiate land lease agreement and reroute grounding cable pathway with local village administration"
                pic = "Adolfo Da Silva (Field Acquisition)"
                target_date = "Tomorrow, 17:00 WIB"
                severity = "CRITICAL"
            elif "ESCALATE" in str(gate):
                if row.get("is_extreme", 0) == 1:
                    category = "Extreme Terrain & Weather Risk"
                    impact = "Logistics Access Blocked"
                    action = "Mobilize 4x4 heavy transport fleet and winch towing cable for steep mountain incline"
                    pic = "Carlos Da Costa (Logistics Lead)"
                    target_date = "3 Business Days"
                    severity = "HIGH"
                else:
                    category = "Grid / Utility Interconnection"
                    impact = "Power Commissioning Delay"
                    action = "Escalate to local power utility (EDTL) for distribution transformer tap connection"
                    pic = "Mateus Fernandes (Power PIC)"
                    target_date = "2 Business Days"
                    severity = "MEDIUM"
            else:
                category = "Civil & Tower Dependency (Plinth Not Ready)"
                impact = "Awaiting TowerCo Plinth Readiness"
                action = "Awaiting TowerCo / MNO plinth foundation handover before mounting equipment"
                pic = "Gaspar Soares (Site Auditor)"
                target_date = "4 Business Days"
                severity = "SCHEDULED"

            blockers.append({
                "site_id": sid,
                "site_name": sname,
                "operator": op,
                "district": dist,
                "paas_status": st,
                "readiness_gate": gate,
                "category": category,
                "impact": impact,
                "mitigation_action": action,
                "pic": pic,
                "target_date": target_date,
                "severity": severity
            })

        # 2. Dynamic Field Teams & Multi-Site Assignment Queues
        def build_assigned_sites(df_primary, fallback_df, team_code, limit=4, strict_explicit=False):
            sites_list = []
            selected_df = pd.DataFrame()

            # Priority 1: Sites explicitly assigned to this team in SQLite
            if not fallback_df.empty and "assigned_team" in fallback_df.columns:
                explicit_sites = fallback_df[fallback_df["assigned_team"] == team_code].copy()
                if not explicit_sites.empty:
                    selected_df = explicit_sites.copy()

            if not strict_explicit:
                # Priority 2: Domain-matched sites (for initial baseline simulation if unassigned)
                if len(selected_df) < limit and not df_primary.empty:
                    existing_ids = set(selected_df["site_id"]) if not selected_df.empty else set()
                    domain_extras = df_primary[~df_primary["site_id"].isin(existing_ids)]
                    if not domain_extras.empty:
                        needed = limit - len(selected_df)
                        selected_df = pd.concat([selected_df, domain_extras.head(needed)]) if not selected_df.empty else domain_extras.head(needed)

                # Priority 3: Fallback from general portfolio
                if len(selected_df) < limit and not fallback_df.empty:
                    existing_ids = set(selected_df["site_id"]) if not selected_df.empty else set()
                    extras = fallback_df[~fallback_df["site_id"].isin(existing_ids)]
                    if not extras.empty:
                        needed = limit - len(selected_df)
                        selected_df = pd.concat([selected_df, extras.head(needed)]) if not selected_df.empty else extras.head(needed)
            
            for _, r in selected_df.iterrows():
                sid = r["site_id"]
                sname = r["site_name"]
                dist = r["district"]
                st = r["paas_status"]
                gate = r["readiness_gate"]
                km = float(r["accessible_route_km"]) if pd.notnull(r.get("accessible_route_km")) else 15.0
                tt = r.get("est_travel_time", "1h 30m")
                mode = r.get("transport_mode", "4x4 Overland Truck")
                rect = r.get("rectifier", "Eltek 48V/3000W Hybrid")
                
                # Contextual Action Plan per Site
                if team_code == "TEAM-ALPHA":
                    act = f"Install DC power panel, rectifier shelf mounting, and internal cabinet DC cabling for {rect} at {sname}."
                elif team_code == "TEAM-BETA":
                    act = f"Commissioning {rect} modules, automatic ATS transfer switch integration, and AC distribution wiring at {sname}."
                elif team_code == "TEAM-GAMMA":
                    act = f"Install 48V/200Ah LiFePO4 battery string, calibrate BMS telemetry bus to NOC, and balance DC circuit breakers at {sname}."
                elif team_code == "TEAM-DELTA":
                    act = f"Execute 24-hour utility blackout simulation test, calibrate RMS telemetry to Control Tower, and complete joint ATP BAST sign-off at {sname}."
                elif team_code == "TEAM-EPSILON":
                    act = f"Direct convoy haulage of hardware from Port to site coordinates ({km:.1f} km via {mode}), and sign MOS delivery receipt at {sname}."
                elif team_code == "TEAM-ZETA":
                    custom_note = r.get("blocker_reason") or r.get("notes") or "Landlord rights-of-way and community re-permitting"
                    act = f"Resolve active site blocker ({custom_note}), coordinate village clearance, and release Gate {gate} within 48h SLA."
                else:
                    act = f"Field power I&C installation, battery integration, and QA sign-off for {rect} at {sname}."
                
                sites_list.append({
                    "site_id": sid,
                    "site_name": sname,
                    "district": dist,
                    "paas_status": st,
                    "readiness_gate": gate,
                    "accessible_route_km": km,
                    "est_travel_time": tt,
                    "transport_mode": mode,
                    "rectifier": rect,
                    "action_plan": act,
                    "assigned_team": r.get("assigned_team") if pd.notnull(r.get("assigned_team")) else team_code,
                    "updated_at": r.get("updated_at") if pd.notnull(r.get("updated_at")) else "Active",
                    "last_updated_by": r.get("last_updated_by") if pd.notnull(r.get("last_updated_by")) else "PMO Lead",
                    "blocker_reason": r.get("blocker_reason") if pd.notnull(r.get("blocker_reason")) else None,
                    "lat": float(r["lat"]) if pd.notnull(r.get("lat")) else None,
                    "lon": float(r["lon"]) if pd.notnull(r.get("lon")) else None,
                    "operator": r.get("operator", "Telkomcel")
                })
            return sites_list

        active_power_sites = df_view[df_view["paas_status"].str.contains("Power", na=False)]
        active_testing_sites = df_view[df_view["paas_status"].str.contains("Testing", na=False)]
        active_blocked_sites = df_view[df_view["paas_status"].str.contains("Blocked", na=False)]
        active_shipping_sites = df_view[df_view["paas_status"].str.contains("Shipping|Staged", na=False)]

        one_third = len(active_power_sites) // 3
        p_alpha = active_power_sites.iloc[:max(1, one_third)] if not active_power_sites.empty else active_power_sites
        p_beta = active_power_sites.iloc[max(1, one_third):max(2, 2 * one_third)] if len(active_power_sites) > 1 else active_power_sites
        p_gamma = active_power_sites.iloc[max(2, 2 * one_third):] if len(active_power_sites) > 2 else active_power_sites

        # Load teams dynamically from SQLite paas_field_teams table
        db_teams = RolloutOperationsService.get_field_teams_list()
        field_teams = []
        for t_info in db_teams:
            t_code = t_info["team_code"]
            is_baseline_team = t_code in ["TEAM-ALPHA", "TEAM-BETA", "TEAM-GAMMA", "TEAM-DELTA", "TEAM-EPSILON", "TEAM-ZETA"]
            
            # Domain-matched fallback preference for baseline teams
            if t_code == "TEAM-ALPHA":
                domain_df = p_alpha
            elif t_code == "TEAM-BETA":
                domain_df = p_beta
            elif t_code == "TEAM-GAMMA":
                domain_df = p_gamma
            elif t_code == "TEAM-DELTA":
                domain_df = active_testing_sites
            elif t_code == "TEAM-EPSILON":
                domain_df = active_shipping_sites
            elif t_code == "TEAM-ZETA":
                domain_df = active_blocked_sites if not active_blocked_sites.empty else df_blocked
            else:
                domain_df = pd.DataFrame()

            # All teams strictly show their truly assigned sites from SQLite (no in-memory mock synthesis)
            t_sites = build_assigned_sites(
                domain_df, 
                df_view, 
                t_code, 
                limit=100, 
                strict_explicit=True
            )

            completed_count = len([s for s in t_sites if "Handover" in s["paas_status"] or "Completed" in s["paas_status"]])
            t_pct = int((completed_count / len(t_sites)) * 100) if t_sites else 0
            if is_baseline_team and t_pct == 0:
                baseline_pcts = {"TEAM-ALPHA": 75, "TEAM-BETA": 60, "TEAM-GAMMA": 45, "TEAM-DELTA": 85, "TEAM-EPSILON": 50, "TEAM-ZETA": 30 if c_blocked > 0 else 100}
                t_pct = baseline_pcts.get(t_code, 50)

            field_teams.append({
                "team_code": t_code,
                "team_name": t_info["team_name"],
                "lead_name": t_info["lead_name"],
                "specialization": t_info["specialization"],
                "crew_size": t_info.get("crew_size", 4),
                "contact_number": t_info.get("contact_number", "-"),
                "assigned_sites": t_sites,
                "assigned_site_id": t_sites[0]["site_id"] if t_sites else "-",
                "assigned_site_name": t_sites[0]["site_name"] if t_sites else "-",
                "district": t_sites[0]["district"] if t_sites else "-",
                "current_activity": t_sites[0]["action_plan"] if t_sites else f"Field operations managed by {t_info['lead_name']}",
                "status": t_info.get("status", "On-Site Active"),
                "completion_pct": t_pct,
                "current_lat": t_info.get("current_lat"),
                "current_lon": t_info.get("current_lon"),
                "current_address": t_info.get("current_address"),
                "last_checkin_site": t_info.get("last_checkin_site"),
                "last_checkin_at": t_info.get("last_checkin_at"),
                "checkin_status": t_info.get("checkin_status"),
                "battery_pct": t_info.get("battery_pct", 95)
            })

        sites_beta = next((t["assigned_sites"] for t in field_teams if t["team_code"] == "TEAM-BETA"), [])
        sites_gamma = next((t["assigned_sites"] for t in field_teams if t["team_code"] == "TEAM-GAMMA"), [])
        sites_delta = next((t["assigned_sites"] for t in field_teams if t["team_code"] == "TEAM-DELTA"), [])

        p1_id = sites_beta[0]["site_id"] if sites_beta else "VCU008"
        p1_name = sites_beta[0]["site_name"] if sites_beta else "EWSD"
        p1_dist = sites_beta[0]["district"] if sites_beta else "Dili"
        p2_id = sites_gamma[0]["site_id"] if sites_gamma else "VCU012"
        p2_name = sites_gamma[0]["site_name"] if sites_gamma else "ROOFTOP_COLMERA"
        p2_dist = sites_gamma[0]["district"] if sites_gamma else "Dili"
        t1_id = sites_delta[0]["site_id"] if sites_delta else "VCU001"
        t1_name = sites_delta[0]["site_name"] if sites_delta else "Palpaco"
        t1_dist = sites_delta[0]["district"] if sites_delta else "Dili"

        # 3. Milestone Check Points & Weekly Completion Targets
        weekly_commissioning = [
            {"site_id": p1_id, "site_name": p1_name, "district": p1_dist, "milestone_checkpoint": "Power I&C Commissioning", "target_week": "Week 36 (Fri 17:00)", "status": "In Progress"},
            {"site_id": p2_id, "site_name": p2_name, "district": p2_dist, "milestone_checkpoint": "Battery Bank Integration", "target_week": "Week 36 (Fri 17:00)", "status": "In Progress"}
        ]
        weekly_atp = [
            {"site_id": t1_id, "site_name": t1_name, "district": t1_dist, "milestone_checkpoint": "ATP Acceptance Sign-off", "target_week": "Week 36 (Fri 17:00)", "status": "Final QA Run"}
        ]
        today_commissioning = weekly_commissioning
        today_atp = weekly_atp

        # 4. 5-Stage Micro-Progress Workflow Pipeline (Pure PaaS Scope)
        micro_pipeline = {
            "stage_1_survey": total_sites,  # 100% baseline survey completed
            "stage_2_staged": c_staged + c_power + c_testing + c_handover,
            "stage_3_power": c_power + c_testing + c_handover,
            "stage_4_testing": c_testing + c_handover,
            "stage_5_atp_live": c_handover
        }

        # 5. Rollout Pace & Velocity (Dynamically synchronized with active fleet & site completions)
        weekly_target = 5
        if len(field_teams) == 0:
            weekly_actual = 0
            velocity_run_rate = 0.0
        else:
            total_handover_assigned = sum(
                len([s for s in t.get("assigned_sites", []) if "Handover" in s.get("paas_status", "")])
                for t in field_teams
            )
            weekly_actual = min(weekly_target, total_handover_assigned) if total_handover_assigned > 0 else min(weekly_target, max(0, c_handover))
            velocity_run_rate = round(weekly_actual / max(weekly_target, 1), 2)

        return {
            "selected_operator": selected_operator,
            "total_sites": total_sites,
            "c_handover": c_handover,
            "c_power": c_power,
            "c_testing": c_testing,
            "c_civil": c_civil,
            "c_civil_dep": c_civil_dep,
            "c_staged": c_staged,
            "c_shipping": c_shipping,
            "c_blocked": c_blocked,
            "active_crews_count": len([t for t in field_teams if "Active" in t["status"] or "In-Transit" in t["status"]]),
            "total_specialists": sum(t["crew_size"] for t in field_teams),
            "field_teams": field_teams,
            "blockers": blockers,
            "weekly_commissioning": weekly_commissioning,
            "weekly_atp": weekly_atp,
            "today_commissioning": today_commissioning,
            "today_atp": today_atp,
            "weekly_target": weekly_target,
            "weekly_actual": weekly_actual,
            "velocity_run_rate": velocity_run_rate,
            "micro_pipeline": micro_pipeline,
            "all_sites_df": df_view,
            "unassigned_sites_df": df_view[df_view["assigned_team"].isna() | (df_view["assigned_team"] == "")].copy(),
            "escalated_sites_df": df_view[df_view["readiness_gate"].str.contains("ESCALATE", na=False) | df_view["paas_status"].str.contains("Blocked", na=False)].copy(),
            "dropped_sites_df": df_view[df_view["readiness_gate"].str.contains("DROPPED", na=False) | df_view["paas_status"].str.contains("Dropped", na=False)].copy()
        }

    @staticmethod
    def get_moa_mos_flow_summary(selected_operator: str = "All") -> Dict[str, Any]:
        """
        Computes the operational logic for Material on Area (MOA) to Material on Site (MOS).
        Pure Direct-to-Site Architecture (Zero Forward Hubs).

        Rules:
        1. MOA (Material on Area):
           - Inbound shipment arrived and unsealed at Port of Entry (Port Dili, Belawan, etc.).
           - Staged at port terminal with zero secondary warehouse rental.
        2. Gate Evaluation (Civil Readiness Verification):
           - IF civil works complete / gate GO:
             -> Status: 'Ready for Direct Dispatch'
           - ELSE:
             -> Status: 'MOA Staged at Port (Awaiting Civil GO)'
        3. In-Transit:
           - Direct dispatch convoy rolling from Port directly to tower coordinates.
        4. MOS (Material on Site):
           - Material arrived and physical delivery accepted at tower foundation (BAST MOS).
           - Unlocks Power I&C installation.
        """
        df_all = query_df("SELECT * FROM timor_sites_100 ORDER BY accessible_route_km ASC")
        if df_all.empty:
            return {
                "total_sites": 0,
                "moa_port_count": 0,
                "ready_dispatch_count": 0,
                "in_transit_count": 0,
                "mos_confirmed_count": 0,
                "flow_df": pd.DataFrame()
            }

        if selected_operator != "All":
            df_view = df_all[df_all["operator"] == selected_operator].copy()
        else:
            df_view = df_all.copy()

        site_flow: List[Dict[str, Any]] = []
        c_moa_port = 0
        c_ready_dispatch = 0
        c_in_transit = 0
        c_mos_confirmed = 0

        for _, row in df_view.iterrows():
            st = str(row["paas_status"])
            gate = str(row["readiness_gate"])
            sid = row["site_id"]
            sname = row["site_name"]
            dist = row["district"]
            km = row["accessible_route_km"]
            eta = row["est_travel_time"]
            op = row.get("operator", "Telkomcel")

            # Determine Port of Entry based on operator
            if op == "XLSmart":
                port_origin = "Pelabuhan Belawan"
            elif op == "Mitratel":
                port_origin = "Pelabuhan Tanjung Perak"
            elif op == "IOH":
                port_origin = "Pelabuhan Semayang"
            else:
                port_origin = "Port Dili"

            if "Handover" in st or "Testing" in st or "Power" in st:
                moa_stage = "MOS Confirmed (On-Site)"
                moa_badge = "MOS_CONFIRMED"
                dispatch_gate = "Delivered & Accepted at Site"
                c_mos_confirmed += 1
            elif "Shipping" in st:
                moa_stage = "Inbound Ocean Freight"
                moa_badge = "INBOUND"
                dispatch_gate = "Customs Clearance at Port"
                c_moa_port += 1
            else:  # Staged / Port
                if "Civil Dependency" in gate or "HOLD" in gate:
                    moa_stage = "MOA Staged at Port (Awaiting Civil/TowerCo)"
                    moa_badge = "MOA_HELD"
                    dispatch_gate = "Tower Plinth Dependency • Dispatch HELD"
                    c_moa_port += 1
                elif "GO" in gate or "Passed" in gate:
                    moa_stage = "Ready for Direct Dispatch"
                    moa_badge = "READY_DISPATCH"
                    dispatch_gate = "Tower Plinth Certified • Ready to Roll"
                    c_ready_dispatch += 1
                else:
                    moa_stage = "MOA Staged at Port"
                    moa_badge = "MOA_PORT"
                    dispatch_gate = "Material Staged at Port Area"
                    c_moa_port += 1

            site_flow.append({
                "site_id": sid,
                "site_name": sname,
                "district": dist,
                "port_origin": port_origin,
                "route_km": km,
                "travel_time": eta,
                "paas_status": st,
                "readiness_gate": gate,
                "moa_stage": moa_stage,
                "moa_badge": moa_badge,
                "dispatch_gate": dispatch_gate
            })

        df_flow = pd.DataFrame(site_flow)

        return {
            "total_sites": len(df_view),
            "moa_port_count": c_moa_port,
            "ready_dispatch_count": c_ready_dispatch,
            "in_transit_count": c_in_transit,
            "mos_confirmed_count": c_mos_confirmed,
            "flow_df": df_flow
        }

    @staticmethod
    def dispatch_moa_to_mos(site_id: str) -> bool:
        """
        Executes the direct dispatch transition from Material on Area (Port) to Material on Site (MOS).
        Advances the site's paas_status to 'Power I&C Active' and sets readiness gate to 'Passed - Site Ready for Installation'.
        """
        return RolloutOperationsService.update_site_status(
            site_id,
            "🟣 Power I&C Active",
            "Passed - Site Ready for Installation"
        )

    @staticmethod
    def resolve_site_blocker(site_id: str, new_status: str, new_gate: str) -> bool:
        """
        Updates a site record in SQLite, resolving a blocker or advancing status.
        """
        sql = "UPDATE timor_sites_100 SET paas_status = ?, readiness_gate = ? WHERE site_id = ?"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (new_status, new_gate, site_id))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def update_site_status(site_id: str, new_status: str, new_gate: str) -> bool:
        """
        Updates a site record in SQLite with new PaaS rollout status and readiness decision gate.
        """
        return RolloutOperationsService.resolve_site_blocker(site_id, new_status, new_gate)

    @staticmethod
    def get_next_stage_preview(current_status: str) -> Tuple[str, str, str]:
        """
        Returns (next_status, next_gate, action_button_label) for governed sequential stage advancement.
        Follows standard telecom rollout quality gates.
        """
        st = str(current_status)
        if "Shipping" in st or "Staged" in st:
            return ("🟣 Power I&C Active", "Passed - Site Ready for Installation", "Advance to Power I&C Installation")
        elif "Power" in st:
            return ("🟡 Testing & QA", "Passed - Power I&C Commissioned", "Advance to Acceptance Testing (ATP)")
        elif "Testing" in st:
            return ("🟢 Handover Telkomcel", "G5 - Handover [GO]", "Advance to Commercial Handover")
        elif "Blocked" in st:
            return ("🟣 Power I&C Active", "GO (Dispatch Ready)", "Resolve Blocker & Resume Power I&C")
        else:
            return ("", "", "Handover Completed (Final Stage)")

    @staticmethod
    def advance_site_stage(site_id: str, operator_user: str = "PMO Command Center") -> Dict[str, Any]:
        """
        Executes governed sequential advancement to the next lifecycle stage.
        Ensures audit logging with timestamp and user.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT paas_status, readiness_gate, operator FROM timor_sites_100 WHERE site_id = ?", (site_id,))
            row = cur.fetchone()
            if not row:
                return {"success": False, "message": f"Site {site_id} not found."}
            
            curr_status = row["paas_status"]
            curr_op = row["operator"] or "Telkomcel"
            next_status, next_gate, _ = RolloutOperationsService.get_next_stage_preview(curr_status)
            
            if not next_status:
                return {"success": False, "message": f"Site {site_id} is already at final Handover Completed stage."}

            if "Handover" in next_status and curr_op != "Telkomcel":
                next_status = f"🟢 Handover {curr_op}"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            cur.execute(
                """
                UPDATE timor_sites_100 
                SET paas_status = ?, readiness_gate = ?, updated_at = ?, last_updated_by = ?, blocker_reason = NULL
                WHERE site_id = ?
                """,
                (next_status, next_gate, now_str, operator_user, site_id)
            )
            conn.commit()
            return {
                "success": True,
                "old_status": curr_status,
                "new_status": next_status,
                "new_gate": next_gate,
                "updated_at": now_str
            }
        finally:
            conn.close()

    @staticmethod
    def flag_site_blocker(site_id: str, category: str, reason: str, pic: str = "Adolfo Da Silva (Field Acquisition)") -> bool:
        """
        Quarantines a site as Blocked / Issue, creates blocker ticket, and automatically
        routes the site to TEAM-ZETA (Rapid Issue Resolution).
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        gate = "HOLD (Dependency)" if "Curing" in category or "Grid" in category else "ESCALATE (High Risk)"
        blocker_text = f"[{category}] {reason}"
        
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE timor_sites_100
                SET paas_status = '🔴 Blocked / Issue', 
                    readiness_gate = ?, 
                    assigned_team = 'TEAM-ZETA', 
                    blocker_reason = ?, 
                    updated_at = ?, 
                    last_updated_by = ?
                WHERE site_id = ?
                """,
                (gate, blocker_text, now_str, pic, site_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def reassign_site_crew(site_id: str, target_team_code: str, pic_user: str = "PMO Command Center") -> bool:
        """
        Reassigns / delegates a site to another field team and logs the user.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE timor_sites_100
                SET assigned_team = ?, updated_at = ?, last_updated_by = ?
                WHERE site_id = ?
                """,
                (target_team_code, now_str, pic_user, site_id)
            )
            site_rowcount = cur.rowcount
            cur.execute(
                """
                UPDATE paas_field_teams
                SET last_checkin_site = ?, updated_at = ?
                WHERE team_code = ?
                """,
                (site_id, now_str, target_team_code)
            )
            conn.commit()
            if site_rowcount > 0:
                from services.fleet_tracking_service import FleetTrackingService
                FleetTrackingService.auto_initialize_assigned_team_hub(target_team_code, site_id)
                return True
            return False
        finally:
            conn.close()

    @staticmethod
    def assign_site_to_team(site_id: str, team_code: str, user: str = "PMO Command Center") -> bool:
        """
        Assigns site ownership to a team owner from the beginning.
        """
        return RolloutOperationsService.reassign_site_crew(site_id, team_code, pic_user=user)

    @staticmethod
    def update_site_lifecycle_status(site_id: str, new_status: str, new_gate: Optional[str] = None, user: str = "PMO Command Center") -> bool:
        """
        Directly updates site status for owned sites with auto-inferred gate.
        """
        if not new_gate:
            st = str(new_status)
            if "Power" in st:
                new_gate = "Passed - Site Ready for Installation"
            elif "Testing" in st:
                new_gate = "Passed - Power I&C Commissioned"
            elif "Completed" in st or "Handover" in st:
                new_gate = "G5 - Handover [GO]"
            else:
                new_gate = "GO (Dispatch Ready)"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE timor_sites_100
                SET paas_status = ?, readiness_gate = ?, updated_at = ?, last_updated_by = ?, blocker_reason = NULL
                WHERE site_id = ?
                """,
                (new_status, new_gate, now_str, user, site_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def escalate_site(site_id: str, blocker_category: str, blocker_note: str, user: str = "PMO Command Center") -> bool:
        """
        Marks site as ESCALATE for urgent management attention while preserving team ownership.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        blocker_text = f"[{blocker_category}] {blocker_note}"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE timor_sites_100
                SET paas_status = '🔴 Blocked / Issue', 
                    readiness_gate = 'ESCALATE', 
                    blocker_reason = ?, 
                    updated_at = ?, 
                    last_updated_by = ?
                WHERE site_id = ?
                """,
                (blocker_text, now_str, user, site_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def drop_site(site_id: str, blocker_category: str, drop_reason: str, user: str = "PMO Command Center") -> bool:
        """
        Drops site from active team queue and parks it into resequenced/reserve pool.
        Frees team from being blocked by this site.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        blocker_text = f"DROPPED: [{blocker_category}] {drop_reason}"
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE timor_sites_100
                SET paas_status = '⚪ Dropped / Resequenced', 
                    readiness_gate = 'DROPPED', 
                    assigned_team = NULL, 
                    blocker_reason = ?, 
                    updated_at = ?, 
                    last_updated_by = ?
                WHERE site_id = ?
                """,
                (blocker_text, now_str, user, site_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def reactivate_site(site_id: str, target_team_code: Optional[str] = None, user: str = "PMO Command Center") -> bool:
        """
        Reactivates a dropped site back into active deployment.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE timor_sites_100
                SET paas_status = '🟣 Power I&C Active', 
                    readiness_gate = 'GO (Dispatch Ready)', 
                    assigned_team = ?, 
                    blocker_reason = NULL, 
                    updated_at = ?, 
                    last_updated_by = ?
                WHERE site_id = ?
                """,
                (target_team_code, now_str, user, site_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def auto_distribute_initial_baseline(operator: str = "All", limit_per_team: int = 4) -> int:
        """
        Seeds initial balanced site workload across all 6 teams if pool is unassigned.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            sql = "SELECT site_id, paas_status FROM timor_sites_100 WHERE assigned_team IS NULL"
            params = ()
            if operator != "All":
                sql += " AND operator = ?"
                params = (operator,)
            sql += " ORDER BY accessible_route_km ASC"
            cur.execute(sql, params)
            unassigned = cur.fetchall()
            
            db_teams = RolloutOperationsService.get_field_teams_list()
            teams = [t["team_code"] for t in db_teams]
            if not teams:
                return 0

            assigned_count = 0
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            for idx, r in enumerate(unassigned[:len(teams) * limit_per_team]):
                t_code = teams[idx % len(teams)]
                cur.execute(
                    "UPDATE timor_sites_100 SET assigned_team = ?, updated_at = ?, last_updated_by = 'Auto Baseline' WHERE site_id = ?",
                    (t_code, now_str, r["site_id"])
                )
                assigned_count += 1
            conn.commit()
            return assigned_count
        finally:
            conn.close()

    @staticmethod
    def get_field_teams_list() -> List[Dict[str, Any]]:
        """
        Retrieves all configured PaaS rollout field teams from SQLite database.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT *
                FROM paas_field_teams
                ORDER BY id ASC
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def add_field_team(
        team_name: str,
        lead_name: str,
        specialization: str,
        crew_size: int = 4,
        contact_number: Optional[str] = None,
        status: str = "On-Site Active",
        team_code: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Adds a new field team to paas_field_teams table.
        """
        clean_name = str(team_name).strip()
        clean_lead = str(lead_name).strip()
        clean_spec = str(specialization).strip()
        if not clean_name or not clean_lead:
            return False, "Team Name and Lead PIC Name are required."
        
        # Generate or format team_code
        if not team_code:
            import re
            slug = re.sub(r'[^A-Za-z0-9]+', '-', clean_name).strip('-').upper()
            if not slug.startswith("TEAM-"):
                slug = f"TEAM-{slug}"
            team_code = slug[:20]
        else:
            team_code = str(team_code).strip().upper()
            if not team_code.startswith("TEAM-"):
                team_code = f"TEAM-{team_code}"

        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM paas_field_teams WHERE team_code = ?", (team_code,))
            if cur.fetchone():
                return False, f"Team Code '{team_code}' already exists. Please choose a unique code."

            cur.execute("""
                INSERT INTO paas_field_teams (team_code, team_name, lead_name, specialization, crew_size, contact_number, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (team_code, clean_name, clean_lead, clean_spec, int(crew_size), contact_number, status, now_iso, now_iso))
            conn.commit()
            return True, f"Field Team '{clean_name}' [{team_code}] successfully added to fleet roster!"
        except Exception as e:
            return False, f"Database error adding team: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def remove_field_team(team_code: str, reassign_to_team_code: Optional[str] = None) -> Tuple[bool, str]:
        """
        Removes a field team from fleet roster.
        If team has assigned sites, reassigns them to target team or unassigns them back to pool.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT team_name FROM paas_field_teams WHERE team_code = ?", (team_code,))
            team_row = cur.fetchone()
            if not team_row:
                return False, f"Team Code '{team_code}' not found."
            t_name = team_row["team_name"]

            # Count assigned sites
            cur.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE assigned_team = ?", (team_code,))
            assigned_count = cur.fetchone()[0]

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
            if assigned_count > 0:
                if reassign_to_team_code:
                    cur.execute("""
                        UPDATE timor_sites_100 
                        SET assigned_team = ?, updated_at = ?, last_updated_by = 'PMO Team Reallocation'
                        WHERE assigned_team = ?
                    """, (reassign_to_team_code, now_iso, team_code))
                else:
                    cur.execute("""
                        UPDATE timor_sites_100 
                        SET assigned_team = NULL, updated_at = ?, last_updated_by = 'PMO Team Disbandment'
                        WHERE assigned_team = ?
                    """, (now_iso, team_code))

            cur.execute("DELETE FROM paas_field_teams WHERE team_code = ?", (team_code,))
            conn.commit()

            site_msg = f"{assigned_count} site(s) reassigned to {reassign_to_team_code}" if reassign_to_team_code else f"{assigned_count} site(s) moved to unassigned pool"
            return True, f"Team '{t_name}' [{team_code}] removed. {site_msg}."
        except Exception as e:
            return False, f"Database error removing team: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def update_field_team(
        team_code: str,
        team_name: str,
        lead_name: str,
        specialization: str,
        crew_size: int = 4,
        contact_number: Optional[str] = None,
        status: str = "On-Site Active"
    ) -> Tuple[bool, str]:
        """
        Updates profile and crew size for an existing field team.
        """
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE paas_field_teams
                SET team_name = ?, lead_name = ?, specialization = ?, crew_size = ?, contact_number = ?, status = ?, updated_at = ?
                WHERE team_code = ?
            """, (team_name, lead_name, specialization, int(crew_size), contact_number, status, now_iso, team_code))
            conn.commit()
            if cur.rowcount > 0:
                return True, f"Team {team_code} profile updated successfully."
            return False, f"Team {team_code} not found."
        except Exception as e:
            return False, f"Database error updating team: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def clear_all_field_teams(unassign_sites: bool = True, reset_to_initial_staging: bool = True) -> Tuple[bool, str]:
        """
        Decommissions all field teams from the fleet roster.
        If reset_to_initial_staging is True, resets all sites back to their initial unworked
        Staged state ('⚪ Staged / Dili Hub' or '⚪ Staged / Regional Hub'), clearing live COD
        and in-flight statuses to 0% so the user can simulate the rollout from scratch.
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM paas_field_teams")
            teams_count = cur.fetchone()[0]

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
            affected_sites = 0
            if reset_to_initial_staging:
                cur.execute("""
                    UPDATE timor_sites_100
                    SET assigned_team = NULL,
                        paas_status = CASE 
                            WHEN operator = 'Telkomcel' THEN '⚪ Staged / Dili Hub'
                            ELSE '⚪ Staged / Regional Hub'
                        END,
                        readiness_gate = 'GO (Dispatch Ready)',
                        blocker_reason = NULL,
                        updated_at = ?,
                        last_updated_by = 'Simulation Reset to Zero'
                """, (now_iso,))
                affected_sites = cur.rowcount
            elif unassign_sites:
                cur.execute("""
                    UPDATE timor_sites_100
                    SET assigned_team = NULL, updated_at = ?, last_updated_by = 'Fleet Reset to Zero'
                    WHERE assigned_team IS NOT NULL AND assigned_team != ''
                """, (now_iso,))
                affected_sites = cur.rowcount

            cur.execute("DELETE FROM paas_field_teams")
            conn.commit()
            return True, f"Successfully removed all {teams_count} field team(s) and reset {affected_sites} site(s) to Staged Backlog (0% Live COD)."
        except Exception as e:
            return False, f"Database error clearing field teams: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def reset_baseline_teams() -> Tuple[bool, str]:
        """
        Restores the standard 6 baseline field teams (Alpha through Zeta) and restores
        the baseline demonstration site statuses and assignments across all operators.
        """
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
        baseline_teams = [
            ("TEAM-ALPHA", "Team Alpha (DC Power & Rectifier I&C)", "Adolfo Da Silva", "DC Power Systems & Rectifier Shelf Mounting", 8, "+670 7723 1001", "On-Site Active", now_iso, now_iso),
            ("TEAM-BETA", "Team Beta (Power I&C Lead)", "Mateus Fernandes", "Rectifiers & Smart Hybrid Integration", 6, "+670 7723 1002", "On-Site Active", now_iso, now_iso),
            ("TEAM-GAMMA", "Team Gamma (Power I&C Secondary)", "Gaspar Soares", "LiFePO4 Lithium Battery Commissioning", 5, "+670 7723 1003", "On-Site Active", now_iso, now_iso),
            ("TEAM-DELTA", "Team Delta (QA & Acceptance Testing)", "Domingos Pinto", "24h Load Test & NOC Telemetry ATP", 4, "+670 7723 1004", "On-Site Active", now_iso, now_iso),
            ("TEAM-EPSILON", "Team Epsilon (JIT Logistics & Delivery)", "Carlos Da Costa", "Pure Direct-to-Site Delivery (Port to Site)", 6, "+670 7723 1005", "In-Transit", now_iso, now_iso),
            ("TEAM-ZETA", "Team Zeta (Rapid Issue Resolution)", "Bernardo Ximenes", "Escalation & Landlord Re-Permitting", 5, "+670 7723 1006", "Standby Ready", now_iso, now_iso),
        ]
        conn = get_connection()
        try:
            cur = conn.cursor()
            for t in baseline_teams:
                cur.execute("""
                    INSERT OR REPLACE INTO paas_field_teams 
                    (team_code, team_name, lead_name, specialization, crew_size, contact_number, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, t)

            # Restore Telkomcel demonstration baseline statuses (28 Handover, 43 Testing, 7 Power, 22 Staged)
            cur.execute("""
                UPDATE timor_sites_100
                SET paas_status = CASE
                    WHEN no <= 28 THEN '🟢 Handover Telkomcel'
                    WHEN no <= 44 THEN '🟡 Testing & QA'
                    WHEN no <= 66 THEN '🟣 Power I&C Active'
                    WHEN no <= 78 THEN '⚪ Staged / Delivery Ready'
                    WHEN no <= 92 THEN '⚪ Staged / Dili Hub'
                    ELSE 'Shipping & Customs'
                END,
                readiness_gate = CASE
                    WHEN no BETWEEN 67 AND 78 THEN 'HOLD (Civil Dependency)'
                    ELSE 'GO (Dispatch Ready)'
                END,
                blocker_reason = CASE
                    WHEN no BETWEEN 67 AND 78 THEN '[Civil Dependency] Tower foundation / plinth not ready by TowerCo'
                    ELSE NULL
                END,
                assigned_team = CASE
                    WHEN no <= 4 THEN 'TEAM-ALPHA'
                    WHEN no BETWEEN 5 AND 8 THEN 'TEAM-BETA'
                    WHEN no BETWEEN 9 AND 12 THEN 'TEAM-GAMMA'
                    WHEN no BETWEEN 13 AND 16 THEN 'TEAM-DELTA'
                    WHEN no BETWEEN 17 AND 20 THEN 'TEAM-EPSILON'
                    WHEN no BETWEEN 21 AND 24 THEN 'TEAM-ZETA'
                    ELSE NULL
                END,
                updated_at = ?,
                last_updated_by = 'Baseline Restoration'
                WHERE operator = 'Telkomcel'
            """, (now_iso,))

            # Restore multi-tenant demonstration baseline
            cur.execute("""
                UPDATE timor_sites_100
                SET paas_status = CASE
                    WHEN operator = 'XLSmart' AND no <= 6 THEN '🟢 Handover XLSmart'
                    WHEN operator = 'XLSmart' AND no <= 14 THEN '🟡 Testing & QA'
                    WHEN operator = 'XLSmart' AND no <= 19 THEN '🟣 Power I&C Active'
                    WHEN operator = 'XLSmart' THEN '⚪ Staged / Regional Hub'
                    WHEN operator = 'Mitratel' AND no <= 10 THEN '🟢 Handover Mitratel'
                    WHEN operator = 'Mitratel' AND no <= 24 THEN '🟡 Testing & QA'
                    WHEN operator = 'Mitratel' AND no <= 27 THEN '🟣 Power I&C Active'
                    WHEN operator = 'Mitratel' THEN '⚪ Staged / Regional Hub'
                    WHEN operator = 'IOH' AND no <= 4 THEN '🟢 Handover IOH'
                    WHEN operator = 'IOH' AND no <= 14 THEN '🟡 Testing & QA'
                    WHEN operator = 'IOH' AND no <= 17 THEN '🟣 Power I&C Active'
                    WHEN operator = 'IOH' THEN '⚪ Staged / Regional Hub'
                    ELSE paas_status
                END
                WHERE operator != 'Telkomcel'
            """)

            cur.execute("INSERT OR REPLACE INTO system_metadata (key, value) VALUES ('paas_teams_seeded', '1')")
            conn.commit()
            return True, "Successfully restored 6 default baseline teams (Alpha - Zeta) and initial demonstration statuses."
        except Exception as e:
            return False, f"Database error restoring baseline teams: {str(e)}"
        finally:
            conn.close()


