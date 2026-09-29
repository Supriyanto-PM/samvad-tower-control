"""
Module 2: Client-Side Margin Optimizer.
Logs CAPEX/OPEX reduction ideas (e.g., site energy efficiency)
implemented at client sites to track gross margin improvement.
"""
from typing import Dict, Any, List
import pandas as pd
from database.connection import query_df, execute_write

class ClientMarginOptimizer:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_all_initiatives(self) -> pd.DataFrame:
        """Fetches all client margin enhancement initiatives."""
        sql = "SELECT * FROM client_margin_initiatives ORDER BY gross_margin_impact_percent DESC"
        return query_df(sql, db_path=self.db_path)

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates total capex savings, annual opex savings, and cumulative gross margin improvement."""
        df = self.get_all_initiatives()
        if df.empty:
            return {
                "total_capex_savings_idr": 0.0,
                "total_opex_savings_annual_idr": 0.0,
                "cumulative_margin_improvement_pct": 0.0,
                "active_initiatives_count": 0
            }

        return {
            "total_capex_savings_idr": float(df["capex_saving_idr"].sum()),
            "total_opex_savings_annual_idr": float(df["opex_saving_annual_idr"].sum()),
            "cumulative_margin_improvement_pct": round(float(df["gross_margin_impact_percent"].sum()), 2),
            "active_initiatives_count": len(df)
        }

    def log_initiative(self, client_name: str, site_id: str, title: str, category: str, capex: float, opex: float, margin_pct: float, status: str = "In Progress") -> int:
        """Adds a new efficiency initiative."""
        sql = """
            INSERT INTO client_margin_initiatives 
            (client_name, site_id, initiative_title, category, capex_saving_idr, opex_saving_annual_idr, gross_margin_impact_percent, implementation_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return execute_write(sql, (client_name, site_id, title, category, capex, opex, margin_pct, status), db_path=self.db_path)
