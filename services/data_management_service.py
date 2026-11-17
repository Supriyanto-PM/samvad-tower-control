"""
Data Management and Cleaning Service for Samvad PMO-CC.
Provides administrative data operations:
1. Bulk site status resets.
2. Blocker and dependency clearing.
3. Fleet unassignment.
4. Clean file import (CSV / Excel) with Upsert or Wipe & Replace modes.
5. Table wiping and baseline restoration.
6. Audit log purge.
Strictly enterprise, typography-focused, icon-free logging.
"""

import os
import io
import sqlite3
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from database.connection import get_connection, query_df, execute_write, ensure_governance_schema
from config.settings import DATABASE_PATH


class DataManagementService:
    @staticmethod
    def get_database_summary() -> Dict[str, Any]:
        """Returns row counts and metadata across operational tables."""
        conn = get_connection()
        summary = {
            "total_sites": 0,
            "sites_by_operator": {},
            "sites_by_status": {},
            "blocked_sites": 0,
            "assigned_sites": 0,
            "field_teams": 0,
            "audit_logs": 0
        }
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM timor_sites_100")
            summary["total_sites"] = cur.fetchone()[0]

            cur.execute("SELECT operator, COUNT(*) FROM timor_sites_100 GROUP BY operator")
            summary["sites_by_operator"] = dict(cur.fetchall())

            cur.execute("SELECT paas_status, COUNT(*) FROM timor_sites_100 GROUP BY paas_status")
            summary["sites_by_status"] = dict(cur.fetchall())

            cur.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE blocker_reason IS NOT NULL AND blocker_reason != ''")
            summary["blocked_sites"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE assigned_team IS NOT NULL AND assigned_team != ''")
            summary["assigned_sites"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM paas_field_teams")
            summary["field_teams"] = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM notification_audit_logs")
            summary["audit_logs"] = cur.fetchone()[0]
        except Exception as e:
            summary["error"] = str(e)
        finally:
            conn.close()
        return summary

    @staticmethod
    def reset_all_site_statuses(target_status: str, operator: str = "All") -> Tuple[bool, str, int]:
        """
        Resets paas_status for all sites (or selected operator) to target_status,
        clearing blocker reasons and resetting readiness gates to GO (Dispatch Ready).
        """
        now_iso = datetime.now().isoformat()
        sql = """
            UPDATE timor_sites_100
            SET paas_status = ?,
                readiness_gate = 'GO (Dispatch Ready)',
                blocker_reason = NULL,
                updated_at = ?,
                last_updated_by = 'Data Management Console'
        """
        params = [target_status, now_iso]

        if operator != "All":
            sql += " WHERE operator = ?"
            params.append(operator)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            affected = cur.rowcount
            conn.commit()

            # Audit entry
            cur.execute(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DataManagement",
                    "Admin",
                    "STATUS_BULK_RESET",
                    f"Reset {affected} sites to '{target_status}' for operator '{operator}'",
                    "SUCCESS"
                )
            )
            conn.commit()
            return True, f"Successfully reset {affected} site(s) to status '{target_status}'.", affected
        except Exception as e:
            return False, f"Failed to reset statuses: {str(e)}", 0
        finally:
            conn.close()

    @staticmethod
    def clear_all_blockers(operator: str = "All") -> Tuple[bool, str, int]:
        """Clears blocker reasons and resets readiness gates back to GO."""
        now_iso = datetime.now().isoformat()
        sql = """
            UPDATE timor_sites_100
            SET blocker_reason = NULL,
                readiness_gate = 'GO (Dispatch Ready)',
                updated_at = ?,
                last_updated_by = 'Data Management Console'
            WHERE (blocker_reason IS NOT NULL AND blocker_reason != '')
               OR readiness_gate LIKE '%HOLD%'
               OR readiness_gate LIKE '%ESCALATE%'
        """
        params = [now_iso]

        if operator != "All":
            sql = """
                UPDATE timor_sites_100
                SET blocker_reason = NULL,
                    readiness_gate = 'GO (Dispatch Ready)',
                    updated_at = ?,
                    last_updated_by = 'Data Management Console'
                WHERE ((blocker_reason IS NOT NULL AND blocker_reason != '')
                   OR readiness_gate LIKE '%HOLD%'
                   OR readiness_gate LIKE '%ESCALATE%')
                   AND operator = ?
            """
            params.append(operator)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            affected = cur.rowcount
            conn.commit()

            cur.execute(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DataManagement",
                    "Admin",
                    "BLOCKER_CLEANUP",
                    f"Cleared blockers on {affected} site(s) for operator '{operator}'",
                    "SUCCESS"
                )
            )
            conn.commit()
            return True, f"Cleared blockers and hold gates on {affected} site(s).", affected
        except Exception as e:
            return False, f"Failed to clear blockers: {str(e)}", 0
        finally:
            conn.close()

    @staticmethod
    def unassign_all_sites(operator: str = "All") -> Tuple[bool, str, int]:
        """Unassigns all field teams from sites, returning assigned_team to NULL."""
        now_iso = datetime.now().isoformat()
        sql = """
            UPDATE timor_sites_100
            SET assigned_team = NULL,
                updated_at = ?,
                last_updated_by = 'Data Management Console'
            WHERE assigned_team IS NOT NULL
        """
        params = [now_iso]

        if operator != "All":
            sql += " AND operator = ?"
            params.append(operator)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            affected = cur.rowcount
            conn.commit()

            cur.execute(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DataManagement",
                    "Admin",
                    "FLEET_UNASSIGN_ALL",
                    f"Unassigned fleet teams from {affected} site(s) for operator '{operator}'",
                    "SUCCESS"
                )
            )
            conn.commit()
            return True, f"Unassigned field teams from {affected} site(s).", affected
        except Exception as e:
            return False, f"Failed to unassign sites: {str(e)}", 0
        finally:
            conn.close()

    @staticmethod
    def wipe_all_sites(operator: str = "All") -> Tuple[bool, str, int]:
        """
        Deletes all site records from timor_sites_100.
        Allows starting with an empty database to import custom sites.
        """
        sql = "DELETE FROM timor_sites_100"
        params = []
        if operator != "All":
            sql += " WHERE operator = ?"
            params.append(operator)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            affected = cur.rowcount
            conn.commit()

            cur.execute(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DataManagement",
                    "Admin",
                    "SITES_WIPE",
                    f"Wiped {affected} site(s) from database for operator '{operator}'",
                    "WARNING"
                )
            )
            conn.commit()
            return True, f"Wiped {affected} site(s) from database.", affected
        except Exception as e:
            return False, f"Failed to wipe sites: {str(e)}", 0
        finally:
            conn.close()

    @staticmethod
    def restore_factory_baseline() -> Tuple[bool, str, int]:
        """
        Restores the full 180-site factory baseline (100 Timor-Leste + 80 multi-tenant regional sites).
        """
        from database.timor_sites_data import seed_timor_100_sites
        from database.multi_tenant_data import seed_multi_tenant_sites
        from services.rollout_operations_service import RolloutOperationsService

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM timor_sites_100")
            conn.commit()
            conn.close()

            seed_timor_100_sites()
            seed_multi_tenant_sites()
            ensure_governance_schema()
            RolloutOperationsService.reset_baseline_teams()

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM timor_sites_100")
            total = cur.fetchone()[0]

            cur.execute(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DataManagement",
                    "Admin",
                    "FACTORY_BASELINE_RESTORE",
                    f"Restored full factory baseline with {total} sites and 6 specialized teams",
                    "SUCCESS"
                )
            )
            conn.commit()
            return True, f"Factory baseline successfully restored with {total} operational sites.", total
        except Exception as e:
            return False, f"Failed to restore factory baseline: {str(e)}", 0
        finally:
            if conn:
                conn.close()

    @staticmethod
    def clear_audit_logs(keep_last_n: int = 0) -> Tuple[bool, str, int]:
        """Purges audit logs, optionally keeping the last N entries."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            if keep_last_n <= 0:
                cur.execute("DELETE FROM notification_audit_logs")
                affected = cur.rowcount
            else:
                cur.execute(
                    """
                    DELETE FROM notification_audit_logs
                    WHERE id NOT IN (
                        SELECT id FROM notification_audit_logs ORDER BY sent_at DESC LIMIT ?
                    )
                    """,
                    (keep_last_n,)
                )
                affected = cur.rowcount
            conn.commit()
            return True, f"Purged {affected} audit log record(s).", affected
        except Exception as e:
            return False, f"Failed to clear audit logs: {str(e)}", 0
        finally:
            conn.close()

    @staticmethod
    def clean_import_from_file(
        uploaded_file,
        replace_mode: bool = False,
        default_operator: str = "Telkomcel"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Parses an uploaded .xlsx or .csv file and imports sites into timor_sites_100.
        Supports:
        - replace_mode=True: Wipes existing sites for the specified operator before importing.
        - replace_mode=False: Upserts sites (updates matching site_id, inserts new site_id).
        """
        try:
            filename = getattr(uploaded_file, "name", "upload.xlsx").lower()
            if filename.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                xl = pd.ExcelFile(uploaded_file)
                # Try finding Timor site sheet, otherwise pick first sheet
                target_sheet = None
                for sheet in xl.sheet_names:
                    if "timor" in sheet.lower() or "site" in sheet.lower():
                        target_sheet = sheet
                        break
                if not target_sheet:
                    target_sheet = xl.sheet_names[0]
                df = xl.parse(target_sheet)

            if df.empty:
                return False, "Uploaded file contains no data rows.", {}

            # Normalize column headers (strip spaces, lowercase, remove underscores/dashes)
            col_map = {}
            for col in df.columns:
                norm = str(col).strip().lower().replace(" ", "_").replace("-", "_")
                col_map[norm] = col

            if "site_id" not in col_map:
                return False, "File must contain a 'site_id' column header.", {}

            stats = {"inserted": 0, "updated": 0, "total_rows": len(df)}

            conn = get_connection()
            cur = conn.cursor()

            if replace_mode:
                if default_operator == "All":
                    cur.execute("DELETE FROM timor_sites_100")
                else:
                    cur.execute("DELETE FROM timor_sites_100 WHERE operator = ?", (default_operator,))
                conn.commit()

            cur.execute("SELECT site_id FROM timor_sites_100")
            existing_site_ids = {row[0] for row in cur.fetchall()}

            now_iso = datetime.now().isoformat()

            for idx, (_, row) in enumerate(df.iterrows(), start=1):
                raw_id = row.get(col_map.get("site_id"))
                if pd.isna(raw_id) or not str(raw_id).strip():
                    continue
                site_id = str(raw_id).strip()

                def _get(field, default):
                    if field in col_map and not pd.isna(row.get(col_map[field])):
                        return row.get(col_map[field])
                    return default

                site_name = str(_get("site_name", f"Site {site_id}"))
                district = str(_get("district", "Dili"))
                site_type = str(_get("site_type", "Macro Tower"))
                rectifier = str(_get("rectifier", "HARIF"))
                try:
                    backup_hours = float(_get("backup_hours", 2.0))
                except Exception:
                    backup_hours = 2.0
                revenue_tier = str(_get("revenue_tier", "Gold"))
                quadrant = str(_get("quadrant", "Q1-Critical"))
                has_dg = str(_get("has_dg", "No DG"))
                program = str(_get("program", "PaaS Rollout"))
                try:
                    lon = float(_get("lon", 125.5736))
                    lat = float(_get("lat", -8.5568))
                except Exception:
                    lon = 125.5736
                    lat = -8.5568
                notes = str(_get("notes", ""))
                try:
                    route_km = float(_get("accessible_route_km", 25.0))
                except Exception:
                    route_km = 25.0
                transport_mode = str(_get("transport_mode", "4x4 Operational Fleet"))
                est_time = str(_get("est_travel_time", "1.0 - 2.0 hrs"))
                hub = str(_get("assigned_forward_hub", "Dili Central Hub"))
                zone = str(_get("deployment_zone", "Zone 1"))
                wave = str(_get("delivery_wave", "Wave 1"))
                try:
                    p_idx = float(_get("priority_index", 50.0))
                except Exception:
                    p_idx = 50.0
                p_tier = str(_get("priority_tier", "Tier 1 Priority"))
                readiness = str(_get("readiness_gate", "GO (Dispatch Ready)"))
                paas_st = str(_get("paas_status", "Shipping & Customs"))
                op = str(_get("operator", default_operator if default_operator != "All" else "Telkomcel"))
                is_ext = int(_get("is_extreme", 0))

                if site_id in existing_site_ids and not replace_mode:
                    cur.execute("""
                        UPDATE timor_sites_100
                        SET site_name = ?, district = ?, site_type = ?, rectifier = ?, backup_hours = ?,
                            revenue_tier = ?, quadrant = ?, has_dg = ?, program = ?, lon = ?, lat = ?,
                            notes = ?, accessible_route_km = ?, transport_mode = ?, est_travel_time = ?,
                            assigned_forward_hub = ?, deployment_zone = ?, delivery_wave = ?,
                            priority_index = ?, priority_tier = ?, readiness_gate = ?, paas_status = ?,
                            operator = ?, is_extreme = ?, updated_at = ?, last_updated_by = 'Clean File Import'
                        WHERE site_id = ?
                    """, (
                        site_name, district, site_type, rectifier, backup_hours,
                        revenue_tier, quadrant, has_dg, program, lon, lat,
                        notes, route_km, transport_mode, est_time,
                        hub, zone, wave, p_idx, p_tier, readiness, paas_st,
                        op, is_ext, now_iso, site_id
                    ))
                    stats["updated"] += 1
                else:
                    cur.execute("""
                        INSERT INTO timor_sites_100 (
                            no, site_id, site_name, district, site_type, rectifier, backup_hours,
                            revenue_tier, quadrant, has_dg, program, lon, lat, notes,
                            haversine_distance_km, accessible_route_km, transport_mode, est_travel_time,
                            assigned_forward_hub, deployment_zone, delivery_wave, priority_index,
                            priority_tier, readiness_gate, paas_status, operator, is_extreme,
                            updated_at, last_updated_by
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?, ?,
                            ?, ?
                        )
                    """, (
                        idx, site_id, site_name, district, site_type, rectifier, backup_hours,
                        revenue_tier, quadrant, has_dg, program, lon, lat, notes,
                        route_km * 0.8, route_km, transport_mode, est_time,
                        hub, zone, wave, p_idx,
                        p_tier, readiness, paas_st, op, is_ext,
                        now_iso, 'Clean File Import'
                    ))
                    existing_site_ids.add(site_id)
                    stats["inserted"] += 1

            conn.commit()

            # Audit record
            cur.execute(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "DataManagement",
                    "Admin",
                    "CLEAN_FILE_IMPORT",
                    f"Processed {stats['total_rows']} rows: {stats['inserted']} inserted, {stats['updated']} updated (replace_mode={replace_mode})",
                    "SUCCESS"
                )
            )
            conn.commit()

            mode_text = "Replaced all records and imported" if replace_mode else "Synchronized"
            msg = f"{mode_text} {stats['inserted']} new sites and updated {stats['updated']} existing sites successfully."
            return True, msg, stats
        except Exception as e:
            return False, f"Import failed: {str(e)}", {}
        finally:
            if 'conn' in locals() and conn:
                conn.close()
