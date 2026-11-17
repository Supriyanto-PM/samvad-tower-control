"""
Module 2: Manpower Cost Optimizer.
Cross-references field engineer visits with daily rates,
highlighting high-utilization resources for transition to fixed monthly retainer packages.
"""
from typing import Dict, Any, List
import pandas as pd
from database.connection import query_df, execute_write

class ManpowerOptimizer:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def audit_engineer_utilization(self) -> pd.DataFrame:
        """
        Audits all engineers, calculating:
        - Total visit days
        - Incurred daily rate cost
        - Monthly retainer cost
        - Optimization recommendation and potential savings
        """
        sql_engineers = "SELECT * FROM field_engineers"
        sql_visits = "SELECT * FROM engineer_visits"

        df_eng = query_df(sql_engineers, db_path=self.db_path)
        df_vis = query_df(sql_visits, db_path=self.db_path)

        if df_eng.empty:
            return pd.DataFrame()

        results = []
        for _, eng in df_eng.iterrows():
            eng_id = eng["engineer_id"]
            eng_name = eng["name"]
            spec = eng["specialization"]
            c_type = eng["contract_type"]
            daily_rate = float(eng["daily_rate_idr"])
            retainer_rate = float(eng["fixed_monthly_rate_idr"])

            vis_rows = df_vis[df_vis["engineer_id"] == eng_id]
            total_days = vis_rows["duration_days"].sum() if not vis_rows.empty else 0
            visit_count = len(vis_rows)

            daily_cost_equivalent = total_days * daily_rate

            # Recommendation logic:
            # If daily cost exceeds fixed retainer, engineer should transition to retainer!
            if c_type == "Daily Rate":
                if daily_cost_equivalent > retainer_rate:
                    potential_saving = daily_cost_equivalent - retainer_rate
                    recommendation = "CONVERT TO RETAINER (High Savings)"
                    status_flag = "OVER_BUDGET_DAILY"
                elif total_days >= 12:
                    potential_saving = 0.0
                    recommendation = "Monitor (Approaching Retainer Threshold)"
                    status_flag = "WATCH"
                else:
                    potential_saving = 0.0
                    recommendation = "Maintain Daily Rate (Low Frequency)"
                    status_flag = "OPTIMAL_DAILY"
            else:
                # Already on retainer
                actual_saving_vs_daily = max(0.0, daily_cost_equivalent - retainer_rate)
                recommendation = f"On Fixed Retainer (Saves IDR {actual_saving_vs_daily:,.0f}/mo)"
                potential_saving = actual_saving_vs_daily
                status_flag = "OPTIMAL_RETAINER"

            results.append({
                "engineer_id": eng_id,
                "name": eng_name,
                "specialization": spec,
                "current_contract": c_type,
                "total_visit_days": total_days,
                "visit_count": visit_count,
                "daily_rate_idr": daily_rate,
                "monthly_retainer_idr": retainer_rate,
                "daily_cost_equivalent_idr": daily_cost_equivalent,
                "potential_saving_idr": potential_saving,
                "recommendation": recommendation,
                "status_flag": status_flag
            })

        return pd.DataFrame(results)

    def log_visit(self, engineer_id: str, site_id: str, visit_date: str, duration_days: int, task_description: str) -> int:
        """Logs a site intervention visit."""
        sql = """
            INSERT INTO engineer_visits (engineer_id, site_id, visit_date, duration_days, task_description)
            VALUES (?, ?, ?, ?, ?)
        """
        return execute_write(sql, (engineer_id, site_id, visit_date, duration_days, task_description), db_path=self.db_path)
