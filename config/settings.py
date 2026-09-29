"""
Configuration and KPI specifications for Samvad PMO Command Center (PMO-CC).
Reflects requirements defined in the PMO-CC PRD v1.0.
"""
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class KPISpecification:
    WEIGHT_CUSTOMS_SUPPLY_CHAIN: float = 0.25      # Category A: 25%
    WEIGHT_FINANCIAL_SGA: float = 0.25             # Category B: 25%
    WEIGHT_SITE_AVAILABILITY: float = 0.25         # Category C: 25%
    WEIGHT_PRESALES_REPORTING: float = 0.25        # Category D: 25%
    
    TARGET_PERFORMANCE_TIER: float = 1.20          # 120% Maximum Performance Tier
    NORMAL_PERFORMANCE_TIER: float = 1.00          # 100% On-target

@dataclass(frozen=True)
class OperationalThresholds:
    # Module 1: Customs & Logistics
    CUSTOMS_DELAY_BUFFER_DAYS_YELLOW: int = 5       # Buffer <= 5 days -> Yellow
    CUSTOMS_DELAY_BUFFER_DAYS_RED: int = 2          # Buffer <= 2 days -> Red Alert
    
    # Module 2: SG&A Financial Discipline
    SGA_MAX_RATIO_TARGET: float = 0.12             # Year 1 project SG&A < 12.0%
    SGA_WARNING_RATIO: float = 0.10                # 10.0% warning threshold
    
    # Module 3: Site SLA & Operations
    SITE_AVAILABILITY_MIN_PERCENT: float = 95.0    # Mandatory >= 95.0%
    EMERGENCY_OUTAGE_TRIGGER_MINUTES: int = 15     # Push notification triggered if down > 15 mins
    
    # Module 4: SLA Reporting & Presales
    FRIDAY_REPORT_AUTO_RUN_HOUR: int = 14          # Friday 14:00 WIB auto-reporter
    FRIDAY_REPORT_DEADLINE_HOUR: int = 17          # Friday 17:00 WIB contract deadline
    POC_STRETCH_TARGET_DAYS_AHEAD: int = 5         # '5-days ahead' stretch target

# App Branding & Meta
APP_TITLE = "Samvad PMO Command Center"
APP_SUBTITLE = "Operational Automation & KPI Alignment Platform"
VERSION = "1.0.0"
COMPANY_NAME = "PT Samvad Technology Services"
DOCUMENT_OWNER = "Supriyanto (PMO Lead)"

# Database Configuration
DATABASE_PATH = "database/pmo_command_center.db"

# Notification Settings
DEFAULT_TELEGRAM_ENABLED = False
DEFAULT_WHATSAPP_ENABLED = False
