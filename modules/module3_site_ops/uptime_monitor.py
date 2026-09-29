"""
Module 3: Site Availability Uptime Monitor & Emergency Outage Detector.
Ensures site availability meets or exceeds mandatory 95.0% threshold.
Flags outages > 15 mins for emergency push alert dispatch.
"""
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
from database.connection import query_df, execute_write
from config.settings import OperationalThresholds
from services.notification_service import NotificationDispatcher

class UptimeMonitor:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.thresholds = OperationalThresholds()
        self.dispatcher = NotificationDispatcher(db_path=self.db_path)

    def get_sites_status(self) -> pd.DataFrame:
        """Retrieves all monitored sites with current status and uptime %."""
        sql = "SELECT * FROM tower_sites ORDER BY uptime_percent ASC"
        return query_df(sql, db_path=self.db_path)

    def get_uptime_summary(self) -> Dict[str, Any]:
        """Calculates nationwide network availability and breach alerts."""
        df = self.get_sites_status()
        if df.empty:
            return {
                "average_uptime": 99.5,
                "total_sites": 0,
                "online_sites": 0,
                "degraded_sites": 0,
                "down_sites": 0,
                "sla_compliant": True,
                "sla_threshold": self.thresholds.SITE_AVAILABILITY_MIN_PERCENT
            }

        avg_uptime = float(df["uptime_percent"].mean())
        total_sites = len(df)
        online_sites = len(df[df["current_status"] == "ONLINE"])
        degraded_sites = len(df[df["current_status"] == "DEGRADED"])
        down_sites = len(df[df["current_status"] == "DOWN"])

        sla_compliant = avg_uptime >= self.thresholds.SITE_AVAILABILITY_MIN_PERCENT

        return {
            "average_uptime": round(avg_uptime, 2),
            "total_sites": total_sites,
            "online_sites": online_sites,
            "degraded_sites": degraded_sites,
            "down_sites": down_sites,
            "sla_compliant": sla_compliant,
            "sla_threshold": self.thresholds.SITE_AVAILABILITY_MIN_PERCENT
        }

    def get_active_incidents(self) -> pd.DataFrame:
        """Returns incidents, highlighting those down > 15 minutes."""
        sql = """
            SELECT i.*, s.site_name, s.region
            FROM site_incidents i
            JOIN tower_sites s ON i.site_id = s.site_id
            ORDER BY i.incident_start DESC
        """
        return query_df(sql, db_path=self.db_path)

    def trigger_emergency_check(self) -> List[Dict[str, Any]]:
        """
        Scans all unresolved incidents. If downtime > 15 minutes and alert not yet sent,
        triggers Telegram / WhatsApp notification immediately.
        """
        sql = """
            SELECT i.*, s.site_name
            FROM site_incidents i
            JOIN tower_sites s ON i.site_id = s.site_id
            WHERE i.resolved = 0 AND i.duration_minutes >= ? AND i.emergency_alert_sent = 0
        """
        df_triggers = query_df(sql, (self.thresholds.EMERGENCY_OUTAGE_TRIGGER_MINUTES,), db_path=self.db_path)
        dispatched = []

        for _, row in df_triggers.iterrows():
            inc_id = row["id"]
            res = self.dispatcher.dispatch_emergency_outage(
                site_id=row["site_id"],
                site_name=row["site_name"],
                duration_mins=row["duration_minutes"],
                root_cause=row["root_cause"] or "Unspecified site transmission drop"
            )
            # Mark alert sent
            execute_write(
                "UPDATE site_incidents SET emergency_alert_sent = 1 WHERE id = ?",
                (inc_id,),
                db_path=self.db_path
            )
            dispatched.append({"incident_id": inc_id, "site_id": row["site_id"], "dispatch_result": res})

        return dispatched
