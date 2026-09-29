"""
KPI Engine for Samvad PMO Command Center (PMO-CC).
Calculates weighted scores across Category A, B, C, D (25% each)
and maps overall achievement to the maximum 120% Performance Tier.
"""
from typing import Dict, Any
import pandas as pd
from config.settings import KPISpecification, OperationalThresholds
from database.connection import query_df

class KPICalculator:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.specs = KPISpecification()
        self.thresholds = OperationalThresholds()

    def calculate_category_a_score(self) -> Dict[str, Any]:
        """
        Category A: Supply Chain & Customs Guardian (25% Weight)
        Metrics:
        - 0% Logistics delays (B/L shipments meeting commissioning buffers)
        - Active competitor intelligence records for cost pushback
        """
        df_shipments = query_df("SELECT * FROM customs_shipments", db_path=self.db_path)
        df_competitor = query_df("SELECT * FROM competitor_intelligence", db_path=self.db_path)

        total_shipments = len(df_shipments)
        if total_shipments == 0:
            shipment_score = 100.0
        else:
            # RED delays penalized heavily, YELLOW slightly, GREEN 100%
            green_count = len(df_shipments[df_shipments["delay_risk_status"] == "GREEN"])
            yellow_count = len(df_shipments[df_shipments["delay_risk_status"] == "YELLOW"])
            red_count = len(df_shipments[df_shipments["delay_risk_status"] == "RED"])
            
            # Perfect score if all Green. Yellow gives 90%, Red gives 50%
            shipment_score = ((green_count * 1.0) + (yellow_count * 0.90) + (red_count * 0.50)) / total_shipments * 100.0

        # Competitor intelligence bonus (if active records > 2, provide up to 20% stretch bonus)
        comp_count = len(df_competitor)
        intelligence_bonus = min(20.0, comp_count * 5.0)

        raw_score = min(120.0, shipment_score * (1.0 + (intelligence_bonus / 100.0)))
        weighted_score = (raw_score / 100.0) * (self.specs.WEIGHT_CUSTOMS_SUPPLY_CHAIN * 100.0)

        return {
            "category": "A. Supply Chain & Customs Guardian",
            "weight": self.specs.WEIGHT_CUSTOMS_SUPPLY_CHAIN,
            "raw_score": round(raw_score, 2),
            "weighted_score": round(weighted_score, 2),
            "shipment_count": total_shipments,
            "intelligence_records": comp_count,
            "status": "Maximum 120% Stretch" if raw_score >= 115.0 else ("On Target" if raw_score >= 95.0 else "Action Required")
        }

    def calculate_category_b_score(self) -> Dict[str, Any]:
        """
        Category B: SG&A & Manpower Financial Sentinel (25% Weight)
        Metrics:
        - Maintain Year 1 project SG&A < 12.0% of baseline revenue
        - Manpower cost optimizations identified & implemented
        - Client gross margin improvement initiatives
        """
        df_baseline = query_df("SELECT * FROM sga_budget_baseline ORDER BY id DESC LIMIT 1", db_path=self.db_path)
        df_expenses = query_df("SELECT * FROM sga_expenses", db_path=self.db_path)
        df_margin = query_df("SELECT * FROM client_margin_initiatives", db_path=self.db_path)

        if df_baseline.empty:
            revenue = 10000000000.0
            allocated_budget = 1150000000.0
        else:
            revenue = df_baseline.iloc[0]["total_project_revenue"]
            allocated_budget = df_baseline.iloc[0]["allocated_sga_budget"]

        total_expense = df_expenses["amount_idr"].sum() if not df_expenses.empty else 0.0
        sga_ratio = (total_expense / revenue) if revenue > 0 else 0.0

        # Scoring: Target < 12.0%.
        # If SG&A is < 10.0%, eligible for full 120% stretch score!
        if sga_ratio <= 0.08:
            base_score = 120.0
        elif sga_ratio <= 0.10:
            base_score = 110.0
        elif sga_ratio <= 0.12:
            base_score = 100.0
        elif sga_ratio <= 0.14:
            base_score = 80.0
        else:
            base_score = 50.0

        # Margin initiatives impact bonus
        margin_impact_sum = df_margin["gross_margin_impact_percent"].sum() if not df_margin.empty else 0.0
        margin_bonus = min(10.0, margin_impact_sum * 2.0)

        raw_score = min(120.0, base_score + (margin_bonus if base_score >= 100.0 else 0.0))
        weighted_score = (raw_score / 100.0) * (self.specs.WEIGHT_FINANCIAL_SGA * 100.0)

        return {
            "category": "B. SG&A & Manpower Financial Sentinel",
            "weight": self.specs.WEIGHT_FINANCIAL_SGA,
            "raw_score": round(raw_score, 2),
            "weighted_score": round(weighted_score, 2),
            "sga_ratio_percent": round(sga_ratio * 100.0, 2),
            "sga_ceiling_percent": self.thresholds.SGA_MAX_RATIO_TARGET * 100.0,
            "total_expense_idr": total_expense,
            "revenue_baseline_idr": revenue,
            "status": "Within <12% Target (120% Tier)" if raw_score >= 115.0 else ("Compliant (<12%)" if sga_ratio <= 0.12 else "Ceiling Exceeded (>12%)")
        }

    def calculate_category_c_score(self) -> Dict[str, Any]:
        """
        Category C: Site Availability & SLA Operations (25% Weight)
        Metrics:
        - Network site uptime >= 95.0% contract threshold
        - Emergency outage alert resolution (<15 min response)
        - I&C SOP generation compliance
        """
        df_sites = query_df("SELECT * FROM tower_sites", db_path=self.db_path)
        df_incidents = query_df("SELECT * FROM site_incidents", db_path=self.db_path)

        if df_sites.empty:
            avg_uptime = 99.0
        else:
            avg_uptime = df_sites["uptime_percent"].mean()

        # Target is >= 95.0%.
        # >= 99.0% qualifies for 120% stretch tier.
        if avg_uptime >= 99.0:
            raw_score = 120.0
        elif avg_uptime >= 97.0:
            raw_score = 110.0
        elif avg_uptime >= 95.0:
            raw_score = 100.0
        else:
            # Below 95% penalty
            raw_score = max(0.0, (avg_uptime / 95.0) * 80.0)

        weighted_score = (raw_score / 100.0) * (self.specs.WEIGHT_SITE_AVAILABILITY * 100.0)

        return {
            "category": "C. Site Availability & SLA Operations",
            "weight": self.specs.WEIGHT_SITE_AVAILABILITY,
            "raw_score": round(raw_score, 2),
            "weighted_score": round(weighted_score, 2),
            "average_uptime_percent": round(avg_uptime, 2),
            "threshold_percent": self.thresholds.SITE_AVAILABILITY_MIN_PERCENT,
            "status": "Exceeds Mandatory 95% (120% Tier)" if raw_score >= 115.0 else ("Meets SLA (>=95%)" if avg_uptime >= 95.0 else "Breached SLA (<95%)")
        }

    def calculate_category_d_score(self) -> Dict[str, Any]:
        """
        Category D: SLA Reporting & Presales Engine (25% Weight)
        Metrics:
        - Friday 14:00 auto-report generation (100% on-time before 17:00 WIB)
        - POC milestone delivery meeting '5-days ahead' stretch target
        """
        df_poc = query_df("SELECT * FROM poc_milestones", db_path=self.db_path)
        
        if df_poc.empty:
            poc_score = 100.0
        else:
            ahead_count = len(df_poc[df_poc["status"].str.contains("Ahead", case=False, na=False)])
            on_track_count = len(df_poc[df_poc["status"].str.contains("On Track", case=False, na=False)])
            lagging_count = len(df_poc[df_poc["status"].str.contains("Lagging", case=False, na=False)])
            total_poc = len(df_poc)

            # Ahead meets 5-day stretch target -> 120%
            poc_score = ((ahead_count * 1.20) + (on_track_count * 1.00) + (lagging_count * 0.70)) / total_poc * 100.0

        # Reporting compliance baseline is 100%
        raw_score = min(120.0, poc_score)
        weighted_score = (raw_score / 100.0) * (self.specs.WEIGHT_PRESALES_REPORTING * 100.0)

        return {
            "category": "D. SLA Reporting & Presales Engine",
            "weight": self.specs.WEIGHT_PRESALES_REPORTING,
            "raw_score": round(raw_score, 2),
            "weighted_score": round(weighted_score, 2),
            "poc_count": len(df_poc),
            "status": "120% Stretch Tier (5-Days Ahead)" if raw_score >= 115.0 else ("100% On-Time Target" if raw_score >= 95.0 else "Lagging Milestones")
        }

    def get_overall_kpi_summary(self) -> Dict[str, Any]:
        """Aggregates all 4 modules to compute cumulative KPI and performance tier."""
        cat_a = self.calculate_category_a_score()
        cat_b = self.calculate_category_b_score()
        cat_c = self.calculate_category_c_score()
        cat_d = self.calculate_category_d_score()

        overall_weighted_score = cat_a["weighted_score"] + cat_b["weighted_score"] + cat_c["weighted_score"] + cat_d["weighted_score"]
        overall_percentage = overall_weighted_score # Since sum of weights is 1.0

        if overall_percentage >= 115.0:
            tier_label = "Tier 1: Maximum 120% Performance Tier"
            tier_badge = "🌟 MAXIMUM 120%"
            tier_color = "#10B981" # Emerald Green
        elif overall_percentage >= 100.0:
            tier_label = "Tier 2: 100% On-Target Contract Compliance"
            tier_badge = "✅ ON TARGET (100%)"
            tier_color = "#3B82F6" # Blue
        else:
            tier_label = "Tier 3: Below Target (<100%)"
            tier_badge = "⚠️ ACTION REQUIRED"
            tier_color = "#EF4444" # Red

        return {
            "overall_score": round(overall_percentage, 2),
            "tier_label": tier_label,
            "tier_badge": tier_badge,
            "tier_color": tier_color,
            "categories": {
                "category_a": cat_a,
                "category_b": cat_b,
                "category_c": cat_c,
                "category_d": cat_d,
            }
        }
