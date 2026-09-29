"""
Module 2: SG&A Ratio Calculator & Budget Baseline Sentinel.
Enforces project-level SG&A below 12.0% in Year 1.
"""
from typing import Dict, Any, List
import pandas as pd
from database.connection import query_df, execute_write
from config.settings import OperationalThresholds

class SGACalculator:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.thresholds = OperationalThresholds()

    def get_budget_baseline(self) -> Dict[str, Any]:
        """Fetches the project revenue and SG&A budget ceiling."""
        sql = "SELECT * FROM sga_budget_baseline ORDER BY id DESC LIMIT 1"
        df = query_df(sql, db_path=self.db_path)
        if df.empty:
            return {
                "project_name": "Samvad Nationwide Modernization",
                "total_project_revenue": 10000000000.0,
                "allocated_sga_budget": 1150000000.0,
                "sga_ceiling_percent": 12.0
            }
        return df.iloc[0].to_dict()

    def get_expenses_summary(self) -> Dict[str, Any]:
        """Calculates cumulative spend by category and current SG&A ratio."""
        baseline = self.get_budget_baseline()
        revenue = float(baseline.get("total_project_revenue", 10000000000.0))
        allocated = float(baseline.get("allocated_sga_budget", 1150000000.0))
        ceiling_pct = float(baseline.get("sga_ceiling_percent", 12.0))

        sql = "SELECT * FROM sga_expenses ORDER BY expense_date DESC"
        df_expenses = query_df(sql, db_path=self.db_path)

        total_spent = float(df_expenses["amount_idr"].sum()) if not df_expenses.empty else 0.0
        sga_ratio_pct = (total_spent / revenue * 100.0) if revenue > 0 else 0.0
        remaining_budget = allocated - total_spent

        # Status check
        if sga_ratio_pct > ceiling_pct:
            status = "RED (Ceiling Exceeded)"
            status_desc = f"CRITICAL: Current SG&A ({sga_ratio_pct:.2f}%) exceeds the 12.0% contract ceiling!"
        elif sga_ratio_pct >= self.thresholds.SGA_WARNING_RATIO * 100.0:
            status = "YELLOW (Warning Threshold)"
            status_desc = f"WARNING: SG&A reached {sga_ratio_pct:.2f}%. Enforce strict spend approval."
        else:
            status = "GREEN (Within Target)"
            status_desc = f"HEALTHY: SG&A is {sga_ratio_pct:.2f}%, well below the 12.0% ceiling."

        category_breakdown = {}
        if not df_expenses.empty:
            cat_group = df_expenses.groupby("category")["amount_idr"].sum().to_dict()
            category_breakdown = cat_group

        return {
            "baseline": baseline,
            "total_spent_idr": total_spent,
            "allocated_sga_budget_idr": allocated,
            "remaining_budget_idr": remaining_budget,
            "sga_ratio_pct": round(sga_ratio_pct, 2),
            "sga_ceiling_pct": ceiling_pct,
            "status": status,
            "status_desc": status_desc,
            "category_breakdown": category_breakdown,
            "expenses_df": df_expenses
        }

    def log_expense(self, expense_date: str, category: str, description: str, amount_idr: float, site_id: str = None) -> int:
        """Adds a new SG&A expense record."""
        sql = """
            INSERT INTO sga_expenses (expense_date, category, description, amount_idr, site_id)
            VALUES (?, ?, ?, ?, ?)
        """
        return execute_write(sql, (expense_date, category, description, amount_idr, site_id), db_path=self.db_path)
