"""
Module 1: Customs Milestone Tracker & SLA Buffer Alert Logic.
"""
from datetime import datetime, date
from typing import Dict, Any, List
import pandas as pd
from database.connection import query_df, execute_write
from config.settings import OperationalThresholds

class CustomsTracker:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.thresholds = OperationalThresholds()

    def get_all_shipments(self) -> pd.DataFrame:
        """Retrieves all shipments with calculated buffer metrics."""
        sql = "SELECT * FROM customs_shipments ORDER BY eta ASC"
        df = query_df(sql, db_path=self.db_path)
        if df.empty:
            return df

        # Calculate buffer days: project_commissioning_deadline - eta
        today = date.today()
        buffer_days_list = []
        calculated_status = []

        for _, row in df.iterrows():
            try:
                eta_dt = datetime.strptime(row["eta"], "%Y-%m-%d").date()
                deadline_dt = datetime.strptime(row["project_commissioning_deadline"], "%Y-%m-%d").date()
                buffer_days = (deadline_dt - eta_dt).days
            except Exception:
                buffer_days = 0

            buffer_days_list.append(buffer_days)

            # Classify Buffer Status
            if row["current_milestone"] == "Released to Warehouse":
                status = "GREEN"
            elif buffer_days <= self.thresholds.CUSTOMS_DELAY_BUFFER_DAYS_RED:
                status = "RED"
            elif buffer_days <= self.thresholds.CUSTOMS_DELAY_BUFFER_DAYS_YELLOW:
                status = "YELLOW"
            else:
                status = "GREEN"

            calculated_status.append(status)

        df["buffer_days"] = buffer_days_list
        df["calculated_delay_risk"] = calculated_status
        return df

    def add_shipment(self, data: Dict[str, Any]) -> int:
        """Inserts a new international shipment record."""
        # Determine delay risk status
        try:
            eta_dt = datetime.strptime(data["eta"], "%Y-%m-%d").date()
            deadline_dt = datetime.strptime(data["project_commissioning_deadline"], "%Y-%m-%d").date()
            buffer_days = (deadline_dt - eta_dt).days
        except Exception:
            buffer_days = 10

        if buffer_days <= self.thresholds.CUSTOMS_DELAY_BUFFER_DAYS_RED:
            status = "RED"
        elif buffer_days <= self.thresholds.CUSTOMS_DELAY_BUFFER_DAYS_YELLOW:
            status = "YELLOW"
        else:
            status = "GREEN"

        sql = """
            INSERT INTO customs_shipments 
            (bl_number, vendor_name, item_description, port_of_origin, destination_port, ocean_freight_carrier,
             etd, eta, project_commissioning_deadline, current_milestone, customs_channel, delay_risk_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["bl_number"],
            data["vendor_name"],
            data["item_description"],
            data["port_of_origin"],
            data.get("destination_port", "Tanjung Priok, Jakarta"),
            data.get("ocean_freight_carrier", "Ocean Carrier"),
            data["etd"],
            data["eta"],
            data["project_commissioning_deadline"],
            data.get("current_milestone", "Ocean Freight Transit"),
            data.get("customs_channel", "Green"),
            status,
            data.get("notes", "")
        )
        return execute_write(sql, params, db_path=self.db_path)

    def update_milestone(self, bl_number: str, milestone: str, customs_channel: str = "Green", cleared_date: str = None) -> None:
        """Updates shipping clearance milestone and status."""
        sql = """
            UPDATE customs_shipments
            SET current_milestone = ?, customs_channel = ?, cleared_date = ?
            WHERE bl_number = ?
        """
        execute_write(sql, (milestone, customs_channel, cleared_date, bl_number), db_path=self.db_path)
