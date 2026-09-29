"""
Module 1: Competitor Intelligence Hub & Supplier Cost Pushback Calculator.
"""
from typing import Dict, Any, List
import pandas as pd
from database.connection import query_df, execute_write

class CompetitorHub:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_all_intelligence(self) -> pd.DataFrame:
        """Returns all competitor intelligence data with price variance delta."""
        sql = "SELECT * FROM competitor_intelligence ORDER BY quote_date DESC"
        df = query_df(sql, db_path=self.db_path)
        if df.empty:
            return df

        # Calculate potential pushback savings %
        savings_pct_list = []
        for _, row in df.iterrows():
            target = row["samvad_target_price_usd"] or row["quoted_unit_price_usd"]
            quoted = row["quoted_unit_price_usd"]
            if quoted > 0:
                pct = ((quoted - target) / quoted) * 100.0
            else:
                pct = 0.0
            savings_pct_list.append(round(pct, 1))

        df["potential_pushback_pct"] = savings_pct_list
        return df

    def add_intelligence(self, data: Dict[str, Any]) -> int:
        """Adds a new competitor quote record."""
        sql = """
            INSERT INTO competitor_intelligence 
            (competitor_name, product_category, model_or_part_number, technical_specs,
             quoted_unit_price_usd, samvad_target_price_usd, quote_date, source_reference, negotiation_tactics_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["competitor_name"],
            data["product_category"],
            data["model_or_part_number"],
            data.get("technical_specs", ""),
            data["quoted_unit_price_usd"],
            data.get("samvad_target_price_usd", data["quoted_unit_price_usd"] * 0.88),
            data["quote_date"],
            data.get("source_reference", ""),
            data.get("negotiation_tactics_notes", "")
        )
        return execute_write(sql, params, db_path=self.db_path)

    def calculate_cost_pushback_matrix(self, vendor_quote_usd: float, competitor_benchmark_usd: float, quantity: int = 1) -> Dict[str, Any]:
        """
        Calculates negotiation leverage and expected cost reduction.
        """
        variance_usd = vendor_quote_usd - competitor_benchmark_usd
        variance_pct = (variance_usd / vendor_quote_usd) * 100.0 if vendor_quote_usd > 0 else 0.0
        total_potential_savings_usd = variance_usd * quantity

        if variance_pct > 15.0:
            posture = "AGGRESSIVE PUSHBACK (Target >= 12% Discount)"
            talking_point = "Market alternatives offer identical spec at >15% lower price. Demand volume rebate or price match."
        elif variance_pct > 5.0:
            posture = "MODERATE PUSHBACK (Target 5-10% Concession)"
            talking_point = "Benchmarking indicates current pricing is above market median. Request warranty extension or shipping subsidy."
        else:
            posture = "COMPETITIVE (Lock-in Price & Demand Priority SLA)"
            talking_point = "Vendor quote is competitive. Focus negotiation on expedited seaport customs clearance and delivery penalty SLA."

        return {
            "vendor_quote_usd": vendor_quote_usd,
            "competitor_benchmark_usd": competitor_benchmark_usd,
            "unit_delta_usd": round(variance_usd, 2),
            "delta_percentage": round(variance_pct, 2),
            "total_savings_usd": round(total_potential_savings_usd, 2),
            "negotiation_posture": posture,
            "recommended_strategy": talking_point
        }
