"""
Module 4: POC Gantt & Milestone Tracker.
Traces technical presentations and pilot setups,
flagging items lagging behind the contract's '5-days ahead' stretch target.
"""
from typing import Dict, Any, List
from datetime import datetime, date, timedelta
import pandas as pd
from database.connection import query_df, execute_write
from config.settings import OperationalThresholds

class POCTracker:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.thresholds = OperationalThresholds()

    def get_all_poc_milestones(self) -> pd.DataFrame:
        """
        Retrieves all POC milestones with stretch target verification:
        Checks whether milestone is on track for '5-days ahead' stretch deadline.
        """
        sql = "SELECT * FROM poc_milestones ORDER BY target_deadline ASC"
        df = query_df(sql, db_path=self.db_path)
        if df.empty:
            return df

        today = date.today()
        stretch_eval = []
        days_ahead_list = []

        for _, row in df.iterrows():
            target_dt = datetime.strptime(row["target_deadline"], "%Y-%m-%d").date()
            stretch_target_dt = datetime.strptime(row["stretch_target_deadline"], "%Y-%m-%d").date()

            if row["actual_completion_date"]:
                actual_dt = datetime.strptime(row["actual_completion_date"], "%Y-%m-%d").date()
                delta_days = (target_dt - actual_dt).days
                days_ahead_list.append(delta_days)
                if delta_days >= self.thresholds.POC_STRETCH_TARGET_DAYS_AHEAD:
                    stretch_eval.append("🌟 5-Day Ahead Stretch Met")
                else:
                    stretch_eval.append("✅ Met On Schedule")
            else:
                delta_days = (stretch_target_dt - today).days
                days_ahead_list.append(delta_days)
                if delta_days >= 0:
                    stretch_eval.append("⚡ Ahead / On Pace for Stretch")
                elif (target_dt - today).days >= 0:
                    stretch_eval.append("🟡 Standard Pace (Stretch at Risk)")
                else:
                    stretch_eval.append("🔴 Lagging Behind Contract Target")

        df["days_buffer_or_ahead"] = days_ahead_list
        df["stretch_status_evaluated"] = stretch_eval
        return df

    def add_poc_milestone(self, data: Dict[str, Any]) -> int:
        """Adds a new presales POC milestone with auto-calculated 5-day stretch target."""
        target_dt = datetime.strptime(data["target_deadline"], "%Y-%m-%d").date()
        stretch_target_dt = target_dt - timedelta(days=self.thresholds.POC_STRETCH_TARGET_DAYS_AHEAD)

        sql = """
            INSERT INTO poc_milestones 
            (poc_code, client_name, poc_scope, lead_presales_engineer, milestone_name, target_deadline, stretch_target_deadline, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return execute_write(
            sql,
            (
                data["poc_code"],
                data["client_name"],
                data["poc_scope"],
                data["lead_presales_engineer"],
                data["milestone_name"],
                data["target_deadline"],
                stretch_target_dt.isoformat(),
                data.get("status", "On Track"),
                data.get("notes", "")
            ),
            db_path=self.db_path
        )
