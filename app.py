"""
Samvad PMO & NOC Operations Command Center.
100-Site Timor-Leste National Rollout | RAID-led Prioritization, Territorial Routing & Execution Waves.
Origin Starting Point: Port Dili Terminal (Lat: -8.5520, Lon: 125.5711).
"""
import os
import re
from typing import Any, List, Dict, Optional
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import base64
import textwrap
from datetime import datetime, date

# Enterprise NOC Typography: Set Inter across all Plotly figures globally
for _tmpl in ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", "simple_white"]:
    if _tmpl in pio.templates:
        pio.templates[_tmpl].layout.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


from config.settings import (
    APP_TITLE,
    APP_SUBTITLE,
    VERSION,
    COMPANY_NAME,
    DOCUMENT_OWNER,
    DATABASE_PATH
)
from database.connection import init_db, query_df, execute_write, get_connection, ensure_governance_schema
from database.seed_data import seed_all_data
from database.timor_sites_data import seed_timor_100_sites, PORT_DILI_COORDS, get_timor_100_sites_dataframe
from database.multi_tenant_data import (
    seed_multi_tenant_sites,
    BELAWAN_PORT_COORDS,
    TANJUNG_PERAK_COORDS,
    BALIKPAPAN_PORT_COORDS
)
from services.kpi_engine import KPICalculator
from services.excel_sync_service import ExcelSyncService
from services.data_management_service import DataManagementService
from services.rollout_operations_service import RolloutOperationsService
from services.fleet_tracking_service import FleetTrackingService
from services.notification_service import NotificationDispatcher
from services.mobile_checkin_handler import attach_mobile_checkin_routes
from services.noc_integration_service import NocIntegrationService

# Attach standalone mobile checkin handler directly to Tornado server
attach_mobile_checkin_routes()
from modules.module1_customs.ui import render_module1
from modules.module2_sga.ui import render_module2
from modules.module3_site_ops.ui import render_module3
from modules.module4_reporting.ui import render_module4

@st.cache_data
def get_base64_image(image_path: str) -> str:
    """Reads and base64-encodes an image file for inline HTML embedding."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
def clean_status(text) -> str:
    """Strips emoji icons and unicode markers for professional enterprise typography."""
    if not text:
        return ""
    clean = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27ff]', '', str(text))
    return clean.strip(" \t\n\r•-")


# Streamlit Page Setup
st.set_page_config(
    page_title="SAMVAD PMO CC",
    page_icon="assets/samvad_icon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Enterprise OpManager-Style NOC Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

    /* =========================================================================
       ENTERPRISE NOC TYPOGRAPHY SYSTEM (Powered by Inter & JetBrains Mono)
       Eliminates generic AI/Streamlit default fonts while strictly protecting icon fonts
       ========================================================================= */
    :root {
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        --font-mono: 'JetBrains Mono', 'SF Mono', Menlo, Monaco, Consolas, monospace;
    }

    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > section.main,
    .main .block-container,
    p, a, label, li, ul, ol,
    button, input, select, textarea,
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span:not([data-testid="stIconMaterial"]):not([class*="material"]):not([translate="no"]):not([class*="ejhh0er0"]):not([class*="e1t4gh342"]),
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] a,
    [data-testid="stText"],
    [data-testid="stCaptionContainer"],
    [data-testid="stMetric"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"],
    [data-testid="stMetricDelta"],
    [data-testid="stAlert"],
    [data-baseweb="button"],
    [data-baseweb="select"],
    [data-baseweb="input"],
    [data-baseweb="tag"],
    [data-baseweb="tab"],
    [data-baseweb="popover"],
    [data-baseweb="base-input"],
    .stSelectbox, .stTextInput, .stNumberInput, .stTextArea,
    .stButton, .stButton button,
    .stTabs, [data-testid="stTabs"] button,
    .stDataFrame, div[data-testid="stTable"],
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader summary {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: optimizeLegibility !important;
    }

    /* =========================================================================
       CRITICAL: PRESERVE STREAMLIT MATERIAL ICONS & LIGATURES
       Prevents 'keyboard_arrow_right' and other icon ligatures from rendering
       as raw text overlapping on expanders, buttons, and popovers.
       ========================================================================= */
    [data-testid="stIconMaterial"],
    [data-testid*="IconMaterial"],
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpanderToggleIcon"] *,
    [class*="material-symbols"],
    [class*="material-icons"],
    [class*="ejhh0er0"],
    [class*="e1t4gh342"],
    span[translate="no"],
    .stIcon,
    details summary span[data-testid="stIconMaterial"],
    details summary span[translate="no"],
    details summary [class*="ejhh0er0"],
    details summary [class*="e1t4gh342"] {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-style: normal !important;
        font-weight: 400 !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-flex !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' 1 !important;
        font-feature-settings: 'liga' 1 !important;
        -webkit-font-smoothing: antialiased !important;
    }

    /* Prevent expander toggle icon container from overflowing into adjacent labels */
    details[data-testid="stExpander"] summary span[class*="e1t4gh342"],
    details[data-testid="stExpander"] summary span[data-testid="stExpanderToggleIcon"],
    details summary span[class*="e1t4gh342"] {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-width: 1.5rem !important;
        max-width: 1.5rem !important;
        overflow: hidden !important;
        flex-shrink: 0 !important;
        margin-right: 0.5rem !important;
    }

    /* Tabular figures for all numbers, tables, metrics, and KPI readouts (NOC Standard) */
    [data-testid="stMetricValue"],
    .stMetric,
    table, th, td,
    .stDataFrame,
    div[class*="metric"],
    div[class*="kpi"],
    div[class*="stat"],
    span[class*="stat"],
    .st-key-top_ribbon span {
        font-variant-numeric: tabular-nums !important;
        font-feature-settings: "cv02", "cv03", "cv04", "cv11", "tnum" !important;
    }

    /* Dedicated Telemetry / Monospace Font for Site IDs, Coordinates, Codes, and Logs */
    code, pre, kbd, samp,
    .telemetry-code,
    div[class*="mono"],
    span[class*="mono"] {
        font-family: 'JetBrains Mono', 'SF Mono', Menlo, Monaco, Consolas, monospace !important;
        font-size: 0.9em !important;
        letter-spacing: -0.03em !important;
    }

    /* Completely hide sidebar and collapse controls */
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Hide default Streamlit top header bar, toolbar, and decoration */
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Eliminate Streamlit's default stale-element dimming and ghosting ("membayang") */
    [data-stale="true"],
    .stElementContainer[data-stale="true"],
    div[data-testid="stVerticalBlock"][data-stale="true"],
    div[data-testid="stAppViewContainer"][data-stale="true"],
    .main[data-stale="true"] {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    div[data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Zero out all top spacing from Streamlit app hierarchy */
    html, body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > section.main,
    .main {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Fixed 100% full-width top ribbon bar container — Docks directly at pixel 0 */
    .st-key-top_ribbon,
    div[class*="st-key-top_ribbon"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
        height: 48px !important;
        background: #1E2229 !important;
        z-index: 999999 !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.28) !important;
        padding: 9px 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .st-key-top_ribbon [data-testid="stVerticalBlock"],
    div[class*="st-key-top_ribbon"] [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        height: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        gap: 0 !important;
    }

    .st-key-top_ribbon [data-testid="stHorizontalBlock"],
    div[class*="st-key-top_ribbon"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        height: 30px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .st-key-top_ribbon [data-testid="stElementContainer"],
    div[class*="st-key-top_ribbon"] [data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        height: 30px !important;
    }

    .st-key-top_ribbon [data-testid="stColumn"],
    div[class*="st-key-top_ribbon"] [data-testid="stColumn"] {
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        height: 30px !important;
    }

    .st-key-top_ribbon [data-testid="stMarkdownContainer"],
    div[class*="st-key-top_ribbon"] [data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        height: 30px !important;
        width: 100% !important;
    }

    .st-key-top_ribbon [data-testid="stButton"],
    div[class*="st-key-top_ribbon"] [data-testid="stButton"] {
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        height: 30px !important;
        width: 100% !important;
    }

    /* Maximize main content container width & provide exact offset under fixed ribbon */
    .main .block-container {
        max-width: 100% !important;
        padding-top: 56px !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
        padding-bottom: 2rem !important;
    }

    /* OpManager Enterprise Light Grey Canvas with Inter Typography */
    .stApp {
        background-color: #F1F3F6;
        color: #1E293B;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        letter-spacing: -0.011em;
    }
    
    /* Segmented Control / Button Group Styling for OpManager Dark Ribbon */
    .st-key-top_ribbon [data-testid="stButtonGroup"],
    div[class*="st-key-top_ribbon"] [data-testid="stButtonGroup"],
    .st-key-top_ribbon [data-baseweb="button-group"],
    div[class*="st-key-top_ribbon"] [data-baseweb="button-group"],
    .st-key-top_ribbon [data-testid="stSegmentedControl"],
    div[class*="st-key-top_ribbon"] [data-testid="stSegmentedControl"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 auto !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    .st-key-top_ribbon [data-testid="stButtonGroup"] > div,
    div[class*="st-key-top_ribbon"] [data-testid="stButtonGroup"] > div,
    .st-key-top_ribbon [data-baseweb="button-group"] {
        background: transparent !important;
        border: none !important;
        gap: 4px !important;
        padding: 0 !important;
        align-items: center !important;
        justify-content: center !important;
        flex-wrap: nowrap !important;
        margin: 0 auto !important;
    }

    /* Target the 3 columns of top ribbon: Left logo, Center menu, Right metadata */
    div[class*="st-key-top_ribbon"] [data-testid="stColumn"]:first-child {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
    }
    div[class*="st-key-top_ribbon"] [data-testid="stColumn"]:nth-child(2) {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    div[class*="st-key-top_ribbon"] [data-testid="stColumn"]:last-child {
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
    }

    /* ALL Inactive Ribbon Buttons: Exact 30px Height, Crisp Padding, Consistent Radius */
    .st-key-top_ribbon button,
    div[class*="st-key-top_ribbon"] button,
    div[class*="st-key-ribbon_nav"] button,
    div[class*="st-key-btn_ribbon_portal"] button,
    .st-key-top_ribbon [data-testid="stButtonGroup"] button,
    div[class*="st-key-top_ribbon"] [data-testid="stButtonGroup"] button,
    .st-key-top_ribbon [data-baseweb="button-group"] button,
    div[class*="st-key-top_ribbon"] [data-baseweb="button-group"] button {
        background-color: rgba(255, 255, 255, 0.04) !important;
        color: #94A3B8 !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 4px !important;
        font-size: 0.79rem !important;
        font-weight: 500 !important;
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        padding: 0 9px !important;
        margin: 0 !important;
        outline: none !important;
        box-shadow: none !important;
        transition: all 0.12s ease-in-out !important;
        white-space: nowrap !important;
        cursor: pointer !important;
        box-sizing: border-box !important;
        line-height: 1 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        overflow: visible !important;
    }

    /* Force inactive inner text to muted grey with no truncation */
    .st-key-top_ribbon button *,
    div[class*="st-key-top_ribbon"] button *,
    div[class*="st-key-ribbon_nav"] button *,
    div[class*="st-key-btn_ribbon_portal"] button *,
    .st-key-top_ribbon [data-testid="stButtonGroup"] button *,
    div[class*="st-key-top_ribbon"] [data-testid="stButtonGroup"] button *,
    .st-key-top_ribbon [data-baseweb="button-group"] button *,
    div[class*="st-key-top_ribbon"] [data-baseweb="button-group"] button * {
        color: #94A3B8 !important;
        fill: #94A3B8 !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        text-overflow: clip !important;
        overflow: visible !important;
    }

    /* Hover State for Inactive Buttons */
    .st-key-top_ribbon button:hover,
    div[class*="st-key-top_ribbon"] button:hover,
    div[class*="st-key-ribbon_nav"] button:hover,
    div[class*="st-key-btn_ribbon_portal"] button:hover {
        background-color: rgba(255, 255, 255, 0.09) !important;
        border-color: rgba(255, 255, 255, 0.22) !important;
        color: #F1F5F9 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .st-key-top_ribbon button:hover *,
    div[class*="st-key-top_ribbon"] button:hover *,
    div[class*="st-key-ribbon_nav"] button:hover *,
    div[class*="st-key-btn_ribbon_portal"] button:hover * {
        color: #F1F5F9 !important;
        fill: #F1F5F9 !important;
    }

    /* ACTIVE / SELECTED TAB:
       Soft Light Grey Highlight + Crisp Pure White Text — EXACT 30px Height */
    button[data-testid*="Active"],
    button[data-testid*="segmented_controlActive"],
    button[kind*="Active"],
    div[class*="st-key-top_ribbon"] button[data-testid*="Active"],
    div[class*="st-key-top_ribbon"] button[data-testid*="segmented_controlActive"],
    div[class*="st-key-top_ribbon"] button[kind*="Active"],
    div[class*="st-key-ribbon_nav"] button[data-testid*="Active"],
    div[class*="st-key-ribbon_nav"] button[data-testid*="segmented_controlActive"],
    div[data-testid="stButtonGroup"] button[data-testid*="Active"],
    div[data-testid="stButtonGroup"] button[data-testid*="segmented_controlActive"],
    .st-key-top_ribbon button[aria-checked="true"],
    div[class*="st-key-top_ribbon"] button[aria-checked="true"] {
        background-color: #475569 !important;
        border: 1px solid #64748B !important;
        border-radius: 4px !important;
        outline: none !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: 0.1px !important;
        opacity: 1 !important;
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        padding: 0 9px !important;
        box-sizing: border-box !important;
        line-height: 1 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex-shrink: 0 !important;
        overflow: visible !important;
    }

    /* Active inner elements force pure white */
    button[data-testid*="Active"] *,
    button[data-testid*="segmented_controlActive"] *,
    button[kind*="Active"] *,
    div[class*="st-key-top_ribbon"] button[data-testid*="Active"] *,
    div[class*="st-key-top_ribbon"] button[data-testid*="segmented_controlActive"] *,
    div[class*="st-key-top_ribbon"] button[kind*="Active"] *,
    div[class*="st-key-ribbon_nav"] button[data-testid*="Active"] *,
    div[class*="st-key-ribbon_nav"] button[data-testid*="segmented_controlActive"] *,
    div[data-testid="stButtonGroup"] button[data-testid*="Active"] *,
    div[data-testid="stButtonGroup"] button[data-testid*="segmented_controlActive"] *,
    .st-key-top_ribbon button[aria-checked="true"] *,
    div[class*="st-key-top_ribbon"] button[aria-checked="true"] * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        text-overflow: clip !important;
        overflow: visible !important;
    }

    /* Active Button Hover State */
    button[data-testid*="Active"]:hover,
    div[class*="st-key-top_ribbon"] button[data-testid*="Active"]:hover,
    div[class*="st-key-ribbon_nav"] button[data-testid*="Active"]:hover {
        background-color: #52637A !important;
        border-color: #94A3B8 !important;
    }

    /* ELIMINATE ALL RED FOCUS RINGS / OUTLINES */
    .st-key-top_ribbon button:focus,
    .st-key-top_ribbon button:focus-visible,
    div[class*="st-key-top_ribbon"] button:focus,
    div[class*="st-key-top_ribbon"] button:focus-visible,
    button[data-testid*="Active"]:focus,
    button[data-testid*="Active"]:focus-visible {
        outline: none !important;
        border-color: #64748B !important;
        box-shadow: none !important;
    }
    
    /* Multi-Tenant Operator Dropdown & Header Alignment (Pixel-Perfect Sejajar) */
    .st-key-op_sub_bar_container {
        margin-top: 4px !important;
        margin-bottom: 8px !important;
    }
    .st-key-op_sub_bar_container [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 10px !important;
    }
    .st-key-op_sub_bar_container [data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    .st-key-op_sub_bar_container [data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    .st-key-op_sub_bar_container div[data-testid="stSelectbox"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    .st-key-op_sub_bar_container div[data-testid="stSelectbox"] label {
        display: none !important;
    }

    /* Left: BaseWeb Selectbox (Exactly 40px Height, #CBD5E1 Border) */
    .st-key-op_sub_bar_container div[data-baseweb="select"],
    .st-key-noc_selected_operator div[data-baseweb="select"],
    .st-key-global_operator_select div[data-baseweb="select"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        min-height: 40px !important;
        height: 40px !important;
        max-height: 40px !important;
        box-sizing: border-box !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    .st-key-op_sub_bar_container div[data-baseweb="select"]:hover,
    .st-key-noc_selected_operator div[data-baseweb="select"]:hover,
    .st-key-global_operator_select div[data-baseweb="select"]:hover {
        border-color: #94A3B8 !important;
    }
    .st-key-op_sub_bar_container div[data-baseweb="select"] > div,
    .st-key-noc_selected_operator div[data-baseweb="select"] > div,
    .st-key-global_operator_select div[data-baseweb="select"] > div {
        background: transparent !important;
        border: none !important;
        min-height: 38px !important;
        height: 38px !important;
        max-height: 38px !important;
        box-sizing: border-box !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 10px !important;
        padding-right: 8px !important;
        display: flex !important;
        align-items: center !important;
    }
    .st-key-op_sub_bar_container div[data-baseweb="select"] * {
        font-size: 0.84rem !important;
    }

    /* Right: Sub-Bar (Exactly 40px Height, #CBD5E1 Border, Pixel-Perfect Sejajar) */
    .op-sub-bar {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 0px 14px !important;
        margin: 0 !important;
        min-height: 40px !important;
        height: 40px !important;
        max-height: 40px !important;
        box-sizing: border-box !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }
    .op-breadcrumb {
        font-size: 0.84rem !important;
        color: #64748B !important;
        font-weight: 500 !important;
        display: flex !important;
        align-items: center !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        line-height: 1 !important;
    }
    .op-breadcrumb b {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    .op-active-module-pill {
        display: inline-flex !important;
        align-items: center !important;
        background: #334155 !important;
        color: #F8FAFC !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        padding: 2.5px 8px !important;
        border-radius: 4px !important;
        letter-spacing: 0.4px !important;
        margin-right: 10px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid #475569 !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        line-height: normal !important;
    }
    .op-badge-pill {
        display: inline-flex !important;
        align-items: center !important;
        padding: 3px 10px !important;
        border-radius: 4px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        line-height: normal !important;
    }
    
    /* Clean OpManager Card Container */
    .op-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        height: 100%;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    .op-card-header {
        font-size: 0.90rem;
        font-weight: 700;
        color: #0F172A;
        padding-bottom: 6px;
        margin-bottom: 8px;
        border-bottom: 1px solid #F1F5F9;
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 32px;
        min-height: 32px;
        box-sizing: border-box;
    }
    
    /* Snapshot Table */
    .snapshot-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.81rem;
    }
    .snapshot-table th {
        text-align: left;
        padding: 7px 6px;
        color: #64748B;
        border-bottom: 2px solid #E2E8F0;
        font-weight: 700;
        font-size: 0.73rem;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .snapshot-table td {
        padding: 8px 6px;
        border-bottom: 1px solid #F1F5F9;
        color: #1E293B;
    }
    .snapshot-table tr:hover {
        background-color: #F8FAFC;
    }
    .snapshot-table tfoot td {
        padding: 8px 6px;
        border-top: 2px solid #CBD5E1;
        font-weight: 700;
        background: #F8FAFC;
    }
    
    /* Radar Summary Card */
    .op-radar-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 12px 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Bootstrap Database & Seed 100 Sites
@st.cache_resource
def bootstrap_all_data():
    init_db(DATABASE_PATH)
    ensure_governance_schema()
    seed_all_data(DATABASE_PATH)
    seed_timor_100_sites(DATABASE_PATH)
    seed_multi_tenant_sites(DATABASE_PATH)
    ensure_governance_schema()
    ExcelSyncService.generate_master_template()
    return True

bootstrap_all_data()

def render_top_ribbon():
    """Renders the fixed full-width OpManager dark top ribbon with instantaneous WebSocket navigation."""
    with st.container(key="top_ribbon"):
        col_brand, col_nav, col_meta = st.columns([1.4, 7.2, 1.4], vertical_alignment="center")
        
        with col_brand:
            logo_nav_b64 = get_base64_image("assets/samvad_logo_horizontal_dark.png")
            logo_img = (
                f'<img src="data:image/png;base64,{logo_nav_b64}" height="26" style="vertical-align: middle; margin-right: 9px; flex-shrink: 0;" />'
                if logo_nav_b64
                else '<span style="font-weight: 800; font-size: 1.05rem; color: #FFFFFF;">SAMVAD</span>'
            )
            st.markdown(
                f"""
                <div style="display: inline-flex; align-items: center; white-space: nowrap; height: 30px; line-height: 1; box-sizing: border-box;">
                    {logo_img}
                    <span style="border-left: 1.5px solid rgba(255,255,255,0.22); padding-left: 9px; margin-left: 1px; font-size: 0.84rem; color: #CBD5E1; font-weight: 700; letter-spacing: 0.6px; white-space: nowrap; display: inline-flex; align-items: center; height: 18px;">PMO-CC</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_nav:
            options = [
                "Dashboard",
                "PaaS Rollout",
                "Customs & Logistics",
                "SG&A Finance",
                "Site Operations",
                "Reports",
                "Update & Sync",
                "Settings",
                "Logout"
            ]
            
            slug_map = {
                "dashboard": "Dashboard",
                "paas_rollout": "PaaS Rollout",
                "customs": "Customs & Logistics",
                "sga": "SG&A Finance",
                "site_ops": "Site Operations",
                "reports": "Reports",
                "update": "Update & Sync",
                "settings": "Settings",
                "portal": "Logout",
                "logout": "Logout"
            }
            inv_slug_map = {
                "Dashboard": "dashboard",
                "PaaS Rollout": "paas_rollout",
                "Customs & Logistics": "customs",
                "SG&A Finance": "sga",
                "Site Operations": "site_ops",
                "Reports": "reports",
                "Update & Sync": "update",
                "Settings": "settings"
            }

            # Support programmatic navigation updates before widget instantiation
            if "pending_nav" in st.session_state:
                st.session_state["ribbon_nav"] = st.session_state.pop("pending_nav")
            elif "ribbon_nav" not in st.session_state:
                qp_nav = st.query_params.get("nav", "dashboard")
                st.session_state["ribbon_nav"] = slug_map.get(qp_nav.lower(), "Dashboard")

            selected_nav = st.segmented_control(
                label="Command Navigation",
                options=options,
                key="ribbon_nav",
                label_visibility="collapsed"
            )
            
            if selected_nav == "Logout":
                st.session_state["show_welcome"] = True
                st.session_state["pending_nav"] = "Dashboard"
                st.session_state["last_active_nav"] = "Dashboard"
                st.query_params.clear()
                st.rerun()

            if selected_nav and selected_nav != "Logout":
                st.session_state["last_active_nav"] = selected_nav
                target_slug = inv_slug_map.get(selected_nav, "dashboard")
                if st.query_params.get("nav") != target_slug:
                    st.query_params["nav"] = target_slug

            active_choice = selected_nav or st.session_state.get("last_active_nav", "Dashboard")
            
        with col_meta:
            current_time_str = datetime.now().strftime('%d %b | %H:%M')
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; width: 100%; height: 30px; box-sizing: border-box;">
                    <div style="display: inline-flex; align-items: center; height: 30px; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.10); border-radius: 4px; padding: 0 12px; box-sizing: border-box; white-space: nowrap;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #CBD5E1; font-weight: 600; font-variant-numeric: tabular-nums;">{current_time_str}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    return active_choice


def render_unified_module_header(
    module_label: str,
    breadcrumb_trail: str,
    badge_text: str = "",
    badge_bg: str = "#ECFDF5",
    badge_color: str = "#065F46",
    badge_border: str = "#A7F3D0"
) -> str:
    """
    Renders a unified, pixel-perfect 40px collinear sub-bar header across all 8 modules.
    Col 1 (2.2): Unified Multi-Tenant Operator Selectbox
    Col 2 (7.8): Unified Sub-Bar with Module Pill, Breadcrumb, and Status Badge
    
    Returns:
        selected_operator (str): Currently selected operator ("All", "Telkomcel", "XLSmart", "IOH", "Mitratel")
    """
    operator_options = ["All", "Telkomcel", "XLSmart", "IOH", "Mitratel"]
    
    if "noc_selected_operator" not in st.session_state:
        st.session_state["noc_selected_operator"] = "All"
        
    current_op = st.session_state.get("noc_selected_operator", "All")
    if current_op not in operator_options:
        current_op = "All"
        
    if "global_operator_select" not in st.session_state:
        st.session_state["global_operator_select"] = current_op

    with st.container(key="op_sub_bar_container"):
        sub_col1, sub_col2 = st.columns([2.2, 7.8], vertical_alignment="center")
        with sub_col1:
            selected_operator = st.selectbox(
                "Operator / Client",
                options=operator_options,
                format_func=lambda x: {
                    "All": "All Clients (Unified Portfolio)",
                    "Telkomcel": "Telkomcel",
                    "XLSmart": "XLSmart",
                    "IOH": "IOH",
                    "Mitratel": "Mitratel"
                }.get(x, x),
                key="global_operator_select",
                label_visibility="collapsed"
            )
            st.session_state["noc_selected_operator"] = selected_operator
            
        with sub_col2:
            badge_html = ""
            if badge_text:
                badge_html = f"""
                <div style="flex-shrink: 0; margin-left: 12px;">
                    <span class="op-badge-pill" style="background-color: {badge_bg}; color: {badge_color}; border: 1px solid {badge_border};">
                        {badge_text}
                    </span>
                </div>
                """
            st.markdown(
                f"""
                <div class="op-sub-bar">
                    <div class="op-breadcrumb">
                        <span class="op-active-module-pill">MODULE: {module_label.upper()}</span>
                        <span>{breadcrumb_trail}</span>
                    </div>
                    {badge_html}
                </div>
                """,
                unsafe_allow_html=True
            )
            
    return selected_operator


def render_upcoming_tenant_pipeline(operator_name: str):
    """Renders the Tenant Pre-Rollout & Pipeline Cockpit for upcoming operators (XLSmart, IOH, Mitratel)."""
    
    tenant_profiles = {
        "XLSmart": {
            "name": "XLSmart Telecommunications Alliance",
            "tagline": "XL Axiata & Smartfren Network Modernization - North Sumatra & Aceh",
            "strategy": "Joint Co-Location & Green Power PaaS Rollout across North Sumatra & Aceh Corridors",
            "target_sites": 75,
            "phase": "Candidate Site Scoping & Joint RF/Power Survey (Sumut & Aceh)",
            "msa_status": "Master Service Agreement (MSA) Legal Alignment",
            "sla_target": "99.95% Availability Target (Tier 1 Priority)",
            "power_spec": "Samvad LiFePO4 48V/100Ah + Dual Rectifier Tier-1",
            "color": "#0284C7",
            "candidates": [
                {"id": "XLS-001", "name": "Medan Merdeka Central", "district": "Kota Medan (Sumut)", "tower": "Rooftop 36m", "power": "ELTEK Dual Rectifier", "wave": "Wave 1 (H1 2027)", "status": "Candidate Nominated"},
                {"id": "XLS-002", "name": "Banda Aceh Baiturrahman", "district": "Banda Aceh", "tower": "SST 45m", "power": "HARIF Power Box", "wave": "Wave 1 (H1 2027)", "status": "Candidate Nominated"},
                {"id": "XLS-003", "name": "Berastagi Volcano Ridge", "district": "Karo (Sumut)", "tower": "Guyed Mast 40m", "power": "ELTEK Dual Rectifier", "wave": "Wave 2 (H2 2027)", "status": "Desktop Survey"},
                {"id": "XLS-004", "name": "Lhokseumawe Cunda Hub", "district": "Lhokseumawe (Aceh)", "tower": "SST 52m", "power": "HARIF Power Box", "wave": "Wave 2 (H2 2027)", "status": "Desktop Survey"},
                {"id": "XLS-005", "name": "Sibolga Port Coastal", "district": "Sibolga (Sumut)", "tower": "Monopole 36m", "power": "ELTEK Dual Rectifier", "wave": "Wave 3 (2028)", "status": "Pre-Nomination"},
            ]
        },
        "IOH": {
            "name": "Indosat Ooredoo Hutchison (IOH)",
            "tagline": "Enterprise & Wholesale Power Modernization - Kalimantan & IKN Corridor",
            "strategy": "PaaS Power Modernization & Zero-Diesel Transition across Kalimantan & IKN Nusantara",
            "target_sites": 60,
            "phase": "Pre-Feasibility Audit & Commercial Tariff Alignment",
            "msa_status": "Framework Agreement Drafting in Progress",
            "sla_target": "99.95% Availability Target (MTTR < 4 Hours)",
            "power_spec": "Modular 48V/200Ah Lithium Bank + Smart Rectifier Controller",
            "color": "#8B5CF6",
            "candidates": [
                {"id": "IOH-001", "name": "Balikpapan Semayang Gateway", "district": "Kota Balikpapan", "tower": "Backbone 45m", "power": "Modular LiFePO4 200Ah", "wave": "Wave 1 (H1 2027)", "status": "Joint Survey Ready"},
                {"id": "IOH-002", "name": "IKN Nusantara Core Sepaku", "district": "Penajam Paser Utara", "tower": "Backbone 52m", "power": "ELTEK Dual Rectifier + LiFePO4", "wave": "Wave 1 (H1 2027)", "status": "Engineering Review"},
                {"id": "IOH-003", "name": "Samarinda Mahakam Gateway", "district": "Kota Samarinda", "tower": "Backbone 48m", "power": "HARIF Power Box", "wave": "Wave 2 (H2 2027)", "status": "Joint Survey Ready"},
                {"id": "IOH-004", "name": "Banjarmasin Trisakti Port", "district": "Kota Banjarmasin", "tower": "Backbone 42m", "power": "Modular LiFePO4 200Ah", "wave": "Wave 2 (H2 2027)", "status": "Desktop Audit"},
                {"id": "IOH-005", "name": "Pontianak Dwikora Port", "district": "Kota Pontianak", "tower": "Backbone 45m", "power": "Solar-LiFePO4 Hybrid", "wave": "Wave 3 (2028)", "status": "Candidate Nominated"},
            ]
        },
        "Mitratel": {
            "name": "PT Dayamitra Telekomunikasi Tbk (Mitratel)",
            "tagline": "Tower-as-a-Service (TaaS) & Power-as-a-Service (PaaS) - Jawa Timur & Jawa Tengah",
            "strategy": "Centralized Power-as-a-Service Provisioning for Macro Towers across Trans-Jawa Corridors",
            "target_sites": 120,
            "phase": "Portfolio Mapping & Micro-Grid Energy Feasibility",
            "msa_status": "SLA & Handover Protocol Harmonization",
            "sla_target": "99.98% High-Resilience Backbone SLA",
            "power_spec": "Samvad High-Capacity LiFePO4 + Integrated ATS/DG Hybrid",
            "color": "#F59E0B",
            "candidates": [
                {"id": "MIT-001", "name": "Surabaya Perak Macro 1", "district": "Surabaya", "tower": "SST 72m Macro", "power": "Samvad ATS-LiFePO4 Tier-1", "wave": "Wave 1 (H1 2027)", "status": "Technical Audit Done"},
                {"id": "MIT-002", "name": "Gresik Manyar Port Access", "district": "Gresik", "tower": "SST 60m Macro", "power": "Samvad ATS-LiFePO4 Tier-1", "wave": "Wave 1 (H1 2027)", "status": "Technical Audit Done"},
                {"id": "MIT-003", "name": "Semarang Tanjung Emas Harbor", "district": "Semarang", "tower": "SST 65m Macro", "power": "High-Cap LiFePO4 Hybrid", "wave": "Wave 2 (H2 2027)", "status": "Engineering Review"},
                {"id": "MIT-004", "name": "Surakarta Manahan Node", "district": "Surakarta", "tower": "SST 55m Macro", "power": "Samvad ATS-LiFePO4 Tier-1", "wave": "Wave 2 (H2 2027)", "status": "Logistics Mapping"},
                {"id": "MIT-005", "name": "Malang Singosari High Mast", "district": "Malang", "tower": "Guyed Mast 60m", "power": "High-Cap LiFePO4 Hybrid", "wave": "Wave 3 (2028)", "status": "Candidate Nominated"},
            ]
        }
    }
    
    prof = tenant_profiles.get(operator_name, tenant_profiles["XLSmart"])
    
    # Notice & Overview Card
    st.markdown(
        f"""
        <div class="op-card" style="border-left: 4px solid {prof['color']}; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A;">
                        {prof['name']}
                    </div>
                    <div style="font-size: 0.85rem; color: #64748B; font-weight: 500; margin-top: 2px;">
                        {prof['tagline']} &bull; <b style="color: {prof['color']};">{prof['strategy']}</b>
                    </div>
                </div>
                <div>
                    <span style="background: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; padding: 4px 12px; border-radius: 4px; font-weight: 700; font-size: 0.78rem;">
                        Multi-Tenant Provisioning &bull; Planning Phase
                    </span>
                </div>
            </div>
            <div style="margin-top: 12px; padding: 10px 14px; background: #F8FAFC; border-radius: 6px; border: 1px solid #E2E8F0; font-size: 0.82rem; color: #334155; line-height: 1.5;">
                <b>PMO & NOC Status:</b> All live field operations data currently applies to <b>Telkomcel (100 Sites)</b>. This <b>{operator_name}</b> tenant module is pre-integrated into the Samvad Tower Control system to support site onboarding, joint technical surveys, and PaaS SLA activation upon project contract kick-off.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4 Pipeline Radar Cards
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid {prof['color']};">
                <div style="font-size: 0.72rem; font-weight: 700; color: {prof['color']}; text-transform: uppercase;">PLANNED PORTFOLIO</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 3px 0;">0 Live &bull; {prof['target_sites']} Planned</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • Target Phase: Indicative Wave 1-3<br/>
                    • Scoping: {prof['phase']}<br/>
                    • Priority: High Revenue Density
                </div>
            </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #10B981;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #059669; text-transform: uppercase;">POWER SPECIFICATION</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin: 3px 0;">LiFePO4 Tier-1</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • {prof['power_spec']}<br/>
                    • Telemetry: SNMP / Modbus RTU<br/>
                    • Target Backup: 4.0 - 8.0 Hours
                </div>
            </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #3B82F6;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #2563EB; text-transform: uppercase;">CONTRACT & MSA</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin: 3px 0;">Gate 0 Scoping</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • {prof['msa_status']}<br/>
                    • Milestone: BAST & PAC Handover<br/>
                    • Commercial: Fixed Monthly PaaS
                </div>
            </div>
        """, unsafe_allow_html=True)
    with r4:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #F59E0B;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #D97706; text-transform: uppercase;">SLA COMMITMENT</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin: 3px 0;">99.95% Availability</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • {prof['sla_target']}<br/>
                    • Field Dispatch: 24/7 Mobile SLA<br/>
                    • Audit: Quarterly Health Index
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Multi-Tenant PMO Onboarding Lifecycle & Candidate Staging Matrix
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    c_gates, c_sample = st.columns([1.1, 1.2])

    with c_gates:
        st.markdown(
            """
            <div class="op-card">
                <div class="op-card-header">
                    <span>Multi-Tenant PMO Onboarding Lifecycle</span>
                    <span style="font-size: 0.75rem; color: #64748B;">6-Gate Protocol</span>
                </div>
                <table class="snapshot-table">
                    <thead>
                        <tr>
                            <th>Onboarding Gate</th>
                            <th style="text-align:center;">Status</th>
                            <th>Target Schedule</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><b>Gate 0:</b> MSA & Commercial Framework</td>
                            <td style="text-align:center;"><span style="color:#10B981; font-weight:700;">Aligned</span></td>
                            <td>Legal Sign-off</td>
                        </tr>
                        <tr style="background:#FFFBEB;">
                            <td><b>Gate 1:</b> Candidate Site Nomination</td>
                            <td style="text-align:center;"><span style="color:#D97706; font-weight:700;">In Progress</span></td>
                            <td>Active Candidate Review</td>
                        </tr>
                        <tr>
                            <td><b>Gate 2:</b> Joint Structural & Power Audit</td>
                            <td style="text-align:center;"><span style="color:#64748B;">Scheduled</span></td>
                            <td>Q4 2026</td>
                        </tr>
                        <tr>
                            <td><b>Gate 3:</b> BOM Sizing & Maritime Freight</td>
                            <td style="text-align:center;"><span style="color:#64748B;">Scheduled</span></td>
                            <td>Q1 2027</td>
                        </tr>
                        <tr>
                            <td><b>Gate 4:</b> Shelter & DC Power I&C</td>
                            <td style="text-align:center;"><span style="color:#64748B;">Pending</span></td>
                            <td>Q2 2027</td>
                        </tr>
                        <tr>
                            <td><b>Gate 5:</b> Battery Load Test & SOP QA</td>
                            <td style="text-align:center;"><span style="color:#64748B;">Pending</span></td>
                            <td>Q2 2027</td>
                        </tr>
                        <tr>
                            <td><b>Gate 6:</b> Commercial BAST & NOC Live</td>
                            <td style="text-align:center;"><span style="color:#64748B;">Pending</span></td>
                            <td>Commercial Go-Live</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c_sample:
        st.markdown(
            f"""
            <div class="op-card">
                <div class="op-card-header">
                    <span>Candidate Staging Matrix: {operator_name}</span>
                    <span style="font-size: 0.75rem; color: {prof['color']}; font-weight: 700;">{len(prof['candidates'])} Scoped Sites</span>
                </div>
            """,
            unsafe_allow_html=True
        )
        
        df_cand = pd.DataFrame(prof["candidates"])
        st.dataframe(
            df_cand.rename(columns={
                "id": "Candidate ID",
                "name": "Site Name",
                "district": "District",
                "tower": "Tower Type",
                "power": "Planned Rectifier",
                "wave": "Rollout Wave",
                "status": "Readiness Status"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Matrix displays candidate site sample for {operator_name}. Upon tender/MSA ratification, Excel bulk upload is enabled for synchronized live ingestion.")
        st.markdown("</div>", unsafe_allow_html=True)


def render_noc_control_tower():
    kpi_calc = KPICalculator()
    summary = kpi_calc.get_overall_kpi_summary()
    score = summary["overall_score"]
    tier_label = summary["tier_label"]

    df_all = query_df("SELECT * FROM timor_sites_100 ORDER BY accessible_route_km ASC")

    # Filter data dynamically based on selection
    current_op = st.session_state.get("global_operator_select") or st.session_state.get("noc_selected_operator", "All")
    if current_op not in ["All", "Telkomcel", "XLSmart", "IOH", "Mitratel"]:
        current_op = "All"

    if current_op == "All":
        df_view = df_all.copy()
    else:
        df_view = df_all[df_all["operator"] == current_op].copy()
    
    # Defensive column check to prevent KeyError across migrations
    for col, default_val in [
        ("blocker_reason", ""),
        ("readiness_gate", ""),
        ("paas_status", ""),
        ("operator", "Telkomcel"),
        ("assigned_team", ""),
        ("last_updated_by", ""),
        ("updated_at", "")
    ]:
        if col not in df_view.columns:
            df_view[col] = default_val
    
    total_sites = len(df_view)
    c_shipping = len(df_view[df_view["paas_status"].str.contains("Shipping", na=False)])
    c_staged = len(df_view[df_view["paas_status"].str.contains("Staged", na=False)])
    c_power = len(df_view[df_view["paas_status"].str.contains("Power", na=False)])
    c_testing = len(df_view[df_view["paas_status"].str.contains("Testing", na=False)])
    c_handover = len(df_view[df_view["paas_status"].str.contains("Handover", na=False)])
    c_blocked = len(df_view[df_view["paas_status"].str.contains("Blocked|Issue", na=False)])
    c_civil_dep = len(df_view[df_view["readiness_gate"].str.contains("Civil", na=False) | df_view["blocker_reason"].str.contains("Civil", na=False)])

    # Dynamic real-time operational score reflecting actual site delivery and blocked penalties
    if total_sites > 0:
        base_progress = (
            (c_handover * 100.0) +
            (c_testing * 92.0) +
            (c_power * 85.0) +
            (c_staged * 55.0) +
            (c_shipping * 35.0)
        ) / total_sites
        # Penalty for blocked sites (-3.5% per blocked site)
        blocked_penalty = c_blocked * 3.5
        live_score = round(max(0.0, min(120.0, base_progress - blocked_penalty + 18.5)), 1)
    else:
        live_score = 100.0

    if live_score >= 115.0:
        live_tier = "Tier 1: Maximum 120% Performance Tier"
    elif live_score >= 100.0:
        live_tier = "Tier 2: 100% On-Target Compliance"
    else:
        live_tier = "Tier 3: Below Target (<100%)"

    if current_op == "All":
        crumb = 'Overview &nbsp;&rsaquo;&nbsp; NOC Views &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">All Clients</b> &nbsp;&rsaquo;&nbsp; <b>Multi-Tenant PaaS Portfolio Command Center</b>'
        badge_txt = f"Portfolio: {total_sites} Sites &bull; KPI: {live_score:.1f}%"
        bg, fg, bd = "#ECFDF5", "#065F46", "#A7F3D0"
    elif current_op == "Telkomcel":
        crumb = 'Overview &nbsp;&rsaquo;&nbsp; NOC Views &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">Telkomcel</b> &nbsp;&rsaquo;&nbsp; <b>Timor-Leste 100-Site PaaS Delivery Blueprint</b>'
        badge_txt = f"KPI: {live_score:.1f}% &bull; {live_tier}"
        bg, fg, bd = "#ECFDF5", "#065F46", "#A7F3D0"
    elif current_op == "XLSmart":
        crumb = 'Overview &nbsp;&rsaquo;&nbsp; NOC Views &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">XLSmart</b> &nbsp;&rsaquo;&nbsp; <b>Sumatra Utara & Aceh 25-Site PaaS Modernization Blueprint</b>'
        badge_txt = f"XLSmart: {total_sites} Sites &bull; KPI: {live_score:.1f}%"
        bg, fg, bd = "#EFF6FF", "#1E40AF", "#BFDBFE"
    elif current_op == "Mitratel":
        crumb = 'Overview &nbsp;&rsaquo;&nbsp; NOC Views &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">Mitratel</b> &nbsp;&rsaquo;&nbsp; <b>Jawa Timur & Jawa Tengah 35-Site Macro Tower PaaS Blueprint</b>'
        badge_txt = f"Mitratel: {total_sites} Macro Sites &bull; KPI: {live_score:.1f}%"
        bg, fg, bd = "#FFFBEB", "#B45309", "#FDE68A"
    elif current_op == "IOH":
        crumb = 'Overview &nbsp;&rsaquo;&nbsp; NOC Views &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">IOH</b> &nbsp;&rsaquo;&nbsp; <b>Kalimantan & IKN 20-Site PaaS Modernization Blueprint</b>'
        badge_txt = f"IOH: {total_sites} Sites &bull; KPI: {live_score:.1f}%"
        bg, fg, bd = "#F5F3FF", "#6D28D9", "#DDD6FE"
    else:
        crumb = f'Overview &nbsp;&rsaquo;&nbsp; NOC Views &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">{current_op}</b> &nbsp;&rsaquo;&nbsp; <b>{current_op} PaaS Rollout & Operations Blueprint</b>'
        badge_txt = f"{current_op}: {total_sites} Sites &bull; Active Rollout"
        bg, fg, bd = "#EFF6FF", "#1E40AF", "#BFDBFE"

    # Multi-Tenant Operator Selection & Sub-Bar (OpManager Clean Style)
    selected_operator = render_unified_module_header(
        module_label="DASHBOARD",
        breadcrumb_trail=crumb,
        badge_text=badge_txt,
        badge_bg=bg,
        badge_color=fg,
        badge_border=bd
    )


    # === FIELD OPERATIONS PULSE (TIGHT TWO-WAY INTEGRATION WITH FIELD OPS) ===
    op_live_data = RolloutOperationsService.get_daily_operational_summary(selected_operator)
    active_crews = op_live_data.get("active_crews_count", 5)
    weekly_comm = len(op_live_data.get("weekly_commissioning", op_live_data.get("today_commissioning", [])))
    weekly_atp = len(op_live_data.get("weekly_atp", op_live_data.get("today_atp", [])))
    weekly_target = op_live_data.get("weekly_target", 5)
    live_blockers = op_live_data.get("c_blocked", 0)

    st.markdown(
        f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #0284C7; padding: 7px 14px; border-radius: 6px; margin: 4px 0 10px 0; display: flex; align-items: center; gap: 14px; flex-wrap: wrap; font-size: 0.78rem;">
            <span style="font-weight: 700; color: #0F172A; text-transform: uppercase; font-size: 0.74rem; letter-spacing: 0.5px;">Live Field Operations:</span>
            <span><b>{active_crews} Active Crews</b> on Duty</span>
            <span>Weekly Target: <b>{weekly_comm} Commissioning</b> &bull; <b>{weekly_atp} ATP Sign-Off</b> (Run-Rate: <b>{weekly_target} Sites/Wk</b>)</span>
            <span style="color: {'#DC2626' if live_blockers > 0 else '#059669'}; font-weight: {'700' if live_blockers > 0 else '600'};">
                {live_blockers} Active Blockers
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Main 3-Widget Row (OpManager 3-Column Split - Equal Height & Aligned)
    col_map, col_heatmap, col_snapshot = st.columns([1.18, 1.18, 1.04])
    card_map = col_map.container(height=430, border=True)
    card_heatmap = col_heatmap.container(height=430, border=True)
    card_snapshot = col_snapshot.container(height=430, border=True)

    # === WIDGET 1: GEOGRAPHIC TOPOLOGY MAP ===
    with card_map:
        if selected_operator == "All":
            header_client = "All Portfolios"
        elif selected_operator == "XLSmart":
            header_client = "XLSmart (Sumut-Aceh)"
        elif selected_operator == "Mitratel":
            header_client = "Mitratel (Jatim-Jateng)"
        elif selected_operator == "IOH":
            header_client = "IOH (Kalimantan-IKN)"
        elif selected_operator == "Telkomcel":
            header_client = "Telkomcel (Timor)"
        else:
            header_client = f"{selected_operator}"

        st.markdown(
            f"""
            <div class="op-card-header">
                <span>Geographic Topology</span>
                <span style="font-size: 0.74rem; color: #0284C7; font-weight: 700; background: #E0F2FE; padding: 2px 8px; border-radius: 4px; border: 1px solid #BAE6FD; white-space: nowrap;">{total_sites} Sites • {header_client}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        active_color_map = {
            "🟢 Handover Telkomcel": "#10B981",
            "🟢 Handover XLSmart": "#10B981",
            "🟢 Handover IOH": "#10B981",
            "🟢 Handover Mitratel": "#10B981",
            "🟢 Handover": "#10B981",
            "🟡 Testing & QA": "#F59E0B",
            "🟣 Power I&C Active": "#8B5CF6",
            "🔵 Civil & Site Prep": "#3B82F6",
            "⚪ Staged / Dili Hub": "#94A3B8",
            "⚪ Staged / Regional Hub": "#94A3B8",
            "⚪ Staged / Medan Hub": "#94A3B8",
            "⚪ Staged / Surabaya Hub": "#94A3B8",
            "⚪ Staged / Balikpapan Hub": "#94A3B8",
            "Shipping & Customs": "#06B6D4",
            "🚢 Shipping & Customs": "#06B6D4",
            "🔴 Blocked / Issue": "#EF4444"
        }

        # Determine dynamic center and zoom based on selected operator
        if selected_operator == "XLSmart":
            map_center = dict(lat=3.75, lon=97.55)
            map_zoom = 6.0
        elif selected_operator == "Mitratel":
            map_center = dict(lat=-7.45, lon=111.45)
            map_zoom = 6.6
        elif selected_operator == "IOH":
            map_center = dict(lat=-0.70, lon=114.80)
            map_zoom = 5.5
        elif selected_operator == "All":
            map_center = dict(lat=-2.5, lon=115.0)
            map_zoom = 4.2
        else:
            map_center = dict(lat=-8.78, lon=125.72)
            map_zoom = 7.8

        fig_map = px.scatter_map(
            df_view,
            lat="lat",
            lon="lon",
            color="paas_status",
            size="priority_index",
            size_max=14,
            hover_name="site_name",
            hover_data={
                "operator": True,
                "site_id": True,
                "district": True,
                "paas_status": True,
                "readiness_gate": True,
                "accessible_route_km": ":.1f km",
                "est_travel_time": True,
                "rectifier": True,
                "backup_hours": True,
                "lon": False,
                "lat": False
            },
            color_discrete_map=active_color_map,
            zoom=map_zoom,
            center=map_center,
            map_style="open-street-map",
            title=None
        )

        if selected_operator == "XLSmart":
            # Sumatra Utara & Aceh Maritime & Transport Corridors
            # Ferry Corridor 1: Banda Aceh (Ulee Lheue) to Sabang (Balohan, Pulau Weh)
            fig_map.add_trace(go.Scattermap(
                lat=[5.5620, 5.8450],
                lon=[95.2860, 95.3340],
                mode="lines",
                line=dict(width=2.5, color="#06B6D4"),
                name="Fast Boat: Banda Aceh – Sabang (33 km)",
                hoverinfo="text",
                text="Maritime Corridor: Ulee Lheue (Banda Aceh) ↔ Balohan (Sabang, Pulau Weh) (33 km)"
            ))

            # Ferry Corridor 2: Sibolga to Gunungsitoli (Nias Island)
            fig_map.add_trace(go.Scattermap(
                lat=[1.7450, 1.2910],
                lon=[98.7860, 97.6160],
                mode="lines",
                line=dict(width=2.5, color="#EC4899"),
                name="Ro-Ro Ferry: Sibolga – Nias (120 km)",
                hoverinfo="text",
                text="Maritime Enclave Corridor: Pelabuhan Sibolga ↔ Gunungsitoli (Nias Island) (120 km)"
            ))

            # 4 Regional Logistics Hubs
            fig_map.add_trace(go.Scattermap(
                lat=[3.5925, 5.5535, 1.7450, 5.1760],
                lon=[98.6780, 95.3180, 98.7860, 97.1350],
                mode="markers+text",
                name="Regional Logistics Hubs",
                text=["Medan Hub", "Banda Aceh", "Sibolga", "Lhokseumawe"],
                textposition="bottom right",
                marker=dict(size=12, color="#F59E0B")
            ))

            # Star Marker: Pelabuhan Belawan (Medan)
            fig_map.add_trace(go.Scattermap(
                lat=[BELAWAN_PORT_COORDS[0]],
                lon=[BELAWAN_PORT_COORDS[1]],
                mode="markers+text",
                name="Pelabuhan Belawan",
                text=["Pelabuhan Belawan (Medan)"],
                textposition="top right",
                marker=dict(size=18, color="#10B981")
            ))
        elif selected_operator == "Mitratel":
            # Jawa Timur & Jawa Tengah Corridors
            # Trans-Jawa Tol Corridor (Surabaya - Mojokerto - Madiun - Solo - Semarang)
            fig_map.add_trace(go.Scattermap(
                lat=[-7.2010, -7.4720, -7.5450, -7.5560, -6.9920],
                lon=[112.7310, 112.4410, 111.6580, 110.8120, 110.4230],
                mode="lines",
                line=dict(width=3.0, color="#3B82F6"),
                name="Tol Trans-Jawa (Surabaya-Solo-Semarang)",
                hoverinfo="text",
                text="Tol Trans-Jawa Arterial Backbone Corridor (Surabaya - Solo - Semarang)"
            ))

            # Suramadu Bridge (Surabaya to Bangkalan Madura)
            fig_map.add_trace(go.Scattermap(
                lat=[-7.2010, -7.0420],
                lon=[112.7310, 112.7950],
                mode="lines",
                line=dict(width=3.0, color="#EC4899"),
                name="Jembatan Suramadu (Surabaya – Madura)",
                hoverinfo="text",
                text="Jembatan Suramadu Madura Gateway (18.5 km)"
            ))

            # Tapal Kuda East Java corridor (Surabaya - Pasuruan - Probolinggo - Banyuwangi)
            fig_map.add_trace(go.Scattermap(
                lat=[-7.2010, -7.6450, -7.7580, -8.1480],
                lon=[112.7310, 112.9050, 113.2180, 114.3980],
                mode="lines",
                line=dict(width=2.5, color="#F59E0B"),
                name="Tol Paspro & Pantura Banyuwangi",
                hoverinfo="text",
                text="Tol Paspro & Pantura East Java Corridor to Banyuwangi (295 km)"
            ))

            # Regional Logistics Hubs: Surabaya, Semarang, Solo, Malang
            fig_map.add_trace(go.Scattermap(
                lat=[-7.2650, -6.9920, -7.5560, -7.8920],
                lon=[112.7520, 110.4230, 110.8120, 112.6650],
                mode="markers+text",
                name="Regional Logistics Hubs",
                text=["Surabaya Hub", "Semarang Hub", "Solo Hub", "Malang Hub"],
                textposition="bottom right",
                marker=dict(size=12, color="#F59E0B")
            ))

            # Star Marker: Pelabuhan Tanjung Perak (Surabaya) & Tanjung Emas (Semarang)
            fig_map.add_trace(go.Scattermap(
                lat=[TANJUNG_PERAK_COORDS[0], -6.9530],
                lon=[TANJUNG_PERAK_COORDS[1], 110.4210],
                mode="markers+text",
                name="Inbound Seaports",
                text=["Pel. Tanjung Perak (Surabaya)", "Pel. Tanjung Emas (Semarang)"],
                textposition="top right",
                marker=dict(size=16, color="#10B981")
            ))
        elif selected_operator == "IOH":
            # Kalimantan & IKN Corridors
            # Tol Balsam & IKN Nusantara Core Corridor (Balikpapan - Sepaku IKN - Samarinda)
            fig_map.add_trace(go.Scattermap(
                lat=[-1.2680, -0.9720, -0.5120],
                lon=[116.8220, 116.7110, 117.1350],
                mode="lines",
                line=dict(width=3.2, color="#8B5CF6"),
                name="Tol Balsam & Akses IKN Nusantara",
                hoverinfo="text",
                text="Tol Balsam & Jalan Bebas Hambatan IKN Nusantara Corridor"
            ))

            # Trans-Kalimantan Highway Corridor (Balikpapan - Banjarmasin)
            fig_map.add_trace(go.Scattermap(
                lat=[-1.2680, -2.1500, -3.3280],
                lon=[116.8220, 115.5000, 114.5680],
                mode="lines",
                line=dict(width=2.5, color="#06B6D4"),
                name="Trans-Kalimantan Selatan",
                hoverinfo="text",
                text="Jalur Lintas Kalimantan Timur ↔ Kalimantan Selatan (Banjarmasin)"
            ))

            # Regional Logistics Hubs: Balikpapan, IKN Sepaku, Samarinda, Banjarmasin, Pontianak
            fig_map.add_trace(go.Scattermap(
                lat=[-1.2610, -0.9720, -0.5120, -3.3280, -0.0250],
                lon=[116.8390, 116.7110, 117.1350, 114.5680, 109.3320],
                mode="markers+text",
                name="Regional Logistics Hubs",
                text=["Balikpapan Hub", "IKN Nusantara", "Samarinda", "Banjarmasin", "Pontianak"],
                textposition="bottom right",
                marker=dict(size=12, color="#F59E0B")
            ))

            # Star Marker: Pelabuhan Semayang Balikpapan
            fig_map.add_trace(go.Scattermap(
                lat=[BALIKPAPAN_PORT_COORDS[0]],
                lon=[BALIKPAPAN_PORT_COORDS[1]],
                mode="markers+text",
                name="Pelabuhan Semayang",
                text=["Pelabuhan Semayang (Balikpapan)"],
                textposition="top right",
                marker=dict(size=18, color="#10B981")
            ))
        elif selected_operator == "All":
            # Origin Ports for all 4 regions
            fig_map.add_trace(go.Scattermap(
                lat=[PORT_DILI_COORDS[0], BELAWAN_PORT_COORDS[0], TANJUNG_PERAK_COORDS[0], BALIKPAPAN_PORT_COORDS[0]],
                lon=[PORT_DILI_COORDS[1], BELAWAN_PORT_COORDS[1], TANJUNG_PERAK_COORDS[1], BALIKPAPAN_PORT_COORDS[1]],
                mode="markers+text",
                name="Central Ports",
                text=["Port Dili", "Pelabuhan Belawan", "Pelabuhan Tanjung Perak", "Pelabuhan Semayang"],
                textposition="top right",
                marker=dict(size=16, color="#10B981")
            ))
            fig_map.add_trace(go.Scattermap(
                lat=[-8.4710, 3.5925, -7.2650, -0.9720],
                lon=[126.4580, 98.6780, 112.7520, 116.7110],
                mode="markers+text",
                name="Regional Hubs",
                text=["Baucau", "Medan", "Surabaya", "IKN Nusantara"],
                textposition="bottom right",
                marker=dict(size=11, color="#F59E0B")
            ))
        else: # Telkomcel (strictly Timor-Leste)
            # Ferry Corridor 1: Port Dili to Atauro Island
            fig_map.add_trace(go.Scattermap(
                lat=[-8.5520, -8.2700],
                lon=[125.5711, 125.6000],
                mode="lines",
                line=dict(width=2.2, color="#A855F7"),
                name="Ferry: Dili – Atauro (36.5 km)",
                hoverinfo="text",
                text="Maritime Corridor: Port Dili to Atauro Island (36.5 km)"
            ))

            # Ferry Corridor 2: Port Dili to Oecusse Enclave
            fig_map.add_trace(go.Scattermap(
                lat=[-8.5520, -8.60, -9.00, -9.2000],
                lon=[125.5711, 125.00, 124.60, 124.3700],
                mode="lines",
                line=dict(width=2.2, color="#EC4899"),
                name="Nakroma Ferry: Dili – Oecusse (148 km)",
                hoverinfo="text",
                text="Maritime Enclave Corridor: Port Dili to Lifau/Oecusse (148 km)"
            ))

            # Regional Virtual Cross-Dock & Drop Points (Zero Warehouse Rental)
            fig_map.add_trace(go.Scattermap(
                lat=[-8.4710, -9.3130, -9.2000],
                lon=[126.4580, 125.2570, 124.3700],
                mode="markers+text",
                name="Virtual Cross-Dock Yards",
                text=["Baucau (Cross-Dock)", "Suai (JIT Drop)", "Oecusse (Branch Yard)"],
                textposition="bottom right",
                marker=dict(size=12, color="#F59E0B")
            ))

            # Star Marker: Port Dili
            fig_map.add_trace(go.Scattermap(
                lat=[PORT_DILI_COORDS[0]],
                lon=[PORT_DILI_COORDS[1]],
                mode="markers+text",
                name="Port Dili",
                text=["Port Dili"],
                textposition="top right",
                marker=dict(size=18, color="#10B981")
            ))

        fig_map.update_layout(
            height=360,
            margin=dict(l=0, r=0, t=2, b=2),
            showlegend=False
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # === WIDGET 2: ROLLOUT DISTRIBUTION (WHITE DONUT + HORIZONTAL BAR CHART) ===
    with card_heatmap:
        st.markdown(
            f"""
            <div class="op-card-header">
                <span>PaaS Rollout Distribution</span>
                <span style="font-size: 0.74rem; color: #059669; font-weight: 700; background: #D1FAE5; padding: 2px 8px; border-radius: 4px; border: 1px solid #A7F3D0; white-space: nowrap;">{total_sites} Sites Target</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        if selected_operator == "XLSmart":
            staged_name = "Staged / Medan Hub"
        elif selected_operator == "Mitratel":
            staged_name = "Staged / Surabaya Hub"
        elif selected_operator == "IOH":
            staged_name = "Staged / Balikpapan Hub"
        elif selected_operator == "All":
            staged_name = "Staged / Regional Hubs"
        else:
            staged_name = "Staged / Dili Hub"

        # Build Donut Chart with Pure White Canvas
        donut_data = [
            {"status": "Handover", "count": c_handover, "color": "#10B981"},
            {"status": "Power I&C", "count": c_power, "color": "#8B5CF6"},
            {"status": "Testing/QA", "count": c_testing, "color": "#F59E0B"},
            {"status": staged_name, "count": c_staged, "color": "#94A3B8"},
            {"status": "Customs", "count": c_shipping, "color": "#06B6D4"},
        ]
        if c_blocked > 0:
            donut_data.append({"status": "Blocked", "count": c_blocked, "color": "#EF4444"})
        df_donut = pd.DataFrame(donut_data)

        fig_donut = go.Figure(data=[go.Pie(
            labels=df_donut["status"],
            values=df_donut["count"],
            hole=0.68,
            marker=dict(colors=df_donut["color"], line=dict(color="#FFFFFF", width=2)),
            textinfo="none",
            hoverinfo="label+value+percent"
        )])
        fig_donut.update_layout(
            showlegend=False,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            annotations=[dict(text=f"<b>{total_sites}</b><br><span style='font-size:10px;color:#64748B;'>Total Sites</span>", x=0.5, y=0.5, font_size=18, showarrow=False)],
            margin=dict(t=5, b=5, l=5, r=5),
            height=260
        )

        # Build Horizontal Bar Chart
        bar_data = [
            {"stage": "Handover", "count": c_handover, "color": "#10B981", "hover": f"Handover: {c_handover} Sites"},
            {"stage": "Power I&C", "count": c_power, "color": "#8B5CF6", "hover": f"Power I&C: {c_power} Sites"},
            {"stage": "Testing/QA", "count": c_testing, "color": "#F59E0B", "hover": f"Testing & QA: {c_testing} Sites"},
            {"stage": "Staged", "count": c_staged, "color": "#94A3B8", "hover": f"{staged_name}: {c_staged} Sites"},
            {"stage": "Customs", "count": c_shipping, "color": "#06B6D4", "hover": f"Shipping & Customs: {c_shipping} Sites"},
        ]
        if c_blocked > 0:
            bar_data.append({"stage": "Blocked", "count": c_blocked, "color": "#EF4444", "hover": f"Blocked / Issue: {c_blocked} Sites"})
        df_bar = pd.DataFrame(bar_data)

        pct_label = lambda c: round(c / total_sites * 100) if total_sites else 0
        fig_bar = go.Figure(go.Bar(
            x=df_bar["count"],
            y=df_bar["stage"],
            orientation="h",
            marker=dict(color=df_bar["color"]),
            text=[f" <b>{c}</b> ({pct_label(c)}%)" for c in df_bar["count"]],
            textposition="outside",
            cliponaxis=False,
            hovertext=df_bar["hover"],
            hoverinfo="text+x"
        ))
        max_bar = max(df_bar["count"].max() if not df_bar.empty else 10, 10)
        fig_bar.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=0, r=46, t=5, b=5),
            height=260,
            xaxis=dict(showgrid=False, showticklabels=False, range=[0, max_bar * 1.34]),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10.5, color="#334155")),
        )

        h_col1, h_col2 = st.columns([1, 1.25], vertical_alignment="center")
        with h_col1:
            st.plotly_chart(fig_donut, use_container_width=True)
        with h_col2:
            st.plotly_chart(fig_bar, use_container_width=True)

        # Legend under Distribution (OpManager Clean Style on Pure White)
        legend_blocked_html = f'<span style="color: #991B1B;"><span style="color:#EF4444;">●</span> Blocked: {c_blocked}</span>' if c_blocked > 0 else ''
        legend_civil_dep_html = f'<span style="color: #B45309;"><span style="color:#D97706;">●</span> Civil Dep: {c_civil_dep}</span>' if c_civil_dep > 0 else ''
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 6px; font-size: 0.72rem; font-weight: 600; margin-top: 4px; padding: 5px 4px; background: #F8FAFC; border-radius: 6px; border: 1px solid #E2E8F0;">
                <span style="color: #065F46;"><span style="color:#10B981;">●</span> Handover: {c_handover}</span>
                <span style="color: #6B21A8;"><span style="color:#8B5CF6;">●</span> Power: {c_power}</span>
                <span style="color: #92400E;"><span style="color:#F59E0B;">●</span> Testing: {c_testing}</span>
                <span style="color: #475569;"><span style="color:#94A3B8;">●</span> Staged: {c_staged}</span>
                <span style="color: #0E7490;"><span style="color:#06B6D4;">●</span> Shipping: {c_shipping}</span>
                {legend_civil_dep_html}
                {legend_blocked_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    # === WIDGET 3: INFRASTRUCTURE SNAPSHOT TABLE ===
    with card_snapshot:
        st.markdown(
            f"""
            <div class="op-card-header">
                <span>Infrastructure Snapshot</span>
                <span style="font-size: 0.74rem; color: #059669; font-weight: 700; background: #D1FAE5; padding: 2px 8px; border-radius: 4px; border: 1px solid #A7F3D0; white-space: nowrap;">{total_sites} Sites Operational</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Compute dynamic hold counts from readiness gate per stage
        is_hold = lambda st_filter: len(df_view[
            df_view["paas_status"].str.contains(st_filter, na=False) &
            ~df_view["readiness_gate"].str.contains("GO", na=False)
        ])
        hold_handover = is_hold("Handover")
        hold_testing = is_hold("Testing")
        hold_power = is_hold("Power")
        hold_staged = is_hold("Staged")
        hold_shipping = is_hold("Shipping")
        total_hold = hold_handover + hold_testing + hold_power + hold_staged + hold_shipping + c_blocked

        st.markdown(
            f"""
            <table class="snapshot-table">
                <thead>
                    <tr>
                        <th>Stage / Infrastructure</th>
                        <th style="text-align:center;">Sites</th>
                        <th style="text-align:center;">Target Wave</th>
                        <th style="text-align:center;">Pending/Hold</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10B981; margin-right:8px;"></span><b>Handover & Live</b></td>
                        <td style="text-align:center; font-weight:700;">{c_handover}</td>
                        <td style="text-align:center; color:#64748B;">Wave 1</td>
                        <td style="text-align:center; color:{'#EF4444' if hold_handover > 0 else '#10B981'}; font-weight:600;">{hold_handover}</td>
                    </tr>
                    <tr>
                        <td><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#F59E0B; margin-right:8px;"></span><b>Testing & QA</b></td>
                        <td style="text-align:center; font-weight:700;">{c_testing}</td>
                        <td style="text-align:center; color:#64748B;">Wave 2</td>
                        <td style="text-align:center; color:{'#EF4444' if hold_testing > 0 else '#10B981'}; font-weight:600;">{hold_testing}</td>
                    </tr>
                    <tr>
                        <td><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#8B5CF6; margin-right:8px;"></span><b>Power I&C Active</b></td>
                        <td style="text-align:center; font-weight:700;">{c_power}</td>
                        <td style="text-align:center; color:#64748B;">Wave 3</td>
                        <td style="text-align:center; color:{'#EF4444' if hold_power > 0 else '#10B981'}; font-weight:600;">{hold_power}</td>
                    </tr>
                    <tr>
                        <td><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#94A3B8; margin-right:8px;"></span><b>{staged_name}</b></td>
                        <td style="text-align:center; font-weight:700;">{c_staged}</td>
                        <td style="text-align:center; color:#64748B;">Wave 4</td>
                        <td style="text-align:center; color:{'#EF4444' if hold_staged > 0 else '#10B981'}; font-weight:600;">{hold_staged}</td>
                    </tr>
                    <tr>
                        <td><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#06B6D4; margin-right:8px;"></span><b>Shipping & Customs</b></td>
                        <td style="text-align:center; font-weight:700;">{c_shipping}</td>
                        <td style="text-align:center; color:#64748B;">Wave 5</td>
                        <td style="text-align:center; color:{'#EF4444' if hold_shipping > 0 else '#10B981'}; font-weight:600;">{hold_shipping}</td>
                    </tr>
                    <tr style="background:{'#FEF2F2' if c_blocked > 0 else 'transparent'};">
                        <td><span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:{'#EF4444' if c_blocked > 0 else '#10B981'}; margin-right:8px;"></span><b>Blocked / Alerts</b></td>
                        <td style="text-align:center; font-weight:700; color:{'#DC2626' if c_blocked > 0 else '#059669'};">{c_blocked}</td>
                        <td style="text-align:center; color:#64748B;">Alerts</td>
                        <td style="text-align:center; color:{'#DC2626' if c_blocked > 0 else '#10B981'}; font-weight:700;">{c_blocked}</td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr>
                        <td><b>Total Operational Sites</b></td>
                        <td style="text-align:center; font-weight:800; color:#0F172A;">{total_sites}</td>
                        <td style="text-align:center; color:#0284C7; font-weight:700;">100% Target</td>
                        <td style="text-align:center; color:{'#DC2626' if total_hold > 0 else '#059669'}; font-weight:700;">{total_hold} Hold</td>
                    </tr>
                </tfoot>
            </table>
            """,
            unsafe_allow_html=True
        )

    # 4. Row 2: 4 Unified Operational Radars (Clean OpManager Style)
    c_go = len(df_view[df_view["readiness_gate"].str.contains("GO", na=False)])
    c_hold = total_sites - c_go
    pct_ho = round(c_handover / total_sites * 100) if total_sites else 0
    client_label = "All Clients" if selected_operator == "All" else selected_operator
    if selected_operator == "XLSmart":
        port_berth_label = "Pelabuhan Belawan Berth: Normal Clearance"
    elif selected_operator == "Mitratel":
        port_berth_label = "Pelabuhan Tanjung Perak Berth: Normal Clearance"
    elif selected_operator == "IOH":
        port_berth_label = "Pelabuhan Semayang Balikpapan Berth: Normal Clearance"
    elif selected_operator == "All":
        port_berth_label = "Multi-Port Inbound: Belawan, Tg. Perak, Semayang & Regional"
    else:
        port_berth_label = "Port Dili Berth: Normal Clearance"

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #06B6D4;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #0891B2;">CUSTOMS & INBOUND</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 3px 0;">0% Delay &bull; 8.5d Buffer</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • {port_berth_label}<br/>
                    • {c_shipping} Sites Inbound via Ocean Freight<br/>
                    • Demurrage Penalties: $0 (Protected)
                </div>
            </div>
        """, unsafe_allow_html=True)
    with r2:
        blocked_bullet = f'• <b style="color: {"#DC2626" if c_blocked > 0 else "#10B981"};">Blocked / Issues: {c_blocked} Sites</b><br/>' if c_blocked > 0 else ''
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #10B981;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #059669;">PAAS ROLLOUT & HANDOVER</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 3px 0;">{pct_ho}% Complete &bull; {c_power + c_testing} Active</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • {c_handover} Sites Handed Over / Commercial Live<br/>
                    • {c_power + c_testing} Sites in Field (I&C + Testing)<br/>
                    {blocked_bullet}
                    • Hardware: ELTEK / HARIF / LiFePO4
                </div>
            </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown("""
            <div class="op-radar-card" style="border-top: 3px solid #3B82F6;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #2563EB;">SG&A FINANCIAL SENTINEL</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 3px 0;">10.4% SG&A (&lt;12% Cap)</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • Lean Direct-to-Site Logistics (Zero Hub Rent)<br/>
                    • Retainer Savings: $1,850/mo (&lt;12% Cap)<br/>
                    • Financial Audit: 100% Compliant
                </div>
            </div>
        """, unsafe_allow_html=True)
    with r4:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #F59E0B;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #D97706;">FIELD DISPATCH GATES</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 3px 0;">{c_go} GO &bull; {c_hold} HOLD</div>
                <div style="font-size: 0.78rem; color: #64748B;">
                    • {c_go} Dispatch-Ready Gates Approved<br/>
                    • Client: {client_label}<br/>
                    • Friday 14:00 Auto-Report: Scheduled
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Optional Multi-Tenant Strategic Overview Expander
    if selected_operator in ["XLSmart", "IOH", "Mitratel"]:
        with st.expander(f"{selected_operator} Master Service Agreement (MSA) & Onboarding Roadmap", expanded=False):
            render_upcoming_tenant_pipeline(selected_operator)
    elif selected_operator == "All":
        with st.expander("Multi-Tenant Client Portfolio Breakdown (Telkomcel, XLSmart, IOH, Mitratel)", expanded=False):
            op_summary = []
            for op in ["Telkomcel", "XLSmart", "IOH", "Mitratel"]:
                df_op = df_all[df_all["operator"] == op]
                ho = len(df_op[df_op["paas_status"].str.contains("Handover", na=False)])
                act = len(df_op[df_op["paas_status"].str.contains("Power|Testing", na=False)])
                blk = len(df_op[df_op["paas_status"].str.contains("Blocked|Issue", na=False)])
                pln = len(df_op) - ho - act - blk
                op_summary.append({
                    "Operator / Client": op,
                    "Total Sites": len(df_op),
                    "Handover (Live)": ho,
                    "Active Field (I&C/QA)": act,
                    "Planned / Staging": pln,
                    "Blocked / Issues": blk,
                    "Completion Rate": f"{round(ho / len(df_op) * 100) if len(df_op) else 0}%"
                })
            st.dataframe(pd.DataFrame(op_summary), use_container_width=True, hide_index=True)

    # 5. Row 3: Operational Master Matrix Table
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    matrix_title = f"All Clients ({total_sites} Sites)" if selected_operator == "All" else f"{selected_operator} ({total_sites} Sites)"
    st.markdown(f"##### Operational Master Matrix: {matrix_title}")

    if selected_operator == "All":
        fcol0, fcol1, fcol2, fcol3, fcol4 = st.columns([1.2, 1.2, 1.2, 1.2, 1.5])
        with fcol0:
            sel_op = st.multiselect("Filter by Operator:", ["Telkomcel", "XLSmart", "IOH", "Mitratel"], default=[])
        with fcol1:
            sel_st = st.multiselect("Filter by PaaS Status:", sorted(df_view["paas_status"].unique()), default=[])
        with fcol2:
            sel_dist = st.multiselect("Filter by District:", sorted(df_view["district"].unique()), default=[])
        with fcol3:
            sel_gate = st.multiselect("Filter by Readiness Gate:", sorted(df_view["readiness_gate"].unique()), default=[])
        with fcol4:
            search_query = st.text_input("Search Site ID or Name:", "")
    else:
        sel_op = []
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            sel_st = st.multiselect("Filter by PaaS Status:", sorted(df_view["paas_status"].unique()), default=[])
        with fcol2:
            sel_dist = st.multiselect("Filter by District:", sorted(df_view["district"].unique()), default=[])
        with fcol3:
            sel_gate = st.multiselect("Filter by Readiness Gate:", sorted(df_view["readiness_gate"].unique()), default=[])
        with fcol4:
            search_query = st.text_input("Search Site ID or Name:", "")

    df_filtered = df_view.copy()
    if sel_op:
        df_filtered = df_filtered[df_filtered["operator"].isin(sel_op)]
    if sel_st:
        df_filtered = df_filtered[df_filtered["paas_status"].isin(sel_st)]
    if sel_dist:
        df_filtered = df_filtered[df_filtered["district"].isin(sel_dist)]
    if sel_gate:
        df_filtered = df_filtered[df_filtered["readiness_gate"].isin(sel_gate)]
    if search_query:
        df_filtered = df_filtered[
            df_filtered["site_name"].str.contains(search_query, case=False, na=False) |
            df_filtered["site_id"].str.contains(search_query, case=False, na=False)
        ]

    df_filtered = df_filtered.sort_values(by="accessible_route_km", ascending=True).reset_index(drop=True)

    if selected_operator == "XLSmart":
        sort_caption = f"Showing **{len(df_filtered)}** of {total_sites} sites. Calculated from Central Hub: **Pelabuhan Belawan (Medan)** via Google Maps overland routes & maritime crossings with driving ETA."
    elif selected_operator == "Mitratel":
        sort_caption = f"Showing **{len(df_filtered)}** of {total_sites} sites. Calculated from Central Hub: **Pelabuhan Tanjung Perak (Surabaya)** via Tol Trans-Jawa, Pantura & Pansela with driving ETA."
    elif selected_operator == "IOH":
        sort_caption = f"Showing **{len(df_filtered)}** of {total_sites} sites. Calculated from Central Hub: **Pelabuhan Semayang (Balikpapan)** via Tol Balsam & Trans-Kalimantan with driving ETA."
    elif selected_operator == "Telkomcel":
        sort_caption = f"Showing **{len(df_filtered)}** of {total_sites} sites. Calculated from Central Hub: **Port Dili** via Estrada Nacional & maritime ferries with transit ETA."
    elif selected_operator == "All":
        sort_caption = f"Showing **{len(df_filtered)}** of {total_sites} sites across all client networks. Sorted by Accessible Distance from Regional Origin Hubs."
    else:
        sort_caption = f"Showing **{len(df_filtered)}** of {total_sites} sites. Sorted by Accessible Distance."
    st.caption(sort_caption)

    if selected_operator == "All":
        display_cols = [
            "operator", "site_id", "site_name", "district", "paas_status", "readiness_gate",
            "accessible_route_km", "est_travel_time", "transport_mode", "assigned_forward_hub",
            "rectifier", "has_dg", "backup_hours", "notes"
        ]
    else:
        display_cols = [
            "site_id", "site_name", "district", "paas_status", "readiness_gate",
            "accessible_route_km", "est_travel_time", "transport_mode", "assigned_forward_hub",
            "rectifier", "has_dg", "backup_hours", "notes"
        ]

    # Operator-tailored status options for clean dropdown selection
    if selected_operator == "Telkomcel":
        status_options = [
            "🟢 Handover Telkomcel",
            "🟣 Power I&C Active",
            "🟡 Testing & QA",
            "⚪ Staged / Dili Hub",
            "Shipping & Customs",
            "🔴 Blocked / Issue"
        ]
    elif selected_operator == "XLSmart":
        status_options = [
            "🟢 Handover XLSmart",
            "🟣 Power I&C Active",
            "🟡 Testing & QA",
            "⚪ Staged / Medan Hub",
            "⚪ Staged / Regional Hub",
            "Shipping & Customs",
            "🔴 Blocked / Issue"
        ]
    elif selected_operator == "Mitratel":
        status_options = [
            "🟢 Handover Mitratel",
            "🟣 Power I&C Active",
            "🟡 Testing & QA",
            "⚪ Staged / Surabaya Hub",
            "⚪ Staged / Regional Hub",
            "Shipping & Customs",
            "🔴 Blocked / Issue"
        ]
    elif selected_operator == "IOH":
        status_options = [
            "🟢 Handover IOH",
            "🟣 Power I&C Active",
            "🟡 Testing & QA",
            "⚪ Staged / Balikpapan Hub",
            "⚪ Staged / Regional Hub",
            "Shipping & Customs",
            "🔴 Blocked / Issue"
        ]
    else:
        status_options = [
            "🟢 Handover Telkomcel",
            "🟢 Handover XLSmart",
            "🟢 Handover Mitratel",
            "🟢 Handover IOH",
            "🟣 Power I&C Active",
            "🟡 Testing & QA",
            "⚪ Staged / Dili Hub",
            "⚪ Staged / Medan Hub",
            "⚪ Staged / Surabaya Hub",
            "⚪ Staged / Balikpapan Hub",
            "⚪ Staged / Regional Hub",
            "Shipping & Customs",
            "🔴 Blocked / Issue"
        ]

    gate_options = [
        "GO (Dispatch Ready)",
        "HOLD (Civil Dependency)",
        "HOLD (Dependency)",
        "ESCALATE (High Risk)",
        "RESEQUENCE (Area Constraint)",
        "G5 - Handover [GO]",
        "G4 - Acceptance Testing [GO]",
        "G3 - Power I&C [GO]",
        "G1 - Material Staged [GO]",
        "G0 - Port Berth & Inbound [HOLD]"
    ]

    col_config = {
        "assigned_forward_hub": st.column_config.TextColumn(
            "Logistics / Staging Mode",
            help="Lean Distribution: Direct Delivery or Virtual Cross-Dock ($0 Extra Hub OPEX)"
        ),
        "paas_status": st.column_config.SelectboxColumn(
            "PaaS Rollout Status",
            help="Double-click to select status from dropdown",
            options=status_options,
            required=True
        ),
        "readiness_gate": st.column_config.SelectboxColumn(
            "Readiness Decision Gate",
            help="Double-click to select decision gate from dropdown",
            options=gate_options,
            required=True
        ),
        "accessible_route_km": st.column_config.NumberColumn(
            "Route Dist.",
            format="%.1f km"
        ),
        "backup_hours": st.column_config.NumberColumn(
            "Backup",
            format="%.1f h"
        )
    }

    editor_key = f"noc_matrix_editor_{selected_operator}"
    df_editor_input = df_filtered[display_cols].copy()

    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; padding: 6px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 0.8rem; color: #475569;">
            <span><b>Manual Inline Edit:</b> Double-click on any cell in <b>paas_status</b> or <b>readiness_gate</b> to select updates directly via dropdown.</span>
            <span style="color: #059669; font-weight: 700; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 4px;">Auto-Save to Database Active</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    edited_df = st.data_editor(
        df_editor_input,
        column_config=col_config,
        disabled=[c for c in display_cols if c not in ["paas_status", "readiness_gate"]],
        use_container_width=True,
        hide_index=True,
        key=editor_key
    )

    diff_mask = (edited_df["paas_status"].fillna("") != df_editor_input["paas_status"].fillna("")) | (edited_df["readiness_gate"].fillna("") != df_editor_input["readiness_gate"].fillna(""))
    if diff_mask.any():
        changed_indices = diff_mask[diff_mask].index
        conn = get_connection()
        cur = conn.cursor()
        saved_details = []
        for idx in changed_indices:
            row_edit = edited_df.loc[idx]
            sid = row_edit["site_id"]
            new_st = row_edit["paas_status"]
            new_gate = row_edit["readiness_gate"]
            cur.execute("UPDATE timor_sites_100 SET paas_status = ?, readiness_gate = ? WHERE site_id = ?", (new_st, new_gate, sid))
            saved_details.append(f"{sid} → {new_st}")
        conn.commit()
        conn.close()

        if editor_key in st.session_state:
            del st.session_state[editor_key]

        st.toast(f"Updates saved to database: {', '.join(saved_details)}")
        st.rerun()


@st.fragment(run_every=15)
def render_fleet_tracking_radar(selected_operator: str = "All"):
    """
    Renders the Live Field Fleet Tracking Radar Map, Telemetry Feed Table,
    and Manual Dispatch Controller.
    Strictly icon-free enterprise typography.
    Adapts camera view between Indonesia National Overview ('All') and specific client sectors.
    Auto-refreshes every 15 seconds to reflect live moving field telemetry.
    """
    fleet_df = FleetTrackingService.get_fleet_tracking_dataframe()
    kpis = FleetTrackingService.get_fleet_kpis()

    if fleet_df.empty:
        st.info("No active field crews currently registered. Register a team below in Step 1 to monitor live GPS telemetry and transit corridors on this radar.")
        unique_teams_df = fleet_df.copy()
        corridors_df = fleet_df.copy()
    else:
        unique_teams_df = fleet_df.drop_duplicates(subset=["team_code"]).copy()
        corridors_df = fleet_df[fleet_df["assigned_site_id"].notna() & fleet_df["target_site_lat"].notna() & fleet_df["current_lat"].notna()].drop_duplicates(subset=["team_code", "assigned_site_id"]).copy()

    # Base operator-specific camera coordinates and regional scope description
    if selected_operator == "XLSmart":
        base_center = dict(lat=3.50, lon=97.80)
        base_zoom = 6.4
        area_scope_desc = "Sumatra Utara &amp; Aceh Rollout Sector"
    elif selected_operator == "Mitratel":
        base_center = dict(lat=-7.45, lon=111.80)
        base_zoom = 6.8
        area_scope_desc = "Jawa Timur &amp; Jawa Tengah Rollout Sector"
    elif selected_operator == "IOH":
        base_center = dict(lat=-0.80, lon=116.80)
        base_zoom = 6.4
        area_scope_desc = "Kalimantan Timur &amp; IKN Rollout Sector"
    elif selected_operator == "Telkomcel":
        base_center = dict(lat=-8.80, lon=125.75)
        base_zoom = 7.8
        area_scope_desc = "Timor-Leste National Rollout Sector"
    else:  # "All" - General Indonesia Map View
        base_center = dict(lat=-2.20, lon=117.50)
        base_zoom = 4.2
        area_scope_desc = "Indonesia &amp; Timor-Leste Multi-Client National Grid"

    has_out_of_area = not unique_teams_df.empty and bool((unique_teams_df.get("is_out_of_area") == True).any())
    active_teams_with_gps = unique_teams_df[unique_teams_df["current_lat"].notna() & unique_teams_df["current_lon"].notna()] if not unique_teams_df.empty else pd.DataFrame()

    # When crew is out-of-area, auto-set default perspective to National Grid so both crew and site are visible
    if has_out_of_area:
        default_cam_center = dict(lat=-4.50, lon=114.50)
        default_cam_zoom = 4.2
    else:
        default_cam_center = base_center
        default_cam_zoom = base_zoom

    # Query sites for selected operator scope
    if selected_operator == "All":
        sites_query = """
            SELECT site_id, site_name, district, lat, lon, paas_status, assigned_team, accessible_route_km, operator 
            FROM timor_sites_100 
            WHERE lat IS NOT NULL AND lon IS NOT NULL
        """
        df_sites_scope = query_df(sites_query)
    else:
        sites_query = """
            SELECT site_id, site_name, district, lat, lon, paas_status, assigned_team, accessible_route_km, operator 
            FROM timor_sites_100 
            WHERE operator = ? AND lat IS NOT NULL AND lon IS NOT NULL
        """
        df_sites_scope = query_df(sites_query, (selected_operator,))

    out_area_count = kpis.get("out_of_area_count", 0)
    out_badge_bg = "#FEF2F2" if out_area_count > 0 else "#F8FAFC"
    out_badge_fg = "#DC2626" if out_area_count > 0 else "#64748B"
    out_badge_border = "#FECACA" if out_area_count > 0 else "#CBD5E1"
    out_badge_weight = "800" if out_area_count > 0 else "700"
    sync_time_str = datetime.now().strftime("%H:%M:%S")

    with st.container(border=True):
        col_rad_head, col_rad_btn = st.columns([4, 1])
        with col_rad_head:
            st.markdown(f"""
                <div>
                    <div style="font-weight: 800; font-size: 0.95rem; color: #0F172A; letter-spacing: 0.3px;">
                        LIVE FIELD FLEET TRACKING &amp; SITE DISPATCH RADAR
                    </div>
                    <div style="font-size: 0.76rem; color: #64748B; margin-top: 2px;">
                        {area_scope_desc} &bull; <span style="color: #059669; font-weight: 700;">LIVE AUTO-SYNC (15s)</span> &bull; Synchronized: {sync_time_str} &bull; Real-time GPS telemetry from field crews.
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col_rad_btn:
            if st.button("Refresh Radar", use_container_width=True, key="btn_refresh_radar_top"):
                st.toast("Refreshing telemetry from field database...")
                st.rerun()

        st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #F1F5F9; font-size: 0.74rem; color: #475569; line-height: 1.4; flex-wrap: wrap; gap: 4px;">
                <span style="background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; padding: 2px 7px; border-radius: 4px; font-weight: 700;">
                    {kpis['total_teams']} Total Crews
                </span>
                <span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; padding: 2px 7px; border-radius: 4px; font-weight: 700;">
                    {kpis['teams_with_gps']} Active GPS
                </span>
                <span style="background: #F0F9FF; color: #0284C7; border: 1px solid #BAE6FD; padding: 2px 7px; border-radius: 4px; font-weight: 700;">
                    {kpis['en_route_teams'] + kpis['confirmed_teams']} Confirmed &amp; En Route
                </span>
                <span style="background: #F5F3FF; color: #7C3AED; border: 1px solid #DDD6FE; padding: 2px 7px; border-radius: 4px; font-weight: 700;">
                    {kpis['on_site_teams']} On-Site Active
                </span>
                <span style="background: {out_badge_bg}; color: {out_badge_fg}; border: 1px solid {out_badge_border}; padding: 2px 7px; border-radius: 4px; font-weight: {out_badge_weight};">
                    {out_area_count} Out-of-Area Flags
                </span>
            </div>
        """, unsafe_allow_html=True)

        # Camera Perspective Switcher
        cam_options = ["Auto (National Transit View)"]
        crew_map_lookup = {}
        for _, r_crew in active_teams_with_gps.iterrows():
            c_code = r_crew["team_code"]
            c_lead = r_crew.get("lead_name", "")
            c_lat_val = float(r_crew["current_lat"])
            c_lon_val = float(r_crew["current_lon"])
            loc_hint = "Bandung" if 107.0 <= c_lon_val <= 108.0 else ("Jakarta" if 106.0 <= c_lon_val <= 107.0 else f"{c_lat_val:.2f}, {c_lon_val:.2f}")
            opt_label = f"Focus Crew: {c_code} ({c_lead} - {loc_hint})"
            cam_options.append(opt_label)
            crew_map_lookup[opt_label] = (c_lat_val, c_lon_val)
        cam_options.append("Focus Target Tower Sector")

        cam_col_left, cam_col_right = st.columns([1.8, 3.2])
        with cam_col_left:
            st.markdown("<div style='font-size:0.75rem; color:#475569; font-weight:700; padding:6px 0;'>Select Radar Camera View:</div>", unsafe_allow_html=True)
        with cam_col_right:
            radar_perspective = st.selectbox(
                "Map Camera View:",
                options=cam_options,
                index=0,
                key="radar_perspective_selectbox",
                label_visibility="collapsed"
            )

        if radar_perspective in crew_map_lookup:
            f_lat, f_lon = crew_map_lookup[radar_perspective]
            map_center = dict(lat=f_lat, lon=f_lon)
            map_zoom = 12.0
        elif radar_perspective == "Focus Target Tower Sector":
            map_center = base_center
            map_zoom = base_zoom
        else:
            map_center = default_cam_center
            map_zoom = default_cam_zoom

        # Plotly Radar Map
        fig_radar = go.Figure()

        # Trace 1A: Assigned Tower Sites in Scope
        df_assigned = df_sites_scope[df_sites_scope["assigned_team"].notna()].copy()
        if not df_assigned.empty:
            site_hovers = []
            for _, r in df_assigned.iterrows():
                # Check assigned team's current coordinates
                matched_team = unique_teams_df[unique_teams_df["team_code"] == r["assigned_team"]]
                if not matched_team.empty and pd.notna(matched_team.iloc[0]["current_lat"]):
                    t_row = matched_team.iloc[0]
                    routing = FleetTrackingService.calculate_road_routing(t_row["current_lat"], t_row["current_lon"], r["lat"], r["lon"])
                    road_sub = f"Live Road Distance from Crew: <b>{routing.get('road_km', 0.0):.1f} km</b><br>Fastest Route ETA: <b>{routing.get('eta_text', '-')}</b>"
                else:
                    road_sub = f"Site GPS Coordinates: <b>{r['lat']:.5f}, {r['lon']:.5f}</b>"

                site_hovers.append(
                    f"<b>TARGET TOWER SITE: {r['site_id']}</b><br>"
                    f"Site Name: <b>{r['site_name']}</b><br>"
                    f"District Sector: <b>{r['district']} ({r['operator']})</b><br>"
                    f"Site GPS: <b>{r['lat']:.5f}, {r['lon']:.5f}</b><br>"
                    f"PaaS Status: <b>{r['paas_status']}</b><br>"
                    f"Assigned Crew: <b>{r['assigned_team']}</b><br>"
                    f"{road_sub}"
                )
            fig_radar.add_trace(go.Scattermap(
                lat=df_assigned["lat"],
                lon=df_assigned["lon"],
                mode="markers+text",
                marker=dict(size=12, color="#D97706"),
                text=df_assigned["site_id"],
                textposition="bottom center",
                textfont=dict(size=9, color="#92400E", family="Inter"),
                name="Assigned Tower Sites",
                hoverinfo="text",
                hovertext=site_hovers
            ))

        # Trace 1B: Pipeline / Unassigned Sites in Scope
        df_unassigned = df_sites_scope[df_sites_scope["assigned_team"].isna()].copy()
        if not df_unassigned.empty:
            unassigned_hovers = [
                f"<b>SITE: {r['site_id']} (Unassigned)</b><br>"
                f"Site Name: {r['site_name']}<br>"
                f"District: {r['district']} ({r['operator']})<br>"
                f"Site GPS: {r['lat']:.5f}, {r['lon']:.5f}<br>"
                f"Status: {r['paas_status']}<br>"
                f"Ready for Field Crew Assignment"
                for _, r in df_unassigned.iterrows()
            ]
            fig_radar.add_trace(go.Scattermap(
                lat=df_unassigned["lat"],
                lon=df_unassigned["lon"],
                mode="markers",
                marker=dict(size=7, color="#94A3B8"),
                name="Pipeline / Unassigned Sites",
                hoverinfo="text",
                hovertext=unassigned_hovers
            ))

        # Live Field Teams (Current GPS Coordinates with Sticky Note Callouts - No Lines)
        if unique_teams_df.empty or "current_lat" not in unique_teams_df.columns:
            teams_with_gps = pd.DataFrame()
        else:
            teams_with_gps = unique_teams_df[unique_teams_df["current_lat"].notna() & unique_teams_df["current_lon"].notna()].copy()

        if not teams_with_gps.empty:
            # White halo underlay for crisp contrast over street tiles
            fig_radar.add_trace(go.Scattermap(
                lat=teams_with_gps["current_lat"],
                lon=teams_with_gps["current_lon"],
                mode="markers",
                marker=dict(size=26, color="#FFFFFF"),
                hoverinfo="skip",
                showlegend=False
            ))

            df_out = teams_with_gps[teams_with_gps["is_out_of_area"] == True]
            df_in = teams_with_gps[teams_with_gps["is_out_of_area"] == False]

            def _format_time_ago(raw_time_str):
                if not raw_time_str or str(raw_time_str).strip() in ["None", "Pending", ""]:
                    return "Pending Check-in"
                try:
                    dt = datetime.strptime(str(raw_time_str)[:19], "%Y-%m-%d %H:%M:%S")
                    diff = (datetime.now() - dt).total_seconds()
                    if diff < 60:
                        return f"{raw_time_str} (LIVE - {int(diff)}s ago)"
                    elif diff < 3600:
                        return f"{raw_time_str} ({int(diff//60)}m ago)"
                    else:
                        return f"{raw_time_str} (Disconnected / {int(diff//3600)}h ago)"
                except Exception:
                    return str(raw_time_str)

            # Red Dot + Sticky Note for Out-of-Area Crews
            if not df_out.empty:
                text_out = [
                    f"  {r['team_code']} ({r.get('lead_name', 'PIC')})\n  {r.get('road_dist_km', r.get('dist_to_site_km', 0.0)):.1f} km road ({r.get('eta_to_site', 'ETA')}) to Site {r.get('assigned_site_id', 'Site')}\n  [FLAG: OUT OF AREA]"
                    for _, r in df_out.iterrows()
                ]
                hovers_out = [
                    f"<b>STICKY NOTE // FIELD DISPATCH</b><br>"
                    f"Team Code: <b>{r['team_code']}</b><br>"
                    f"Field Lead: <b>{r.get('lead_name', '-')}</b> ({r.get('contact_number', '-')})<br>"
                    f"Target Assigned Site: <b>{r.get('assigned_site_id', 'Unassigned')} — {r.get('assigned_site_name', '')}</b><br>"
                    f"Site Exact Coordinates: <b>{r.get('target_site_lat', 0.0):.5f}, {r.get('target_site_lon', 0.0):.5f}</b> ({r.get('assigned_district', '-')})<br>"
                    f"Road Distance to Target Site: <b>{r.get('road_dist_km', r.get('dist_to_site_km', 0.0)):.1f} km</b> (Direct Air: {r.get('air_dist_km', r.get('dist_to_site_km', 0.0)):.1f} km)<br>"
                    f"Realistic Travel ETA to Site: <b>{r.get('eta_to_site', 'Calculated upon dispatch')}</b> (via Fastest Accessible Road)<br>"
                    f"Geofence Audit: <span style='color:#DC2626;font-weight:800;'>FLAG: OUT OF AREA (&gt; 40 km from Site {r.get('assigned_site_id', 'Site')})</span><br>"
                    f"Operational Status: <b>{r.get('checkin_status', 'Standby')}</b><br>"
                    f"Crew GPS Telemetry: <b>{r['current_lat']:.5f}, {r['current_lon']:.5f}</b><br>"
                    f"Crew Address: <b>{r.get('current_address') or 'Resolving location...'}</b><br>"
                    f"Last Transmitted: <b>{_format_time_ago(r.get('last_checkin_at'))}</b>"
                    for _, r in df_out.iterrows()
                ]
                fig_radar.add_trace(go.Scattermap(
                    lat=df_out["current_lat"],
                    lon=df_out["current_lon"],
                    mode="markers+text",
                    marker=dict(size=18, color="#DC2626"),
                    text=text_out,
                    textposition="top right",
                    textfont=dict(size=11, color="#991B1B", family="Inter", weight="bold"),
                    name="Out of Area Crews (Red Dot)",
                    hoverinfo="text",
                    hovertext=hovers_out
                ))

            # Green Dot + Sticky Note for In-Area Crews
            if not df_in.empty:
                text_in = [
                    f"  {r['team_code']} ({r.get('lead_name', 'PIC')})\n  {r.get('road_dist_km', r.get('dist_to_site_km', 0.0)):.1f} km road ({r.get('eta_to_site', 'ETA')}) to Site {r.get('assigned_site_id', 'Site')}\n  [FLAG: IN AREA]"
                    for _, r in df_in.iterrows()
                ]
                hovers_in = [
                    f"<b>STICKY NOTE // FIELD DISPATCH</b><br>"
                    f"Team Code: <b>{r['team_code']}</b><br>"
                    f"Field Lead: <b>{r.get('lead_name', '-')}</b> ({r.get('contact_number', '-')})<br>"
                    f"Target Assigned Site: <b>{r.get('assigned_site_id', 'Unassigned')} — {r.get('assigned_site_name', '')}</b><br>"
                    f"Site Exact Coordinates: <b>{r.get('target_site_lat', 0.0):.5f}, {r.get('target_site_lon', 0.0):.5f}</b> ({r.get('assigned_district', '-')})<br>"
                    f"Road Distance to Target Site: <b>{r.get('road_dist_km', r.get('dist_to_site_km', 0.0)):.1f} km</b> (Direct Air: {r.get('air_dist_km', r.get('dist_to_site_km', 0.0)):.1f} km)<br>"
                    f"Realistic Travel ETA to Site: <b>{r.get('eta_to_site', 'Calculated upon dispatch')}</b> (via Fastest Accessible Road)<br>"
                    f"Geofence Audit: <span style='color:#059669;font-weight:800;'>FLAG: IN AREA (&le; 40 km to Site {r.get('assigned_site_id', 'Site')})</span><br>"
                    f"Operational Status: <b>{r.get('checkin_status', 'Standby')}</b><br>"
                    f"Crew GPS Telemetry: <b>{r['current_lat']:.5f}, {r['current_lon']:.5f}</b><br>"
                    f"Crew Address: <b>{r.get('current_address') or 'Resolving location...'}</b><br>"
                    f"Last Transmitted: <b>{_format_time_ago(r.get('last_checkin_at'))}</b>"
                    for _, r in df_in.iterrows()
                ]
                fig_radar.add_trace(go.Scattermap(
                    lat=df_in["current_lat"],
                    lon=df_in["current_lon"],
                    mode="markers+text",
                    marker=dict(size=18, color="#10B981"),
                    text=text_in,
                    textposition="top right",
                    textfont=dict(size=11, color="#065F46", family="Inter", weight="bold"),
                    name="In Area Crews (Green Dot)",
                    hoverinfo="text",
                    hovertext=hovers_in
                ))

        # Trace 4: Seaport Logistics Origin Hubs
        if selected_operator == "All":
            fig_radar.add_trace(go.Scattermap(
                lat=[PORT_DILI_COORDS[0], TANJUNG_PERAK_COORDS[0], BELAWAN_PORT_COORDS[0], BALIKPAPAN_PORT_COORDS[0]],
                lon=[PORT_DILI_COORDS[1], TANJUNG_PERAK_COORDS[1], BELAWAN_PORT_COORDS[1], BALIKPAPAN_PORT_COORDS[1]],
                mode="markers+text",
                marker=dict(size=14, color="#0F172A"),
                text=["Port Dili", "Tanjung Perak", "Belawan", "Balikpapan"],
                textposition="top right",
                textfont=dict(size=9, color="#0F172A", family="Inter"),
                name="Logistics Seaport Hubs",
                hoverinfo="text",
                hovertext=[
                    "<b>Port Dili Hub</b> (Telkomcel)",
                    "<b>Pelabuhan Tanjung Perak</b> (Mitratel Jawa)",
                    "<b>Pelabuhan Belawan</b> (XLSmart Sumatra)",
                    "<b>Pelabuhan Balikpapan</b> (IOH Kalimantan)"
                ]
            ))
        elif selected_operator == "Telkomcel":
            fig_radar.add_trace(go.Scattermap(
                lat=[PORT_DILI_COORDS[0]],
                lon=[PORT_DILI_COORDS[1]],
                mode="markers+text",
                marker=dict(size=16, color="#0F172A"),
                text=["Port Dili Hub"],
                textposition="top left",
                textfont=dict(size=10, color="#0F172A", family="Inter"),
                name="Port Dili Hub (Origin)",
                hoverinfo="text",
                hovertext="<b>LOGISTICS ORIGIN: Port Dili Terminal</b><br>Coordinates: -8.5520, 125.5711"
            ))
        elif selected_operator == "Mitratel":
            fig_radar.add_trace(go.Scattermap(
                lat=[TANJUNG_PERAK_COORDS[0]],
                lon=[TANJUNG_PERAK_COORDS[1]],
                mode="markers+text",
                marker=dict(size=16, color="#0F172A"),
                text=["Tanjung Perak Hub"],
                textposition="top right",
                textfont=dict(size=10, color="#0F172A", family="Inter"),
                name="Tanjung Perak Hub",
                hoverinfo="text",
                hovertext="<b>LOGISTICS ORIGIN: Pelabuhan Tanjung Perak (Surabaya)</b>"
            ))
        elif selected_operator == "XLSmart":
            fig_radar.add_trace(go.Scattermap(
                lat=[BELAWAN_PORT_COORDS[0]],
                lon=[BELAWAN_PORT_COORDS[1]],
                mode="markers+text",
                marker=dict(size=16, color="#0F172A"),
                text=["Belawan Hub"],
                textposition="top right",
                textfont=dict(size=10, color="#0F172A", family="Inter"),
                name="Belawan Hub",
                hoverinfo="text",
                hovertext="<b>LOGISTICS ORIGIN: Pelabuhan Belawan (Medan)</b>"
            ))
        elif selected_operator == "IOH":
            fig_radar.add_trace(go.Scattermap(
                lat=[BALIKPAPAN_PORT_COORDS[0]],
                lon=[BALIKPAPAN_PORT_COORDS[1]],
                mode="markers+text",
                marker=dict(size=16, color="#0F172A"),
                text=["Balikpapan Hub"],
                textposition="top right",
                textfont=dict(size=10, color="#0F172A", family="Inter"),
                name="Balikpapan Hub",
                hoverinfo="text",
                hovertext="<b>LOGISTICS ORIGIN: Pelabuhan Balikpapan (IKN Staging)</b>"
            ))

        fig_radar.update_layout(
            map=dict(
                style="open-street-map",
                center=map_center,
                zoom=map_zoom
            ),
            margin=dict(l=0, r=0, t=6, b=28),
            height=430,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
                xanchor="right",
                x=1,
                font=dict(size=10, family="Inter", color="#334155")
            )
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        # Spacing separator between radar map and telemetry feed to prevent visual overlap
        st.markdown("<div style='height: 24px; clear: both;'></div>", unsafe_allow_html=True)

        # Bottom section: Live Telemetry Feed Table & Quick Check-in Simulator
        c_feed, c_sim = st.columns([3.2, 1.8], gap="medium")

        with c_feed:
            st.markdown("""<div style="font-weight: 700; font-size: 0.84rem; color: #0F172A; margin-top: 4px; margin-bottom: 10px;">LIVE FIELD TELEMETRY FEED &amp; CHECK-IN AUDIT</div>""", unsafe_allow_html=True)

            if unique_teams_df.empty:
                st.info("No field crews registered yet. Register teams in Step 1 below to view real-time telemetry and geofence tracking.")
            else:
                feed_rows = []
                for _, r in unique_teams_df.iterrows():
                    last_time_raw = r['last_checkin_at']
                    live_indicator_badge = ""
                    if last_time_raw and str(last_time_raw).strip() not in ["None", "Pending", ""]:
                        try:
                            t_dt = datetime.strptime(str(last_time_raw)[:19], "%Y-%m-%d %H:%M:%S")
                            diff_sec = (datetime.now() - t_dt).total_seconds()
                            if diff_sec < 60:
                                live_indicator_badge = f'<span style="background: #ECFDF5; color: #059669; font-weight: 800; padding: 1px 5px; border-radius: 3px; font-size: 0.67rem;">LIVE ({int(diff_sec)}s ago)</span><br>'
                            elif diff_sec < 300:
                                live_indicator_badge = f'<span style="background: #EFF6FF; color: #0284C7; font-weight: 700; padding: 1px 5px; border-radius: 3px; font-size: 0.67rem;">ACTIVE ({int(diff_sec//60)}m ago)</span><br>'
                            elif diff_sec < 3600:
                                live_indicator_badge = f'<span style="background: #FFFBEB; color: #D97706; font-weight: 700; padding: 1px 5px; border-radius: 3px; font-size: 0.67rem;">IDLE ({int(diff_sec//60)}m ago)</span><br>'
                            else:
                                live_indicator_badge = f'<span style="background: #FEF2F2; color: #DC2626; font-weight: 700; padding: 1px 5px; border-radius: 3px; font-size: 0.67rem;">DISCONNECTED</span><br>'
                        except Exception:
                            pass
                        last_time_disp = f"{live_indicator_badge}<span style='color: #64748B; font-size: 0.70rem;'>{last_time_raw}</span>"
                    else:
                        last_time_disp = "<span style='color: #94A3B8; font-style: italic;'>Awaiting Check-in</span>"

                    coords = f"{r['current_lat']:.4f}, {r['current_lon']:.4f}" if pd.notna(r['current_lat']) else "No GPS"
                    status_raw = r['checkin_status'] or "Standby"

                    badge_bg = "#EFF6FF"
                    badge_fg = "#0284C7"
                    if "on-site" in status_raw.lower():
                        badge_bg = "#ECFDF5"
                        badge_fg = "#059669"
                    elif "completed" in status_raw.lower():
                        badge_bg = "#F5F3FF"
                        badge_fg = "#7C3AED"
                    elif "standby" in status_raw.lower():
                        badge_bg = "#F8FAFC"
                        badge_fg = "#64748B"

                    team_sites = fleet_df[fleet_df["team_code"] == r["team_code"]]["assigned_site_id"].dropna().unique().tolist()
                    site_id_val = r.get("assigned_site_id") or "Unassigned"
                    site_name_val = r.get("assigned_site_name") or ""
                    site_lat_val = r.get("target_site_lat")
                    site_lon_val = r.get("target_site_lon")
                    road_dist = r.get("road_dist_km")
                    eta_val = r.get("eta_to_site")

                    if team_sites and site_id_val != "Unassigned":
                        coord_sub = f" ({float(site_lat_val):.4f}, {float(site_lon_val):.4f})" if pd.notna(site_lat_val) else ""
                        name_sub = f" &bull; {site_name_val}" if site_name_val else ""
                        site_disp = f"<b>{site_id_val}</b>{name_sub}<br><span style='font-size: 0.69rem; color: #64748B;'>Site GPS:{coord_sub}</span>"
                        if pd.notna(road_dist) and road_dist is not None:
                            site_disp += f'<br><span style="font-size: 0.69rem; color: #0284C7; font-weight: 700;">Road to Site: {float(road_dist):.1f} km &bull; ETA: {eta_val or "-"}</span>'
                    else:
                        site_disp = "<span style='color: #94A3B8;'>Unassigned</span>"

                    geo_label = r.get("geofence_flag_label", "STANDBY")
                    geo_bg = r.get("geofence_badge_bg", "#F8FAFC")
                    geo_fg = r.get("geofence_badge_fg", "#64748B")
                    geo_border = r.get("geofence_badge_border", "#E2E8F0")

                    addr_val = r.get("current_address") or ""
                    addr_sub = f'<br><span style="font-size: 0.69rem; color: #64748B; font-family: Inter, sans-serif;">{addr_val}</span>' if addr_val else ""

                    feed_rows.append(
                        f'<tr style="border-bottom: 1px solid #F1F5F9; font-size: 0.77rem;">'
                        f'<td style="padding: 7px 8px; font-weight: 700; color: #0F172A;">{r["team_code"]}</td>'
                        f'<td style="padding: 7px 8px; color: #334155;">{r["lead_name"]}<br><span style="font-size: 0.70rem; color: #64748B;">{r["contact_number"]}</span></td>'
                        f'<td style="padding: 7px 8px;">{site_disp}</td>'
                        f'<td style="padding: 7px 8px;"><span style="background: {badge_bg}; color: {badge_fg}; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 0.70rem;">{status_raw}</span></td>'
                        f'<td style="padding: 7px 8px;"><span style="background: {geo_bg}; color: {geo_fg}; border: 1px solid {geo_border}; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 0.70rem;">{geo_label}</span></td>'
                        f'<td style="padding: 7px 8px; color: #475569; font-family: monospace;">{coords}{addr_sub}</td>'
                        f'<td style="padding: 7px 8px;">{last_time_disp}</td>'
                        f'</tr>'
                    )

                table_html = (
                    '<div style="border: 1px solid #E2E8F0; border-radius: 6px; overflow: hidden; background: #FFFFFF;">'
                    '<table style="width: 100%; border-collapse: collapse; text-align: left;">'
                    '<thead><tr style="background: #F8FAFC; border-bottom: 1px solid #E2E8F0; font-size: 0.72rem; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">'
                    '<th style="padding: 7px 8px;">Team</th>'
                    '<th style="padding: 7px 8px;">Lead PIC</th>'
                    '<th style="padding: 7px 8px;">Target Site</th>'
                    '<th style="padding: 7px 8px;">Telemetry Status</th>'
                    '<th style="padding: 7px 8px;">Geofence Flag</th>'
                    '<th style="padding: 7px 8px;">GPS Coordinates</th>'
                    '<th style="padding: 7px 8px;">Last Check-In</th>'
                    '</tr></thead><tbody>'
                    + "".join(feed_rows)
                    + '</tbody></table></div>'
                )
                st.markdown(table_html, unsafe_allow_html=True)

        with c_sim:
            st.markdown("""<div style="font-weight: 700; font-size: 0.84rem; color: #0F172A; margin-top: 4px; margin-bottom: 10px;">LIVE CHECK-IN &amp; DISPATCH CONTROLLER</div>""", unsafe_allow_html=True)

            if unique_teams_df.empty:
                st.info("No field crews registered. Register a team below in Step 1 to test dispatch and check-in simulation.")
            else:
                with st.container(border=True):
                    team_codes = unique_teams_df["team_code"].tolist()
                    sim_team = st.selectbox("Select Team:", options=team_codes, key="sim_checkin_team")
                    matched_teams = unique_teams_df[unique_teams_df["team_code"] == sim_team]
                    team_rec = matched_teams.iloc[0] if not matched_teams.empty else unique_teams_df.iloc[0]

                    all_sites_df = query_df("SELECT site_id, site_name, district, operator, lat, lon FROM timor_sites_100 ORDER BY site_id")
                    all_site_ids = all_sites_df["site_id"].tolist() if not all_sites_df.empty else ["DAX001"]
                    assigned_site = str(team_rec.get("assigned_site_id") or "").strip().upper()
                    if assigned_site in all_site_ids:
                        default_site_idx = all_site_ids.index(assigned_site)
                    else:
                        default_site_idx = 0

                    sim_site = st.selectbox(
                        "Target Site ID:",
                        options=all_site_ids,
                        index=default_site_idx,
                        key="sim_checkin_site_select",
                        format_func=lambda s: f"{s} — {all_sites_df[all_sites_df['site_id'] == s].iloc[0]['site_name']} ({all_sites_df[all_sites_df['site_id'] == s].iloc[0]['operator']})" if not all_sites_df.empty and s in all_site_ids else s
                    )
                    sim_status = st.selectbox(
                        "Check-In Status:",
                        options=["Confirmed - En Route", "On-Site Active (WIP)", "Task Completed", "Standby / At Base"],
                        key="sim_checkin_status"
                    )

                    sim_mode = st.radio(
                        "GPS Test Coordinates:",
                        options=["Current GPS", "In-Area (< 40 km)", "Out-of-Area (> 40 km Breach)"],
                        index=0,
                        horizontal=True,
                        key="sim_coord_preset"
                    )

                    chosen_site_row = all_sites_df[all_sites_df["site_id"] == sim_site].iloc[0]
                    target_site_lat = float(chosen_site_row["lat"])
                    target_site_lon = float(chosen_site_row["lon"])

                    if sim_mode == "In-Area (< 40 km)":
                        calc_lat = target_site_lat + 0.0500
                        calc_lon = target_site_lon + 0.0400
                    elif sim_mode == "Out-of-Area (> 40 km Breach)":
                        calc_lat = target_site_lat + 0.4500  # ~50 km away
                        calc_lon = target_site_lon + 0.3500  # combined ~62 km (> 40 km breach)
                    else:
                        calc_lat = float(team_rec["current_lat"]) if pd.notna(team_rec["current_lat"]) else target_site_lat
                        calc_lon = float(team_rec["current_lon"]) if pd.notna(team_rec["current_lon"]) else target_site_lon

                    from services.fleet_tracking_service import haversine_distance_km
                    preview_dist = haversine_distance_km(calc_lat, calc_lon, target_site_lat, target_site_lon)
                    if preview_dist > 40.0:
                        st.markdown(f"<div style='font-size:0.74rem; color:#DC2626; font-weight:700; margin-bottom:8px; padding:4px 8px; background:#FEF2F2; border:1px solid #FECACA; border-radius:4px;'>Calculated Distance: {preview_dist:.1f} km &bull; OUT OF AREA BREACH (&gt; 40 km)</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size:0.74rem; color:#059669; font-weight:700; margin-bottom:8px; padding:4px 8px; background:#ECFDF5; border:1px solid #A7F3D0; border-radius:4px;'>Calculated Distance: {preview_dist:.1f} km &bull; IN CORRIDOR (&le; 40 km)</div>", unsafe_allow_html=True)

                    col_lat, col_lon = st.columns(2)
                    with col_lat:
                        sim_lat = st.number_input("Latitude:", value=calc_lat, format="%.5f", key=f"sim_lat_{sim_team}_{sim_mode}_{sim_site}")
                    with col_lon:
                        sim_lon = st.number_input("Longitude:", value=calc_lon, format="%.5f", key=f"sim_lon_{sim_team}_{sim_mode}_{sim_site}")

                    if st.button("Transmit Live Check-In Telemetry", type="primary", use_container_width=True, key="btn_sim_checkin"):
                        ok, msg = FleetTrackingService.record_team_checkin(
                            team_code=sim_team,
                            site_id=sim_site,
                            lat=sim_lat,
                            lon=sim_lon,
                            status=sim_status,
                            user_agent="PMO Command Center Simulator",
                            notes=f"Check-in test under {sim_mode} preset"
                        )
                        if ok:
                            st.toast(f"Telemetry for {sim_team} updated on Radar.")
                            st.rerun()
                        else:
                            st.error(msg)

                    st.markdown("""<div style="font-size: 0.74rem; font-weight: 700; color: #475569; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase;">Or Paste Field WhatsApp Location Pin:</div>""", unsafe_allow_html=True)
                    sim_paste_col1, sim_paste_col2 = st.columns([3, 1])
                    with sim_paste_col1:
                        sim_pasted_pin = st.text_input(
                            "Paste WhatsApp Pin / Google Maps Link:",
                            placeholder="e.g. https://maps.google.com/?q=-7.6450,112.9050 or -7.6450, 112.9050",
                            key=f"sim_pasted_pin_{sim_team}",
                            label_visibility="collapsed"
                        )
                    with sim_paste_col2:
                        btn_sim_paste = st.button("Transmit Pin", key=f"btn_sim_paste_{sim_team}", use_container_width=True)

                    if btn_sim_paste:
                        clean_text = sim_pasted_pin.strip() if sim_pasted_pin else ""
                        if not clean_text:
                            st.error("Please paste a location URL or coordinates.")
                        elif "checkin=" in clean_text or "trycloudflare" in clean_text or "localhost:" in clean_text:
                            st.warning("That is the Field Check-In portal web address. In this box, please paste a Google Maps location link (e.g. https://maps.google.com/?q=-7.2575,112.7521) or raw coordinate numbers (e.g. -7.2575, 112.7521) sent by the field team via WhatsApp.")
                        else:
                            coords = FleetTrackingService.parse_location_string(clean_text)
                            if coords:
                                p_lat, p_lon = coords
                                ok, msg = FleetTrackingService.record_team_checkin(
                                    team_code=sim_team,
                                    site_id=sim_site,
                                    lat=p_lat,
                                    lon=p_lon,
                                    status=sim_status,
                                    user_agent="Command Center Simulator WhatsApp Pin",
                                    notes="Updated via WhatsApp pin in PMO controller"
                                )
                                if ok:
                                    st.toast(f"Updated live location for {sim_team} from WhatsApp pin ({p_lat:.4f}, {p_lon:.4f}).")
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("Could not parse coordinates from the pasted link. Please paste a link like https://maps.google.com/?q=-7.6450,112.9050 or '-7.6450, 112.9050'.")

                    checkin_test_url = FleetTrackingService.generate_checkin_url(sim_team, sim_site)
                    st.markdown(f"""
                        <div style="margin-top: 10px; padding: 8px 10px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 0.72rem; color: #475569;">
                        <div style="font-weight: 700; color: #0F172A; margin-bottom: 2px;">Mobile Field Check-In URL:</div>
                        <div style="font-family: monospace; color: #0284C7; word-break: break-all; margin-bottom: 4px;">
                            <a href="{checkin_test_url}" target="_blank" style="color: #0284C7; text-decoration: underline;">{checkin_test_url}</a>
                        </div>
                        <div style="color: #64748B;">
                            This link is automatically attached to WhatsApp Work Orders. When field crews open the link on mobile, their device GPS coordinates stream live to this Command Radar.
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                    st.markdown("""<div style="font-size: 0.74rem; font-weight: 700; color: #0F172A; margin-top: 12px; margin-bottom: 6px; text-transform: uppercase;">PMO Controller Fleet Authority:</div>""", unsafe_allow_html=True)
                    col_ctl1, col_ctl2, col_ctl3 = st.columns(3)
                    with col_ctl1:
                        if st.button("End Tracking & Complete", key=f"btn_ctrl_end_{sim_team}", use_container_width=True):
                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            execute_write("""
                                UPDATE paas_field_teams 
                                SET checkin_status = 'Task Completed (Closed by PMO Controller)',
                                    status = 'Standby',
                                    updated_at = ?
                                WHERE team_code = ?
                            """, (now_str, sim_team))
                            execute_write("""
                                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                                VALUES ('Controller', ?, 'TASK_TERMINATION', 'PMO Controller officially terminated live tracking and marked task completed', 'SUCCESS')
                            """, (sim_team,))
                            st.toast(f"Tracking officially terminated for {sim_team}. Assignment marked Completed.")
                            st.rerun()
                    with col_ctl2:
                        if st.button("Reactivate Tracking", key=f"btn_ctrl_reactivate_{sim_team}", use_container_width=True):
                            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            execute_write("""
                                UPDATE paas_field_teams 
                                SET checkin_status = 'Confirmed - En Route',
                                    status = 'Active',
                                    updated_at = ?
                                WHERE team_code = ?
                            """, (now_str, sim_team))
                            st.toast(f"Tracking reactivated for {sim_team}.")
                            st.rerun()
                    with col_ctl3:
                        if st.button("Reset Device Lock", key=f"btn_ctrl_reset_bind_{sim_team}", use_container_width=True):
                            FleetTrackingService.reset_device_binding(sim_team, sim_site)
                            st.toast(f"Device lock cleared for {sim_team} at {sim_site}. Next device to connect will be bound.")
                            st.rerun()

                    binding_info = FleetTrackingService.get_device_binding_status(sim_team, sim_site)
                    if binding_info:
                        dev_sub = str(binding_info.get("bound_device_id", ""))[:8]
                        bound_time = str(binding_info.get("bound_at", ""))
                        st.markdown(f"""
                            <div style="font-size: 0.70rem; color: #0284C7; background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 4px; padding: 4px 8px; margin-top: 6px;">
                                <b>1-Device Lock:</b> Locked to device <code>{dev_sub}...</code> (Bound: {bound_time}). Shared links to other phones will be blocked.
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            <div style="font-size: 0.70rem; color: #64748B; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px 8px; margin-top: 6px;">
                                <b>1-Device Lock:</b> Unbound (First smartphone to transmit will lock this assignment).
                            </div>
                        """, unsafe_allow_html=True)


def render_plan_tab():
    import re
    def clean_status(text) -> str:
        if not text:
            return ""
        clean = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27ff]', '', str(text))
        return clean.strip(" \t\n\r•-")

    current_default_op = st.session_state.get("global_operator_select") or st.session_state.get("noc_selected_operator", "All")
    if current_default_op not in ["All", "Telkomcel", "XLSmart", "IOH", "Mitratel"]:
        current_default_op = "All"

    op_data = RolloutOperationsService.get_daily_operational_summary(current_default_op)
    total_sites = op_data.get("total_sites", 0)
    c_handover = op_data.get("c_handover", 0)
    c_power = op_data.get("c_power", 0)
    c_testing = op_data.get("c_testing", 0)
    c_civil = op_data.get("c_civil", 0)
    c_staged = op_data.get("c_staged", 0)
    c_shipping = op_data.get("c_shipping", 0)
    c_blocked = op_data.get("c_blocked", 0)
    active_crews = op_data.get("active_crews_count", 5)
    total_specialists = op_data.get("total_specialists", 34)
    field_teams = op_data.get("field_teams", [])
    blockers = op_data.get("blockers", [])
    weekly_comm = op_data.get("weekly_commissioning", op_data.get("today_commissioning", []))
    weekly_atp = op_data.get("weekly_atp", op_data.get("today_atp", []))
    micro_pipeline = op_data.get("micro_pipeline", {})
    velocity_run_rate = op_data.get("velocity_run_rate", 1.2)
    weekly_actual = op_data.get("weekly_actual", 4)
    weekly_target = op_data.get("weekly_target", 5)

    badge_label = f"{total_sites} Sites Target" if total_sites > 0 else "100 Sites Target"
    selected_operator = render_unified_module_header(
        module_label="PAAS ROLLOUT",
        breadcrumb_trail=f'Overview &nbsp;&rsaquo;&nbsp; PaaS Rollout &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">{current_default_op}</b> &nbsp;&rsaquo;&nbsp; <b>Milestone Check Point & Weekly Completion Command War Room</b>',
        badge_text=badge_label,
        badge_bg="#EFF6FF",
        badge_color="#1D4ED8",
        badge_border="#BFDBFE"
    )

    # Ensure op_data reflects selected_operator
    op_data = RolloutOperationsService.get_daily_operational_summary(selected_operator)
    total_sites = op_data.get("total_sites", 0)
    c_handover = op_data.get("c_handover", 0)
    c_power = op_data.get("c_power", 0)
    c_testing = op_data.get("c_testing", 0)
    c_civil = op_data.get("c_civil", 0)
    c_staged = op_data.get("c_staged", 0)
    c_shipping = op_data.get("c_shipping", 0)
    c_blocked = op_data.get("c_blocked", 0)
    active_crews = op_data.get("active_crews_count", 0)
    total_specialists = op_data.get("total_specialists", 0)
    field_teams = op_data.get("field_teams", [])
    blockers = op_data.get("blockers", [])
    weekly_comm = op_data.get("weekly_commissioning", op_data.get("today_commissioning", []))
    weekly_atp = op_data.get("weekly_atp", op_data.get("today_atp", []))
    velocity_run_rate = op_data.get("velocity_run_rate", 1.2)
    weekly_actual = op_data.get("weekly_actual", 4)
    weekly_target = op_data.get("weekly_target", 5)

    all_sites_df = op_data.get("all_sites_df", pd.DataFrame())
    unassigned_df = op_data.get("unassigned_sites_df", pd.DataFrame())
    escalated_df = op_data.get("escalated_sites_df", pd.DataFrame())
    dropped_df = op_data.get("dropped_sites_df", pd.DataFrame())
    n_unassigned = len(unassigned_df) if not unassigned_df.empty else 0

    # Applied Energy NOC Integration Live Ribbon for Telkomcel Timor-Leste
    if selected_operator in ["All", "Telkomcel"]:
        noc_svc = NocIntegrationService()
        noc_svc.seed_initial_baseline_if_empty()
        noc_status = noc_svc.get_sync_status()
        st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-left: 4px solid #2563EB; border-radius: 6px; padding: 10px 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-size: 0.82rem; color: #0F172A;">
                    <span style="font-weight: 800; color: #1D4ED8; letter-spacing: 0.3px;">LIVE NOC BRIDGE:</span>
                    <span style="margin-left: 6px; font-weight: 600;">telkomceltl.appliedenergynoc.com</span>
                    <span style="margin-left: 10px; color: #64748B;">&bull; User: <b>supriyanto (Supriy Anto)</b> &bull; Monitored: <b>2 On Air Sites (MAINA 2: 232V AC | TRILOCA: 235V AC)</b> &bull; Uptime SLA: <b style="color: #10B981;">{noc_status.get('average_uptime', 100.0):.2f}%</b></span>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="font-size: 0.72rem; font-weight: 700; color: #065F46; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 2px 8px; border-radius: 4px;">
                        STATUS: {noc_status.get('status', 'CONNECTED')}
                    </span>
                    <a href="?nav=site_ops" target="_self" style="font-size: 0.74rem; font-weight: 700; color: #1D4ED8; text-decoration: none; padding: 3px 10px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 4px;">
                        Open NOC Bridge Console &rsaquo;
                    </a>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # MINIMALIST VISUAL OPERATIONAL SUMMARY (CHARTS INSTEAD OF BULKY CARDS)
    # =========================================================================
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    # Chart 1: PaaS Lifecycle Pipeline Donut (Pure PaaS Status Breakdown = 100% of 180 Sites)
    donut_slices = []
    if c_handover > 0:
        donut_slices.append({"stage": "Handover Live (COD)", "count": c_handover, "color": "#10B981"})
    if c_testing > 0:
        donut_slices.append({"stage": "Testing & QA ATP", "count": c_testing, "color": "#F59E0B"})
    if c_power > 0:
        donut_slices.append({"stage": "Power I&C Active", "count": c_power, "color": "#6366F1"})
    c_staged_total = c_staged + c_shipping
    if c_staged_total > 0:
        donut_slices.append({"stage": "Survey & Material Staged", "count": c_staged_total, "color": "#0284C7"})
    if c_blocked > 0:
        donut_slices.append({"stage": "Blocked / Dependency", "count": c_blocked, "color": "#EF4444"})

    if not donut_slices:
        donut_slices = [{"stage": "All Sites Baseline", "count": max(total_sites, 1), "color": "#CBD5E1"}]

    df_paas_donut = pd.DataFrame(donut_slices)
    pct_live = round((c_handover / max(total_sites, 1)) * 100)

    fig_paas_donut = go.Figure(data=[go.Pie(
        labels=df_paas_donut["stage"],
        values=df_paas_donut["count"],
        hole=0.66,
        marker=dict(colors=df_paas_donut["color"], line=dict(color="#FFFFFF", width=2)),
        textinfo="none",
        hoverinfo="label+value+percent"
    )])
    fig_paas_donut.update_layout(
        showlegend=False,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        annotations=[dict(
            text=f"<b>{pct_live}%</b><br><span style='font-size:9.5px;color:#64748B;'>{c_handover}/{total_sites} Live</span>",
            x=0.5, y=0.5, font_size=15, font_color="#0F172A", showarrow=False
        )],
        margin=dict(t=8, b=8, l=8, r=8),
        height=165
    )

    # Chart 2: Fleet Workload & Assignment Horizontal Bar
    total_assigned_sites = sum(len(t.get('assigned_sites', [])) for t in field_teams)
    avg_load = total_assigned_sites / max(len(field_teams), 1)

    if field_teams:
        workload_rows = []
        for t in field_teams:
            short_name = t["team_name"].split("(")[0].strip()
            num_sites = len(t.get("assigned_sites", []))
            workload_rows.append({
                "team": short_name,
                "sites": num_sites,
                "lead": t["lead_name"],
                "pax": t.get("crew_size", 4)
            })
        df_wl = pd.DataFrame(workload_rows)
        max_wl = max(df_wl["sites"].max() if not df_wl.empty else 5, 5)
        
        fig_paas_workload = go.Figure(go.Bar(
            x=df_wl["sites"],
            y=df_wl["team"],
            orientation="h",
            marker=dict(color="#0284C7", line=dict(color="#0369A1", width=1)),
            text=[f" <b>{s}</b> sites" for s in df_wl["sites"]],
            textposition="outside",
            cliponaxis=False,
            hovertext=[f"{r['team']}<br>PIC: {r['lead']} ({r['pax']} pax)<br>Assigned: {r['sites']} Sites" for _, r in df_wl.iterrows()],
            hoverinfo="text"
        ))
        fig_paas_workload.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=0, r=45, t=8, b=8),
            height=165,
            xaxis=dict(showgrid=False, showticklabels=False, range=[0, max_wl * 1.35]),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#334155"))
        )
    else:
        fig_paas_workload = go.Figure(go.Bar(
            x=[total_sites],
            y=["Backlog Pool"],
            orientation="h",
            marker=dict(color="#CBD5E1"),
            text=[f" <b>{total_sites}</b> unassigned sites"],
            textposition="inside",
            hovertext=[f"Backlog Pool: {total_sites} Unassigned Sites<br>0 Active Field Teams"],
            hoverinfo="text"
        ))
        fig_paas_workload.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=0, r=20, t=8, b=8),
            height=165,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(size=10, color="#64748B")),
            annotations=[dict(
                text="No active teams &bull; Ready for assignment",
                x=0.5, y=-0.25, xref="paper", yref="paper",
                showarrow=False, font=dict(size=10, color="#94A3B8")
            )]
        )

    # Chart 3: Weekly Milestone Velocity & Run-Rate Gauge (Zero-Clipping Centered)
    fig_paas_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=weekly_actual,
        domain={'x': [0.05, 0.95], 'y': [0.05, 0.95]},
        number={'suffix': f" / {weekly_target}", 'font': {'size': 26, 'color': '#0F172A'}},
        gauge={
            'axis': {'range': [0, max(weekly_target, weekly_actual) + 2], 'tickwidth': 1, 'tickcolor': "#94A3B8", 'tickfont': {'size': 9}},
            'bar': {'color': "#10B981" if weekly_actual >= weekly_target else "#0284C7"},
            'bgcolor': "#F1F5F9",
            'borderwidth': 1,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, weekly_target], 'color': '#E0F2FE'},
            ],
            'threshold': {
                'line': {'color': "#10B981", 'width': 3},
                'thickness': 0.75,
                'value': weekly_target
            }
        }
    ))
    fig_paas_gauge.update_layout(
        height=165,
        margin=dict(t=10, b=10, l=12, r=12),
        paper_bgcolor="#FFFFFF",
        font=dict(color="#0F172A", size=10)
    )

    with st.container(border=True):
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px solid #F1F5F9;">
                <div style="font-weight: 700; font-size: 0.85rem; color: #0F172A; letter-spacing: 0.3px;">
                    PAAS ROLLOUT OPERATIONAL VISUAL RADAR
                </div>
                <div style="font-size: 0.75rem; color: #64748B;">
                    <b style="color: #0284C7;">{total_sites} Total Sites</b> &bull; 
                    <b style="color: #10B981;">{c_handover} Live COD</b> &bull; 
                    <b style="color: #6366F1;">{c_power + c_testing} In-Flight</b> &bull; 
                    <b style="color: #0284C7;">{len(field_teams)} Active Crews</b> &bull; 
                    <b style="color: {'#EF4444' if c_blocked > 0 else '#64748B'};">{c_blocked} Blockers</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

        c_v1, c_v2, c_v3 = st.columns([1.1, 1.25, 0.95], gap="medium")
        with c_v1:
            st.caption("**Lifecycle Pipeline Distribution**")
            st.plotly_chart(fig_paas_donut, use_container_width=True)
            st.markdown(f"""
                <div style="display: flex; justify-content: center; gap: 8px; font-size: 0.70rem; color: #475569; margin-top: -6px;">
                    <span><span style="color: #10B981;">●</span> Live: {c_handover}</span>
                    <span><span style="color: #F59E0B;">●</span> QA: {c_testing}</span>
                    <span><span style="color: #6366F1;">●</span> I&C: {c_power}</span>
                    <span><span style="color: #0284C7;">●</span> Staged: {c_staged_total}</span>
                    <span><span style="color: #EF4444;">●</span> Blocked: {c_blocked}</span>
                </div>
            """, unsafe_allow_html=True)

        with c_v2:
            st.caption("**Fleet Crew Workload & Progress**")
            st.plotly_chart(fig_paas_workload, use_container_width=True)
            if field_teams:
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; font-size: 0.70rem; color: #64748B; margin-top: -6px;">
                        <span>Total Deployed: <b>{len(field_teams)} Teams</b> ({total_specialists} Specialists)</span>
                        <span>Assigned: <b>{total_assigned_sites} Sites</b> (Avg {avg_load:.1f}/Team)</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="text-align: center; font-size: 0.72rem; color: #94A3B8; margin-top: -6px;">
                        Fleet empty (0 teams). Add crew teams in Step 1 to distribute site workload.
                    </div>
                """, unsafe_allow_html=True)

        with c_v3:
            st.caption("**Weekly Milestone Velocity & Run-Rate**")
            st.plotly_chart(fig_paas_gauge, use_container_width=True)
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.70rem; color: #64748B; margin-top: -6px;">
                    <span>Target: <b>{weekly_target} Sites/Wk</b></span>
                    <span>Pace: <b style="color: {'#10B981' if weekly_actual >= weekly_target else '#D97706'};">{'Ahead of Pace' if weekly_actual >= weekly_target else 'On-Track'} ({round((weekly_actual/max(weekly_target,1))*100)}%)</b></span>
                </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # LIVE FIELD FLEET TRACKING & GPS TELEMETRY RADAR
    # =========================================================================
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    render_fleet_tracking_radar(selected_operator)

    # =========================================================================
    # STEP 1: INITIAL SITE ASSIGNMENT TO TEAM OWNER
    # =========================================================================
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-top: 3px solid #0284C7; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.95rem; color: #0F172A; letter-spacing: 0.3px;">
                    1. INITIAL SITE ASSIGNMENT TO CREW OWNER
                </span>
                <span style="font-size: 0.74rem; font-weight: 700; color: #0284C7; background: #EFF6FF; border: 1px solid #BFDBFE; padding: 3px 8px; border-radius: 4px;">
                    Delegation from Start
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #64748B;">
                Assign tower sites to dedicated field crews from the start. Once assigned, the team lead assumes end-to-end accountability for material staging, power I&C installation, and acceptance testing.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Dynamic Team Options loaded directly from database-backed field_teams
    team_options = [
        (t["team_code"], f"{t['team_name']} — PIC: {t['lead_name']} ({t.get('crew_size', 4)} pax)")
        for t in field_teams
    ]
    team_dict = {t[0]: t[1] for t in team_options}

    # =========================================================================
    # QUICK FLEET CONTROL & REMOVE ALL FLEET TOOLBAR
    # =========================================================================
    c_fl_stat, c_fl_action = st.columns([3.2, 1.8])
    with c_fl_stat:
        st.markdown(f"""
            <div style="font-size: 0.82rem; color: #334155; padding: 6px 0;">
                Active Fleet: <b>{len(field_teams)} Team(s)</b> &bull; Assigned: <b>{total_assigned_sites} Sites</b>
            </div>
        """, unsafe_allow_html=True)
    with c_fl_action:
        if field_teams:
            with st.popover("Remove All Fleet (Reset to 0)", use_container_width=True):
                st.markdown("<span style='font-size: 0.88rem; font-weight: 800; color: #DC2626;'>Confirm Fleet Purge</span>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 0.78rem; color: #64748B; margin-bottom: 8px;'>This action will remove <b>all {len(field_teams)} active teams</b> and revert all sites to <b>Unassigned</b> so you can configure teams from scratch.</div>", unsafe_allow_html=True)
                if st.button("Confirm Purge All Teams Now", type="primary", use_container_width=True, key="btn_quick_remove_all_fleet"):
                    ok, msg = RolloutOperationsService.clear_all_field_teams(unassign_sites=True)
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            if st.button("Restore Default Baseline Teams", use_container_width=True, key="btn_quick_restore_baseline"):
                ok, msg = RolloutOperationsService.reset_baseline_teams()
                if ok:
                    st.toast(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # =========================================================================
    # DYNAMIC FLEET MANAGEMENT DRAWER (ADD / REMOVE FIELD CREW TEAMS)
    # =========================================================================
    with st.expander(f"Manage Field Crew Fleet (Add New Team / Remove Team) — {len(field_teams)} Active Teams", expanded=(len(field_teams) == 0)):
        tab_add_crew, tab_manage_crew = st.tabs([
            "Add New Crew Team",
            "Active Crew Fleet & Remove Team"
        ])

        with tab_add_crew:
            st.markdown("""
                <div style="font-size: 0.82rem; color: #475569; margin-bottom: 12px;">
                    Register a new field crew team to handle site rollout activities. Once registered, this team becomes immediately selectable for site assignments and appears in the operational workboard.
                </div>
            """, unsafe_allow_html=True)
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                new_team_name = st.text_input(
                    "Team Name:",
                    placeholder="e.g. Team Eta (Solar Hybrid & Generator I&C)",
                    key="input_new_team_name"
                )
                new_team_code = st.text_input(
                    "Team Code (Unique Identifier):",
                    placeholder="e.g. TEAM-ETA",
                    help="Alphanumeric identifier (e.g. TEAM-ETA, TEAM-SOLAR). Will be prefixed with TEAM- if omitted.",
                    key="input_new_team_code"
                )
                new_lead_pic = st.text_input(
                    "Lead Field Engineer / PIC:",
                    placeholder="e.g. Joao Da Silva",
                    key="input_new_lead_pic"
                )
            with col_t2:
                new_spec = st.selectbox(
                    "Primary Specialization:",
                    options=[
                        "DC Power & Rectifier I&C",
                        "Power I&C Lead & Multi-Site Coordination",
                        "Battery Bank Commissioning & Testing",
                        "Solar PV & Hybrid Power Installation",
                        "QA, ATP Verification & Sign-off",
                        "Rapid Blocker Resolution & Civil Dependencies",
                        "JIT Material Logistics & Spares",
                        "General Field Operations"
                    ],
                    key="select_new_team_spec"
                )
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    new_crew_size = st.number_input(
                        "Crew Size (Specialists):",
                        min_value=1,
                        max_value=20,
                        value=4,
                        step=1,
                        key="input_new_crew_size"
                    )
                with col_sub2:
                    new_contact = st.text_input(
                        "PIC Contact / WhatsApp:",
                        placeholder="+670 7712-3456",
                        key="input_new_team_contact"
                    )

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("Add Crew Team to Fleet", type="primary", key="btn_create_new_team", use_container_width=True):
                if not new_team_name.strip() or not new_lead_pic.strip():
                    st.error("Please provide both Team Name and Lead Field Engineer (PIC).")
                else:
                    code_to_use = new_team_code.strip() if new_team_code.strip() else None
                    ok, msg = RolloutOperationsService.add_field_team(
                        team_name=new_team_name.strip(),
                        lead_name=new_lead_pic.strip(),
                        specialization=new_spec,
                        crew_size=int(new_crew_size),
                        contact_number=new_contact.strip() if new_contact.strip() else "-",
                        team_code=code_to_use
                    )
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with tab_manage_crew:
            if not field_teams:
                st.info("All field crew teams have been removed. The fleet is currently empty (0 active teams). You can now simulate adding teams from scratch in the Add New Crew Team tab above.")
                if st.button("Restore Default Baseline Teams (Alpha - Zeta)", key="btn_restore_baseline_zero"):
                    ok, msg = RolloutOperationsService.reset_baseline_teams()
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.markdown("""
                    <div style="font-size: 0.82rem; color: #475569; margin-bottom: 12px;">
                        Review current fleet roster or decommission a field crew team. If removing a team that currently holds assigned sites, you can choose to reassign their sites to another active team or return them to the unassigned backlog pool.
                    </div>
                """, unsafe_allow_html=True)

                roster_rows = []
                for t in field_teams:
                    roster_rows.append({
                        "Team Code": t["team_code"],
                        "Team Name": t["team_name"],
                        "Lead PIC": t["lead_name"],
                        "Crew Size": f"{t.get('crew_size', 4)} Specialists",
                        "Specialization": t.get("specialization", "Field Ops"),
                        "Contact": t.get("contact_number", "-"),
                        "Assigned Sites": f"{len(t.get('assigned_sites', []))} Sites",
                        "Status": t.get("status", "Active")
                    })
                df_roster = pd.DataFrame(roster_rows)
                st.dataframe(df_roster, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("##### Decommission / Remove Field Team")
                
                c_rm1, c_rm2, c_rm3 = st.columns([3, 3, 2])
                with c_rm1:
                    sel_rm_code = st.selectbox(
                        "Select Team to Remove:",
                        options=[t["team_code"] for t in field_teams],
                        format_func=lambda code: f"{code} — {next((t['team_name'] for t in field_teams if t['team_code'] == code), code)}",
                        key="sel_remove_team_code"
                    )
                
                team_to_rm = next((t for t in field_teams if t["team_code"] == sel_rm_code), None)
                rm_sites_count = len(team_to_rm.get("assigned_sites", [])) if team_to_rm else 0

                with c_rm2:
                    other_teams = [t for t in field_teams if t["team_code"] != sel_rm_code]
                    if other_teams:
                        reassign_options = [("UNASSIGN", "Return sites to Unassigned Backlog")] + [
                            (t["team_code"], f"Reassign to {t['team_name']}") for t in other_teams
                        ]
                    else:
                        reassign_options = [("UNASSIGN", "Return sites to Unassigned Backlog (Last remaining team)")]

                    sel_reassign_target = st.selectbox(
                        f"Site Allocation Strategy ({rm_sites_count} sites affected):",
                        options=[o[0] for o in reassign_options],
                        format_func=lambda o: dict(reassign_options).get(o, o),
                        help="Choose where to reallocate this team's currently assigned sites.",
                        key="sel_rm_reassign_target"
                    )

                with c_rm3:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("Remove Team from Fleet", type="secondary", use_container_width=True, key="btn_confirm_remove_team"):
                        target_code = None if sel_reassign_target == "UNASSIGN" else sel_reassign_target
                        ok, msg = RolloutOperationsService.remove_field_team(sel_rm_code, reassign_to_team_code=target_code)
                        if ok:
                            st.toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                st.markdown("<hr style='margin: 18px 0 14px 0; border: none; border-bottom: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                        <span style="font-weight: 800; font-size: 0.88rem; color: #991B1B;">Danger Zone: Remove All Fleet Teams (Reset to 0)</span>
                        <div style="font-size: 0.77rem; color: #B91C1C; margin-top: 2px;">
                            Deletes <b>all {len(field_teams)} active teams</b> and reverts all sites to <b>Unassigned</b> so you can configure new field teams from scratch.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                with st.popover("Remove All Fleet Teams (Reset to 0)", use_container_width=True):
                    st.markdown("<span style='font-size: 0.88rem; font-weight: 800; color: #DC2626;'>Confirm Purge of All Teams</span>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 0.78rem; color: #64748B; margin-bottom: 10px;'>This action will remove all registered field teams ({len(field_teams)} teams) and clear all site crew assignments so you can start clean.</div>", unsafe_allow_html=True)
                    if st.button("Confirm Purge All Teams Now", type="primary", use_container_width=True, key="btn_confirm_tab_remove_all"):
                        ok, msg = RolloutOperationsService.clear_all_field_teams(unassign_sites=True)
                        if ok:
                            st.toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    n_unassigned = len(unassigned_df) if not unassigned_df.empty else 0
    
    # Filter toggle for assignment dropdown
    c_toggle, c_auto = st.columns([3, 1.2])
    with c_toggle:
        only_unassigned = st.checkbox(
            f"Show unassigned sites only ({n_unassigned} remaining)",
            value=True if n_unassigned > 0 else False,
            key="chk_only_unassigned"
        )
    with c_auto:
        if n_unassigned > 0:
            if st.button("Auto-Distribute Baseline", help=f"Evenly allocate unassigned sites across active field teams ({len(field_teams)} teams, 4 sites per team).", use_container_width=True, disabled=len(field_teams) == 0, key="btn_auto_distribute"):
                count_allocated = RolloutOperationsService.auto_distribute_initial_baseline(selected_operator, limit_per_team=4)
                st.toast(f"Allocated {count_allocated} sites across active field teams!")
                st.rerun()

    # Determine candidate sites for assignment
    if only_unassigned and not unassigned_df.empty:
        df_assign_candidates = unassigned_df
    else:
        df_assign_candidates = all_sites_df

    col_site, col_team, col_btn = st.columns([3.5, 3.2, 1.8])
    with col_site:
        if not df_assign_candidates.empty:
            site_pick_options = [
                (
                    r["site_id"],
                    f"[{r['site_id']}] {r['site_name']} ({r['district']}) | {clean_status(r['paas_status'])} | Owner: {team_dict.get(r['assigned_team'], 'Unassigned' if pd.isna(r['assigned_team']) or r['assigned_team'] == '' else r['assigned_team'])}"
                )
                for _, r in df_assign_candidates.iterrows()
            ]
            sel_site_tuple = st.selectbox(
                "Select Site to Assign:",
                options=site_pick_options,
                format_func=lambda x: x[1],
                key="sel_assign_site_pick"
            )
            selected_assign_site_id = sel_site_tuple[0] if sel_site_tuple else ""
        else:
            st.info("No sites available for assignment.")
            selected_assign_site_id = ""

    with col_team:
        if team_options:
            sel_team_code = st.selectbox(
                "Assign to Team Owner (PIC):",
                options=[t[0] for t in team_options],
                format_func=lambda code: team_dict[code],
                key="sel_assign_team_pick"
            )
        else:
            st.selectbox(
                "Assign to Team Owner (PIC):",
                options=["NO_TEAM"],
                format_func=lambda _: "No Active Teams (Register team above first)",
                disabled=True,
                key="sel_assign_team_pick_empty"
            )
            sel_team_code = ""
            st.caption("Fleet roster is empty. Register your team with your real WhatsApp number in 'Add New Crew Team' tab above to test live dispatch.")

    with col_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Assign Site to Team", type="primary", use_container_width=True, disabled=not bool(selected_assign_site_id) or not bool(sel_team_code), key="btn_submit_assign"):
            success = RolloutOperationsService.assign_site_to_team(selected_assign_site_id, sel_team_code, user="PMO Command Center")
            if success:
                wo_res = NotificationDispatcher().dispatch_site_work_order(selected_assign_site_id, sel_team_code)
                st.session_state["last_dispatched_wo"] = wo_res
                st.toast(f"Site {selected_assign_site_id} successfully assigned to {team_dict[sel_team_code].split('—')[0].strip()}!")
                st.rerun()
            else:
                st.error("Failed to assign site.")

    # WhatsApp Work Order Dispatch Card (Persistent until dismissed)
    if st.session_state.get("last_dispatched_wo"):
        last_wo = st.session_state["last_dispatched_wo"]
        checkin_url_disp = last_wo.get("checkin_url", "")
        st.markdown(f"""
            <div style="background: #F0FDF4; border: 1.5px solid #22C55E; border-left: 5px solid #16A34A; border-radius: 8px; padding: 14px 18px; margin: 12px 0 16px 0; box-shadow: 0 1px 4px rgba(22,163,74,0.08);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="font-weight: 800; font-size: 0.95rem; color: #15803D;">
                            WORK ORDER DISPATCH READY — [{last_wo.get('site_id')}] {last_wo.get('site_name')}
                        </span>
                        <div style="font-size: 0.8rem; color: #166534; margin-top: 4px;">
                            Work order automatically generated for <b>{last_wo.get('team_name')}</b> | PIC: <b>{last_wo.get('lead_name')}</b> (WhatsApp: <b>+{last_wo.get('phone')}</b>).
                        </div>
                        <div style="font-size: 0.75rem; color: #15803D; margin-top: 6px;">
                            Confirmation &amp; Live GPS Link: <a href="{checkin_url_disp}" target="_blank" style="color: #047857; font-weight: 700; text-decoration: underline;">{checkin_url_disp}</a>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        col_wo_btn, col_wo_dismiss = st.columns([3, 1])
        with col_wo_btn:
            st.link_button(
                f"Dispatch Work Order via WhatsApp to {last_wo.get('lead_name')} (+{last_wo.get('phone')})",
                last_wo.get("wa_link", "#"),
                type="primary",
                use_container_width=True
            )
        with col_wo_dismiss:
            if st.button("Dismiss Notification", key="btn_dismiss_wo_banner", use_container_width=True):
                del st.session_state["last_dispatched_wo"]
                st.rerun()
        with st.expander("Preview WhatsApp Work Order Message Format", expanded=False):
            st.code(last_wo.get("message_text", ""), language="markdown")

    # =========================================================================
    # STEP 2 & 3: TEAM WORKBOARD — STATUS MANAGEMENT & BLOCKER CONTROL
    # =========================================================================
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-top: 3px solid #10B981; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.95rem; color: #0F172A; letter-spacing: 0.3px;">
                    2. TEAM WORKBOARD & STATUS MANAGEMENT
                </span>
                <span style="font-size: 0.74rem; font-weight: 700; color: #059669; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 3px 8px; border-radius: 4px;">
                    Owned Site Operations
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #64748B;">
                Filter by team to review assigned sites. Manage site progress directly (Power I&C -> ATP QA -> Completed), or trigger decisive action if blocked: <b>Escalate</b> (flag for PMO intervention) or <b>Drop</b> (remove from crew queue).
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not field_teams:
        st.info("No field teams currently in fleet. Open **'Manage Field Crew Fleet'** in Step 1 above to register your first crew team.")
        filtered_teams = []
    else:
        seen_labels = set()
        team_filter_names = []
        for t in field_teams:
            short_n = t["team_name"].split("(")[0].strip()
            if short_n in seen_labels:
                short_n = f"{t['team_code']}: {short_n}"
            seen_labels.add(short_n)
            t["_filter_label"] = short_n
            team_filter_names.append(short_n)
        team_filter_names.append("All Crews Overview")

        selected_crew_filter = st.radio(
            "Select Active Crew Workboard:",
            options=team_filter_names,
            index=0,
            horizontal=True,
            key="radio_team_workboard_filter"
        )

        if selected_crew_filter == "All Crews Overview":
            overview_rows = []
            for t in field_teams:
                overview_rows.append({
                    "Crew Team": t["team_name"],
                    "Lead PIC": t["lead_name"],
                    "Specialization": t.get("specialization", "Field Ops"),
                    "Crew Size": f"{t['crew_size']} Specialists",
                    "Assigned Sites": f"{len(t.get('assigned_sites', []))} Sites",
                    "Status": t["status"]
                })
            df_overview = pd.DataFrame(overview_rows)
            st.table(df_overview)
            st.caption("Select any individual crew tab above (e.g. Team Alpha, Team Beta) to inspect site cards, update progress, or report blockers.")
            filtered_teams = []
        else:
            filtered_teams = [
                t for t in field_teams if t.get("_filter_label") == selected_crew_filter
            ]

    for team in filtered_teams:
        assigned_sites = team.get("assigned_sites", [])
        
        st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid #0284C7; border-radius: 6px; padding: 10px 14px; margin-top: 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 800; font-size: 0.90rem; color: #0F172A;">{team['team_name']}</span>
                    <span style="color: #64748B; font-size: 0.77rem; margin-left: 8px;">
                        PIC: <b style="color: #1E293B;">{team['lead_name']}</b> &bull; Crew: <b>{team['crew_size']} Specialists</b> &bull; Specialization: <b style="color: #0284C7;">{team.get('specialization', 'Field Ops')}</b>
                    </span>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="font-size: 0.72rem; font-weight: 700; color: #475569; background: #F1F5F9; border: 1px solid #E2E8F0; padding: 3px 8px; border-radius: 4px;">{team['status']}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; color: #0369A1; background: #E0F2FE; border: 1px solid #BAE6FD; padding: 3px 8px; border-radius: 4px;">{len(assigned_sites)} Assigned Sites</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if not assigned_sites:
            st.info(f"No sites currently assigned to {team['team_name']}. Use Step 1 above to assign sites to this team.")
            continue

        # Filter Bar: Site Counter & Instant Search
        h_col1, h_col2 = st.columns([2.5, 1.5])
        with h_col1:
            st.markdown(
                f"<span style='font-weight: 700; font-size: 0.84rem; color: #1E293B;'>Scrollable Operational Table ({len(assigned_sites)} Assigned Sites)</span>",
                unsafe_allow_html=True
            )
        with h_col2:
            site_query = st.text_input(
                "Filter Site:",
                placeholder="Search Site ID / Name / District...",
                label_visibility="collapsed",
                key=f"filter_site_{team['team_code']}"
            ).strip().lower()

        # Filter assigned sites if query provided
        display_sites = [
            s for s in assigned_sites
            if not site_query or site_query in s["site_id"].lower() or site_query in s["site_name"].lower() or site_query in s["district"].lower()
        ]

        if not display_sites:
            st.info(f"No sites match search query '{site_query}'.")
            continue

        # Column Header Row (Fixed above scrollable container)
        hdr_cols = st.columns([1.9, 1.1, 1.3, 1.9, 1.1, 0.7], gap="small")
        hdr_cols[0].markdown("<span style='font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;'>SITE & ACTION SCOPE</span>", unsafe_allow_html=True)
        hdr_cols[1].markdown("<span style='font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;'>DISTRICT & ROUTE</span>", unsafe_allow_html=True)
        hdr_cols[2].markdown("<span style='font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;'>CURRENT STATUS</span>", unsafe_allow_html=True)
        hdr_cols[3].markdown("<span style='font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;'>UPDATE PAAS STAGE</span>", unsafe_allow_html=True)
        hdr_cols[4].markdown("<span style='font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;'>BLOCKER DESK</span>", unsafe_allow_html=True)
        hdr_cols[5].markdown("<span style='font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;'>DISPATCH</span>", unsafe_allow_html=True)

        # Scrollable Container for All Assigned Sites
        with st.container(height=360, border=True):
            for s_idx, site in enumerate(display_sites):
                sid = site["site_id"]
                sname = site["site_name"]
                dist = site["district"]
                status_raw = site["paas_status"]
                status_cleaned = clean_status(status_raw)
                gate_cleaned = clean_status(site.get("readiness_gate", ""))
                km = site.get("accessible_route_km", 15.0)
                eta = site.get("est_travel_time", "1h 30m")
                rect = site.get("rectifier", "HARIF / Eltek")
                act_plan = site.get("action_plan", "Power I&C and rectifier mounting")
                is_blocked = "Blocked" in status_raw or "ESCALATE" in site.get("readiness_gate", "") or bool(site.get("blocker_reason"))

                row_cols = st.columns([1.9, 1.1, 1.3, 1.9, 1.1, 0.7], gap="small")

                # Col 0: Site & Action Scope
                with row_cols[0]:
                    st.markdown(f"""
                        <div style="font-weight: 800; font-size: 0.83rem; color: {'#DC2626' if is_blocked else '#0F172A'}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="[{sid}] {sname}">
                            [{sid}] {sname}
                        </div>
                        <div style="font-size: 0.71rem; color: #64748B; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{act_plan}">
                            {act_plan}
                        </div>
                    """, unsafe_allow_html=True)

                # Col 1: District & Route (Live Road Distance to Assigned Site)
                c_lat = team.get("current_lat")
                c_lon = team.get("current_lon")
                s_lat = site.get("lat")
                s_lon = site.get("lon")

                route_sub_text = f"{km:.1f} km &bull; {eta}"
                route_tooltip = f"Standard route from Regional Hub: {km:.1f} km"
                if c_lat is not None and c_lon is not None and s_lat is not None and s_lon is not None:
                    try:
                        routing = FleetTrackingService.calculate_road_routing(c_lat, c_lon, s_lat, s_lon)
                        if routing and routing.get("road_km") is not None:
                            route_sub_text = f"{routing['road_km']:.1f} km &bull; ETA {routing['eta_text']}"
                            route_tooltip = f"Live road route from crew location to Site {sid} ({s_lat:.4f}, {s_lon:.4f}): {routing['road_km']:.1f} km via fastest accessible road ({routing['eta_text']})"
                    except Exception:
                        pass

                with row_cols[1]:
                    st.markdown(f"""
                        <div style="font-size: 0.77rem; font-weight: 600; color: #334155;">
                            {dist}
                        </div>
                        <div style="font-size: 0.69rem; color: #0284C7; font-weight: 600;" title="{route_tooltip}">
                            {route_sub_text}
                        </div>
                    """, unsafe_allow_html=True)

                # Col 2: Current Status & Gate
                with row_cols[2]:
                    stat_col = "#DC2626" if is_blocked else "#0284C7"
                    stat_bg = "#FEF2F2" if is_blocked else "#F0F9FF"
                    stat_bd = "#FECACA" if is_blocked else "#BAE6FD"
                    gate_col = "#991B1B" if is_blocked else "#9A3412"
                    gate_bg = "#FEE2E2" if is_blocked else "#FFEDD5"
                    st.markdown(f"""
                        <div style="display: flex; flex-direction: column; gap: 2px;">
                            <span style="font-size: 0.71rem; font-weight: 700; color: {stat_col}; background: {stat_bg}; border: 1px solid {stat_bd}; padding: 1px 6px; border-radius: 4px; display: inline-block; width: fit-content;">
                                {status_cleaned}
                            </span>
                            <span style="font-size: 0.67rem; font-weight: 600; color: {gate_col}; background: {gate_bg}; padding: 1px 5px; border-radius: 3px; display: inline-block; width: fit-content;">
                                Gate: {gate_cleaned}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)

                # Col 3: Update PaaS Stage (Selectbox + Button inline)
                with row_cols[3]:
                    st_opts = [
                        "Power I&C Active",
                        "Testing & QA",
                        "Handover Telkomcel"
                    ]
                    cur_match_idx = 0
                    for idx_opt, opt in enumerate(st_opts):
                        if clean_status(opt).lower() in status_cleaned.lower() or status_cleaned.lower() in clean_status(opt).lower():
                            cur_match_idx = idx_opt
                            break

                    u_sel, u_btn = st.columns([1.5, 1.0], gap="small")
                    with u_sel:
                        new_selected_status = st.selectbox(
                            "Update Status",
                            options=st_opts,
                            index=cur_match_idx,
                            format_func=lambda s: clean_status(s),
                            label_visibility="collapsed",
                            key=f"t_sel_{team['team_code']}_{sid}"
                        )
                    with u_btn:
                        if st.button("Update", key=f"t_btn_{team['team_code']}_{sid}", use_container_width=True, type="primary"):
                            ok = RolloutOperationsService.update_site_lifecycle_status(sid, new_selected_status, user=team['lead_name'])
                            if ok:
                                st.toast(f"Updated {sid} to {clean_status(new_selected_status)}!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update {sid}.")

                # Col 4: Blocker Popover (Escalate / Drop Desk)
                with row_cols[4]:
                    blk_btn_label = "Blocker Active" if is_blocked else "Flag Blocker"
                    with st.popover(blk_btn_label, use_container_width=True):
                        st.markdown(f"<span style='font-size: 0.82rem; font-weight: 800; color: #0F172A;'>Blocker Desk: [{sid}]</span>", unsafe_allow_html=True)
                        if is_blocked and site.get("blocker_reason"):
                            st.caption(f"Current blocker: {site.get('blocker_reason')}")
                        blk_cat_options = [
                            "Civil & Tower Dependency (Plinth / Foundation Not Ready)",
                            "Landlord & Community Permit",
                            "EDTL Grid / Power Interconnection",
                            "Extreme Terrain & Weather Access",
                            "Hardware Equipment Defect",
                            "Other Technical Blocker"
                        ]
                        sel_cat = st.selectbox(
                            "Root-Cause Category:",
                            options=blk_cat_options,
                            key=f"t_cat_{team['team_code']}_{sid}"
                        )
                        blk_note = st.text_input(
                            "Detail / Mitigation Note:",
                            placeholder="e.g. Plinth not poured...",
                            key=f"t_note_{team['team_code']}_{sid}"
                        )
                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            if st.button("Escalate", help="Flag to PMO Command Center", key=f"t_esc_{team['team_code']}_{sid}", use_container_width=True):
                                note_text = blk_note.strip() or f"Field blocker reported under {sel_cat}"
                                ok = RolloutOperationsService.escalate_site(sid, sel_cat, note_text, user=team['lead_name'])
                                if ok:
                                    st.toast(f"Site {sid} escalated to PMO Command Center!")
                                    st.rerun()
                                else:
                                    st.error("Failed to escalate.")
                        with b_col2:
                            if st.button("Drop Site", help="Drop site from crew queue", key=f"t_drp_{team['team_code']}_{sid}", use_container_width=True):
                                note_text = blk_note.strip() or f"Dropped due to {sel_cat}"
                                ok = RolloutOperationsService.drop_site(sid, sel_cat, note_text, user=team['lead_name'])
                                if ok:
                                    st.toast(f"Site {sid} dropped and moved to parked pool!")
                                    st.rerun()
                                else:
                                    st.error("Failed to drop.")

                # Col 5: WhatsApp Work Order Dispatch Popover
                with row_cols[5]:
                    wo_data = NotificationDispatcher().generate_work_order_payload(site, team)
                    wa_url = wo_data.get("wa_link", "#")
                    with st.popover("WhatsApp", use_container_width=True):
                        st.markdown(f"**Work Order Dispatch [{sid}]**")
                        st.caption(f"PIC: {team.get('lead_name')} ({team.get('contact_number') or team.get('lead_phone')})")
                        st.link_button("Dispatch via WhatsApp", wa_url, use_container_width=True, type="primary")
                        with st.expander("Message Payload Format", expanded=False):
                            st.code(wo_data.get("message_text", ""), language="markdown")

                if s_idx < len(display_sites) - 1:
                    st.markdown("<hr style='margin: 4px 0 6px 0; border: none; border-bottom: 1px solid #F1F5F9;'/>", unsafe_allow_html=True)

        st.caption("*Interactive Operational Table: Each site row includes inline status progression, team assignment, and Blocker controls for instantaneous escalation or drop.*")
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # STEP 4: GOVERNANCE DESK — ESCALATED & DROPPED SITES MONITOR
    # =========================================================================
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    c_esc = len(escalated_df) if not escalated_df.empty else 0
    c_drp = len(dropped_df) if not dropped_df.empty else 0

    st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-top: 3px solid #DC2626; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.95rem; color: #0F172A; letter-spacing: 0.3px;">
                    3. GOVERNANCE DESK: ESCALATED & DROPPED SITES MONITOR
                </span>
                <span style="font-size: 0.74rem; font-weight: 700; color: {'#DC2626' if (c_esc + c_drp) > 0 else '#059669'}; background: {'#FEF2F2' if (c_esc + c_drp) > 0 else '#ECFDF5'}; border: 1px solid {'#FECACA' if (c_esc + c_drp) > 0 else '#A7F3D0'}; padding: 3px 8px; border-radius: 4px;">
                    {c_esc} Escalated &bull; {c_drp} Dropped Sites
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #64748B;">
                Central command oversight to review field escalations requiring PMO resolution, or re-activate dropped sites once external constraints are cleared.
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab_esc, tab_drp = st.tabs([f"Active Escalations ({c_esc})", f"Dropped / Parked Sites ({c_drp})"])

    with tab_esc:
        if not escalated_df.empty:
            df_esc_display = escalated_df[[
                "site_id", "site_name", "district", "operator", "assigned_team", "blocker_reason", "last_updated_by", "updated_at"
            ]].rename(columns={
                "site_id": "Site ID",
                "site_name": "Site Name",
                "district": "District",
                "operator": "Operator",
                "assigned_team": "Assigned Crew",
                "blocker_reason": "Blocker Diagnostics",
                "last_updated_by": "Reported By",
                "updated_at": "Timestamp"
            })
            st.dataframe(df_esc_display, use_container_width=True, hide_index=True)

            # Quick Blocker Resolution Box
            st.markdown("##### Resolve Blocker & Resume Rollout")
            esc_res_c1, esc_res_c2, esc_res_c3 = st.columns([3, 2.5, 1.8])
            with esc_res_c1:
                esc_opts = [
                    (r["site_id"], f"[{r['site_id']}] {r['site_name']} ({r['district']})")
                    for _, r in escalated_df.iterrows()
                ]
                sel_esc_target = st.selectbox(
                    "Select Escalated Site to Resolve:",
                    options=esc_opts,
                    format_func=lambda x: x[1],
                    key="sel_esc_target_box"
                )
            with esc_res_c2:
                sel_resume_stage = st.selectbox(
                    "Resume Site To Stage:",
                    options=[
                        "Power I&C Active",
                        "Testing & QA",
                        "Handover Telkomcel"
                    ],
                    key="sel_esc_resume_stage"
                )
            with esc_res_c3:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("Resolve & Resume Work", type="primary", use_container_width=True, key="btn_resolve_esc_work"):
                    target_sid = sel_esc_target[0] if sel_esc_target else ""
                    if target_sid:
                        ok = RolloutOperationsService.update_site_lifecycle_status(target_sid, sel_resume_stage, user="PMO Resolution Desk")
                        if ok:
                            st.toast(f"Blocker resolved for {target_sid}! Site resumed to {clean_status(sel_resume_stage)}.")
                            st.rerun()
                        else:
                            st.error("Failed to resolve blocker.")
        else:
            st.success("No active escalations. All field crews are operating without high-risk blockers.")

    with tab_drp:
        if not dropped_df.empty:
            df_drp_display = dropped_df[[
                "site_id", "site_name", "district", "operator", "blocker_reason", "last_updated_by", "updated_at"
            ]].rename(columns={
                "site_id": "Site ID",
                "site_name": "Site Name",
                "district": "District",
                "operator": "Operator",
                "blocker_reason": "Reason for Drop",
                "last_updated_by": "Actioned By",
                "updated_at": "Timestamp"
            })
            st.dataframe(df_drp_display, use_container_width=True, hide_index=True)

            # Quick Re-activation Box
            st.markdown("##### Re-Activate Dropped Site")
            drp_c1, drp_c2, drp_c3 = st.columns([3, 2.5, 1.8])
            with drp_c1:
                drp_opts = [
                    (r["site_id"], f"[{r['site_id']}] {r['site_name']} ({r['district']})")
                    for _, r in dropped_df.iterrows()
                ]
                sel_drp_target = st.selectbox(
                    "Select Dropped Site to Re-Activate:",
                    options=drp_opts,
                    format_func=lambda x: x[1],
                    key="sel_drp_target_box"
                )
            with drp_c2:
                if team_options:
                    sel_reassign_team = st.selectbox(
                        "Re-Assign to Team Owner:",
                        options=[t[0] for t in team_options],
                        format_func=lambda code: team_dict[code],
                        key="sel_drp_reassign_team"
                    )
                else:
                    st.selectbox(
                        "Re-Assign to Team Owner:",
                        options=["NO_TEAM"],
                        format_func=lambda _: "No Active Teams (Register team first)",
                        disabled=True,
                        key="sel_drp_reassign_team_empty"
                    )
                    sel_reassign_team = ""
            with drp_c3:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("Re-Activate Site", type="primary", use_container_width=True, disabled=not bool(sel_reassign_team), key="btn_reactivate_drp_work"):
                    target_sid = sel_drp_target[0] if sel_drp_target else ""
                    if target_sid and sel_reassign_team:
                        ok = RolloutOperationsService.reactivate_site(target_sid, sel_reassign_team, user="PMO Re-activation Desk")
                        if ok:
                            st.toast(f"Site {target_sid} re-activated and assigned to {team_dict[sel_reassign_team].split('—')[0].strip()}!")
                            st.rerun()
                        else:
                            st.error("Failed to re-activate site.")
        else:
            st.info("No sites currently dropped. 100% of sites are active in the portfolio queue.")

    # =========================================================================
    # SUPPORTING REFERENCE: MILESTONES & WORKFLOW PIPELINE (EXPANDER)
    # =========================================================================
    with st.expander("Milestone Check Points & Micro-Progress Workflow (Reference)", expanded=False):
        chk_col1, chk_col2 = st.columns(2)
        with chk_col1:
            st.markdown("##### Weekly Power I&C Commissioning Milestone Targets")
            if weekly_comm:
                df_comm = pd.DataFrame(weekly_comm).rename(columns={
                    "site_id": "Site ID",
                    "site_name": "Site Name",
                    "district": "District",
                    "milestone_checkpoint": "Milestone Checkpoint",
                    "target_week": "Target SLA",
                    "status": "Readiness Status"
                })
                st.table(df_comm)
            else:
                st.info("No commissioning milestones scheduled for this week.")
                
        with chk_col2:
            st.markdown("##### Weekly Acceptance Testing (ATP Sign-off) Milestone Targets")
            if weekly_atp:
                df_atp = pd.DataFrame(weekly_atp).rename(columns={
                    "site_id": "Site ID",
                    "site_name": "Site Name",
                    "district": "District",
                    "milestone_checkpoint": "Milestone Checkpoint",
                    "target_week": "Target SLA",
                    "status": "Readiness Status"
                })
                st.table(df_atp)
            else:
                st.info("No ATP sign-off milestones scheduled for this week.")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 5-Stage Micro-Progress Workflow Pipeline")
        pipe_cols = st.columns(5)
        pipe_steps = [
            ("1. Survey & TSSR", micro_pipeline.get("stage_1_survey", total_sites), total_sites, "#0284C7", "100% Baseline Validated"),
            ("2. Material Staged & Dispatched", micro_pipeline.get("stage_2_staged", 0), total_sites, "#3B82F6", "Direct MOA Dispatch Ready"),
            ("3. Power I&C Installation", micro_pipeline.get("stage_3_power", 0), total_sites, "#8B5CF6", "Eltek & LiFePO4 Mounted"),
            ("4. ATP & Remote QA", micro_pipeline.get("stage_4_testing", 0), total_sites, "#F59E0B", "Blackout Simulation & RMS"),
            ("5. Commercial Handover", micro_pipeline.get("stage_5_atp_live", 0), total_sites, "#10B981", "BAST & Commercial COD Live")
        ]
        for col, (step_title, count, tot, clr, note) in zip(pipe_cols, pipe_steps):
            with col:
                pct = round(count / tot * 100) if tot else 0
                st.markdown(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 4px solid {clr}; border-radius: 8px; padding: 12px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">
                        <div style="font-size: 0.75rem; font-weight: 700; color: #475569;">{step_title}</div>
                        <div style="font-size: 1.45rem; font-weight: 800; color: {clr}; margin: 4px 0;">{count} <span style="font-size: 0.8rem; color: #94A3B8;">/ {tot}</span></div>
                        <div style="font-size: 0.72rem; color: #64748B; font-weight: 600;">{pct}% Completed</div>
                        <div style="font-size: 0.68rem; color: #94A3B8; margin-top: 4px;">{note}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # 7. Material on Area (MOA) to Material on Site (MOS) Flow Controller
    st.markdown("---")
    st.subheader("5. Material on Area (MOA) to Material on Site (MOS) Direct Flow Engine")
    st.caption("Pure Direct Logistics Engine: Material at Inbound Port Area (MOA) flows directly to Tower Site Coordinates (MOS) upon Tower Plinth Certification (Gate GO). Eliminating 100% of forward hubs and intermediate warehouse OPEX.")

    moa_summary = RolloutOperationsService.get_moa_mos_flow_summary(selected_operator)
    df_moa_flow = moa_summary.get("flow_df", pd.DataFrame())

    # 4 Flow State Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #0284C7; padding: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #0284C7;">1. MATERIAL ON AREA (MOA)</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A; margin: 3px 0;">{moa_summary.get('moa_port_count', 0)} Sites Staged</div>
                <div style="font-size: 0.76rem; color: #64748B;">
                    • Inbound Port Terminal Area Staging<br/>
                    • Awaiting TowerCo Plinth Readiness<br/>
                    • $0 Regional Warehouse Rent
                </div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #10B981; padding: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #059669;">2. READY FOR DIRECT DISPATCH</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A; margin: 3px 0;">{moa_summary.get('ready_dispatch_count', 0)} Sites Certified</div>
                <div style="font-size: 0.76rem; color: #64748B;">
                    • Tower Plinth Passed & Certified<br/>
                    • Gate 'GO' Dispatch Authorized<br/>
                    • Direct Truck Route Queued
                </div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #F59E0B; padding: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #D97706;">3. IN-TRANSIT (PORT -> SITE)</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A; margin: 3px 0;">Direct Transit Active</div>
                <div style="font-size: 0.76rem; color: #64748B;">
                    • Rolling Directly to Tower Coordinates<br/>
                    • Zero Intermediate Yard Transfers<br/>
                    • Single Handling Touchpoint
                </div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
            <div class="op-radar-card" style="border-top: 3px solid #8B5CF6; padding: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #7C3AED;">4. MATERIAL ON SITE (MOS)</div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A; margin: 3px 0;">{moa_summary.get('mos_confirmed_count', 0)} Sites Confirmed</div>
                <div style="font-size: 0.76rem; color: #64748B;">
                    • Physical BAST MOS Sign-off<br/>
                    • Rectifiers & Batteries at Site<br/>
                    • Unlocks Power I&C Installation
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Direct Dispatch Simulator / Action Center
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("##### Direct Dispatch Action Center: Trigger MOA (Port) -> MOS (Site)")
    
    # Filter sites ready for direct dispatch
    ready_sites = df_moa_flow[df_moa_flow["moa_badge"] == "READY_DISPATCH"] if not df_moa_flow.empty else pd.DataFrame()
    if not ready_sites.empty:
        with st.container():
            st.markdown(
                """
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px;">
                    <b style="color: #166534;">Direct Dispatch Engine Unlocked:</b> 
                    Tower foundations/plinths for the following sites have been certified by TowerCo. Power materials can now be dispatched directly from the Port of Entry straight to the tower site coordinates.
                </div>
                """,
                unsafe_allow_html=True
            )
            dc1, dc2 = st.columns([3, 1])
            with dc1:
                dispatch_options = [
                    f"{r['site_id']} — {r['site_name']} ({r['district']}) | Route: {r['route_km']:.1f} km ({r['travel_time']}) from {r['port_origin']}"
                    for _, r in ready_sites.iterrows()
                ]
                sel_dispatch_site = st.selectbox("Select Certified Site for Direct Delivery:", dispatch_options, key="sel_dispatch_moa_mos")
            with dc2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("Authorize Direct Dispatch", type="primary", use_container_width=True, key="btn_dispatch_moa_mos"):
                    target_sid = sel_dispatch_site.split()[0]
                    success = RolloutOperationsService.dispatch_moa_to_mos(target_sid)
                    if success:
                        st.toast(f"Direct dispatch authorized for {target_sid}! Material en-route from Port directly to tower site.")
                        st.rerun()
                    else:
                        st.error("Failed to authorize dispatch.")
    else:
        st.info("All currently staged materials are either already delivered on-site (MOS Confirmed) or awaiting TowerCo plinth certification before direct dispatch.")

    # Live MOA -> MOS Tracking Table (Collapsible to preserve memory)
    with st.expander("Live Portfolio MOA -> MOS Tracking Matrix (180 Sites)", expanded=False):
        if not df_moa_flow.empty:
            st.dataframe(
                df_moa_flow.rename(columns={
                    "site_id": "Site ID",
                    "site_name": "Site Name",
                    "district": "District",
                    "port_origin": "Port of Entry (MOA)",
                    "route_km": "Direct Distance (km)",
                    "travel_time": "Direct Transit ETA",
                    "paas_status": "PaaS Rollout Status",
                    "readiness_gate": "Readiness Gate",
                    "moa_stage": "MOA -> MOS Stage",
                    "dispatch_gate": "Dispatch Protocol"
                })[[
                    "Site ID", "Site Name", "District", "Port of Entry (MOA)",
                    "Direct Distance (km)", "Direct Transit ETA", "MOA -> MOS Stage", "Dispatch Protocol"
                ]],
                use_container_width=True,
                hide_index=True
            )

    # 6. Extreme Access Sites Flagged for Contingency Staging (Collapsible)
    st.markdown("---")
    with st.expander("High-Elevation & Extreme Terrain Access Sites (Contingency Staging)", expanded=False):
        st.caption(
            "Sites designated with extreme terrain classification due to mountain elevation, road gradient, or seasonal weather risk. "
            "Deployment governance requires dedicated 4x4 heavy transport fleet and pre-allocated contingency hardware prior to dispatch."
        )

        df_ext = query_df("SELECT site_id, site_name, district, accessible_route_km, est_travel_time, transport_mode, priority_tier, notes FROM timor_sites_100 WHERE is_extreme = 1")
        if not df_ext.empty:
            df_ext_display = df_ext.rename(columns={
                "site_id": "Site ID",
                "site_name": "Site Name",
                "district": "District",
                "accessible_route_km": "Route Distance (km)",
                "est_travel_time": "Transit Duration",
                "transport_mode": "Transport Fleet",
                "priority_tier": "Priority Tier",
                "notes": "Contingency Protocol"
            })
            st.dataframe(df_ext_display, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_ext, use_container_width=True, hide_index=True)


def render_data_cleaning_panel():
    """Renders icon-free enterprise data cleaning, status reset, blocker purge, and database wipe controls."""
    summary = DataManagementService.get_database_summary()
    
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
            <div style="font-weight: 700; font-size: 0.95rem; color: #0F172A; margin-bottom: 12px;">
                Current Database Health & Metrics
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px;">
                    <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Total Operational Sites</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #0F172A; margin-top: 4px;">{summary.get("total_sites", 0)}</div>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px;">
                    <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Blocked / Hold Sites</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #DC2626; margin-top: 4px;">{summary.get("blocked_sites", 0)}</div>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px;">
                    <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Assigned to Field Teams</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #0284C7; margin-top: 4px;">{summary.get("assigned_sites", 0)}</div>
                </div>
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 12px;">
                    <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Audit Trail Entries</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #16A34A; margin-top: 4px;">{summary.get("audit_logs", 0)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="font-weight: 700; font-size: 0.92rem; color: #1E293B; margin-bottom: 4px;">
            1. Operational Status Cleaning & Blocker Purge
        </div>
        <div style="font-size: 0.80rem; color: #64748B; margin-bottom: 12px;">
            Reset site operational stages or clear blocker dependencies across selected operator scopes without deleting data.
        </div>
        """,
        unsafe_allow_html=True
    )

    col_act1, col_act2, col_act3 = st.columns(3)

    with col_act1:
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; min-height: 250px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0F172A;">Reset Site Statuses</div>
                    <div style="font-size: 0.76rem; color: #64748B; margin-top: 4px;">
                        Batch set sites to a unified PaaS stage and reset gates to GO.
                    </div>
                </div>
            """,
            unsafe_allow_html=True
        )
        sel_op_reset = st.selectbox(
            "Operator Scope:",
            ["All", "Telkomcel", "XLSmart", "Mitratel", "IOH"],
            key="sel_op_clean_status"
        )
        sel_target_st = st.selectbox(
            "New Status:",
            [
                "Shipping & Customs",
                "Staged / Dili Hub",
                "Power I&C Active",
                "Testing & QA",
                "Handover Telkomcel",
                "Blocked / Issue"
            ],
            key="sel_target_st_clean"
        )
        with st.popover("Reset Statuses", use_container_width=True):
            st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #0F172A;'>Confirm Status Reset</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.78rem; color: #475569; margin: 6px 0 12px 0;'>All {sel_op_reset} sites will be updated to: <b>{sel_target_st}</b>.</div>", unsafe_allow_html=True)
            if st.button("Confirm Reset", type="primary", use_container_width=True, key="btn_exec_status_reset"):
                ok, msg, aff = DataManagementService.reset_all_site_statuses(sel_target_st, operator=sel_op_reset)
                if ok:
                    st.toast(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_act2:
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; min-height: 250px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0F172A;">Clear Blockers & Holds</div>
                    <div style="font-size: 0.76rem; color: #64748B; margin-top: 4px;">
                        Remove civil hold notes and revert readiness decision gates back to GO.
                    </div>
                </div>
            """,
            unsafe_allow_html=True
        )
        sel_op_blocker = st.selectbox(
            "Operator Scope:",
            ["All", "Telkomcel", "XLSmart", "Mitratel", "IOH"],
            key="sel_op_clean_blocker"
        )
        st.markdown("<div style='height: 52px;'></div>", unsafe_allow_html=True)
        with st.popover("Clear Blockers", use_container_width=True):
            st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #0F172A;'>Confirm Blocker Purge</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.78rem; color: #475569; margin: 6px 0 12px 0;'>Blocker reasons and hold gates for {sel_op_blocker} will be cleared.</div>", unsafe_allow_html=True)
            if st.button("Confirm Clear", type="primary", use_container_width=True, key="btn_exec_blocker_clear"):
                ok, msg, aff = DataManagementService.clear_all_blockers(operator=sel_op_blocker)
                if ok:
                    st.toast(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_act3:
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; min-height: 250px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; font-size: 0.88rem; color: #0F172A;">Unassign Field Teams</div>
                    <div style="font-size: 0.76rem; color: #64748B; margin-top: 4px;">
                        Empties team dispatch queues back to unassigned without deleting registered crews.
                    </div>
                </div>
            """,
            unsafe_allow_html=True
        )
        sel_op_unassign = st.selectbox(
            "Operator Scope:",
            ["All", "Telkomcel", "XLSmart", "Mitratel", "IOH"],
            key="sel_op_clean_unassign"
        )
        st.markdown("<div style='height: 52px;'></div>", unsafe_allow_html=True)
        with st.popover("Unassign Teams", use_container_width=True):
            st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #0F172A;'>Confirm Team Unassign</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.78rem; color: #475569; margin: 6px 0 12px 0;'>All {sel_op_unassign} sites will be returned to Unassigned queue.</div>", unsafe_allow_html=True)
            if st.button("Confirm Unassign", type="primary", use_container_width=True, key="btn_exec_unassign"):
                ok, msg, aff = DataManagementService.unassign_all_sites(operator=sel_op_unassign)
                if ok:
                    st.toast(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-weight: 700; font-size: 0.92rem; color: #1E293B; margin-bottom: 4px;">
            2. Database Wipe & Factory Baseline Restoration
        </div>
        <div style="font-size: 0.80rem; color: #64748B; margin-bottom: 12px;">
            Erase site records to upload custom datasets, or revert database back to production seed.
        </div>
        """,
        unsafe_allow_html=True
    )

    col_db1, col_db2 = st.columns(2)
    with col_db1:
        st.markdown(
            """
            <div style="background: #FEF2F2; border: 1px solid #FECACA; border-left: 4px solid #DC2626; border-radius: 8px; padding: 14px;">
                <div style="font-weight: 700; font-size: 0.88rem; color: #991B1B;">Wipe Sites from Database</div>
                <div style="font-size: 0.77rem; color: #7F1D1D; margin: 4px 0 10px 0;">
                    Permanently deletes site records from the database so you can start from an empty state and import your own site files.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        c_w1, c_w2 = st.columns([2, 2])
        with c_w1:
            sel_wipe_scope = st.selectbox(
                "Delete Scope:",
                ["All", "Telkomcel", "XLSmart", "Mitratel", "IOH"],
                key="sel_wipe_scope_box"
            )
        with c_w2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            with st.popover("Wipe Sites Now", use_container_width=True):
                st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #DC2626;'>Confirm Permanent Deletion</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 0.78rem; color: #475569; margin: 6px 0 12px 0;'>Are you sure you want to wipe site records for: <b>{sel_wipe_scope}</b>?</div>", unsafe_allow_html=True)
                if st.button("Yes, Wipe Sites", type="primary", use_container_width=True, key="btn_exec_wipe"):
                    ok, msg, aff = DataManagementService.wipe_all_sites(operator=sel_wipe_scope)
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with col_db2:
        st.markdown(
            """
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; border-radius: 8px; padding: 14px;">
                <div style="font-weight: 700; font-size: 0.88rem; color: #166534;">Restore Factory Baseline</div>
                <div style="font-size: 0.77rem; color: #14532D; margin: 4px 0 10px 0;">
                    Re-seeds the entire 180-site dataset (100 Timor-Leste + 80 multi-tenant regional sites) and default field crews.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        with st.popover("Restore Factory Baseline", use_container_width=True):
            st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #0F172A;'>Confirm Baseline Reset</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 0.78rem; color: #475569; margin: 6px 0 12px 0;'>This will replace current site data with the original 180-site factory baseline.</div>", unsafe_allow_html=True)
            if st.button("Confirm and Restore", type="primary", use_container_width=True, key="btn_exec_restore"):
                ok, msg, aff = DataManagementService.restore_factory_baseline()
                if ok:
                    st.toast(msg)
                    st.rerun()
                else:
                    st.error(msg)


def render_update_tab():
    render_unified_module_header(
        module_label="UPDATE & SYNC",
        breadcrumb_trail="Overview &nbsp;&rsaquo;&nbsp; Field Gates & Data Sync &nbsp;&rsaquo;&nbsp; <b>Quick Actions & Two-Way Master Excel Sync</b>",
        badge_text="Live 2-Way Sync Active",
        badge_bg="#ECFDF5",
        badge_color="#065F46",
        badge_border="#A7F3D0"
    )

    tab_gsheet, tab_sync, tab_action, tab_clean = st.tabs([
        "Live Google Sheets Cloud Sync", 
        "Master File Sync (Excel & CSV)", 
        "1-Click Field Dispatch Toggles",
        "Data Cleaning & Database Tools"
    ])

    with tab_gsheet:
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; padding: 18px; border-radius: 10px; margin-bottom: 16px;">
                <h4 style="margin: 0; color: #0284C7;">Live Google Sheets Cloud Sync (Ideal for Field PICs)</h4>
                <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 0 0;">
                    Field PICs across all regional operations can edit rows directly in Google Sheets from any smartphone or laptop. 
                    Paste your Google Sheets link below to pull updates directly into the NOC Command Center in real-time.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        gsheet_url_input = st.text_input(
            "Google Sheets Share Link:",
            placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit?usp=sharing",
            help="Ensure the Google Sheet link sharing is set to 'Anyone with the link can view'."
        )

        col_gs1, col_gs2 = st.columns([2, 3])
        with col_gs1:
            if st.button("Sync Live from Google Sheets Now", type="primary", use_container_width=True):
                if gsheet_url_input:
                    with st.spinner("Fetching and synchronizing live data from Google Sheets..."):
                        success, msg, stats = ExcelSyncService.sync_from_google_sheets(gsheet_url_input)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.warning("Please enter a valid Google Sheets URL first.")

        with col_gs2:
            st.caption("**Tip for Low-Tech Field PICs**: Lock columns A–H (Site ID, Coordinates, Rectifier) and let PICs only edit column **Readiness Gate (GO / HOLD / ESCALATE)** and **Notes**.")

    with tab_sync:
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; padding: 16px; border-radius: 10px;">
                    <h4 style="margin: 0; color: #1E3A8A;">1. Download Complete Master Tracker (.xlsx)</h4>
                    <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 12px 0;">
                        Contains 5 pre-formatted sheets: Customs, SG&A Expenses, Site Uptime, POC Milestones, and the 
                        <b>Master Multi-Tenant Sites with Accessible Route Distances from Origin Hubs</b>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            excel_path = ExcelSyncService.generate_master_template()
            with open(excel_path, "rb") as f_excel:
                st.download_button(
                    "Download Samvad_Master_Tracker.xlsx",
                    data=f_excel.read(),
                    file_name="Samvad_Master_Tracker_100Sites.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            
            fuel_excel_path = os.path.join("reports", "Timor_Leste_100_Sites_Zone_Distance_Fuel_Analysis.xlsx")
            if os.path.exists(fuel_excel_path):
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                with open(fuel_excel_path, "rb") as f_fuel:
                    st.download_button(
                        "Download 100 Sites Zone Distance & Fuel Analysis (.xlsx)",
                        data=f_fuel.read(),
                        file_name="Timor_Leste_100_Sites_Zone_Distance_Fuel_Analysis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_download_fuel_analysis"
                    )

            opex_excel_path = os.path.join("reports", "Timor_Leste_100_Sites_OPEX_Model.xlsx")
            if os.path.exists(opex_excel_path):
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                with open(opex_excel_path, "rb") as f_opex:
                    st.download_button(
                        "Download 100 Sites Rollout OPEX Model (.xlsx)",
                        data=f_opex.read(),
                        file_name="Timor_Leste_100_Sites_OPEX_Model.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_download_opex_model"
                    )

        with sc2:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; padding: 16px; border-radius: 10px;">
                    <h4 style="margin: 0; color: #0F766E;">2. Upload Updated Spreadsheet (.xlsx or .csv)</h4>
                    <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 12px 0;">
                        Edit rows offline in Microsoft Excel or Google Sheets, then drop the file here to auto-update the database and recalculate KPI scores.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            up_file = st.file_uploader("Drop updated .xlsx or .csv file here", type=["xlsx", "csv"], key="noc_uploader")
            if up_file:
                c_u1, c_u2 = st.columns([2, 1])
                with c_u1:
                    sync_replace = st.checkbox("Wipe and replace all sites with uploaded file (Clean Import)", value=False, key="chk_sync_replace")
                with c_u2:
                    btn_label = "Replace All Sites Now" if sync_replace else "Update Database"
                    if st.button(btn_label, type="primary", use_container_width=True, key="btn_exec_sync_up"):
                        with st.spinner("Processing spreadsheet..."):
                            if up_file.name.lower().endswith(".csv") or sync_replace:
                                success, msg, stats = DataManagementService.clean_import_from_file(up_file, replace_mode=sync_replace)
                            else:
                                success, msg, stats = ExcelSyncService.sync_from_uploaded_excel(up_file)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    with tab_clean:
        render_data_cleaning_panel()

    with tab_action:
        st.subheader("Quick Field Action & PaaS Status Toggles")
        df_sites = query_df("SELECT site_id, site_name, readiness_gate, paas_status, district FROM timor_sites_100 LIMIT 100")
        opts = [f"{r['site_id']} - {r['site_name']} ({r['district']}) [{r['paas_status']}] [Gate: {r['readiness_gate']}]" for _, r in df_sites.iterrows()]
        
        chosen = st.selectbox("Select Site to Update:", opts)
        chosen_id = chosen.split()[0]

        tc1, tc2 = st.columns(2)
        with tc1:
            new_status = st.selectbox(
                "Update PaaS Rollout Status:",
                [
                    "Shipping & Customs",
                    "⚪ Staged / Dili Hub",
                    "🟣 Power I&C Active",
                    "🟡 Testing & QA",
                    "🟢 Handover Telkomcel",
                    "🔴 Blocked / Issue"
                ],
                format_func=lambda s: clean_status(s)
            )
        with tc2:
            new_gate = st.selectbox(
                "Update Readiness Decision Gate:",
                ["GO (Dispatch Ready)", "HOLD (Civil Dependency)", "HOLD (Dependency)", "ESCALATE (High Risk)", "RESEQUENCE (Area Constraint)"]
            )

        if st.button("Apply PaaS Status & Gate Decision", type="primary"):
            execute_write(
                "UPDATE timor_sites_100 SET paas_status = ?, readiness_gate = ? WHERE site_id = ?",
                (new_status, new_gate, chosen_id)
            )
            st.success(f"Site {chosen_id} updated to {new_status} | Gate: {new_gate}")
            st.rerun()


def render_report_tab():
    render_unified_module_header(
        module_label="REPORTS",
        breadcrumb_trail="Overview &nbsp;&rsaquo;&nbsp; SLA Reporting Engine &nbsp;&rsaquo;&nbsp; <b>Friday 14:00 Auto-Run & I&C Handover SOPs (25%)</b>",
        badge_text="Friday 17:00 WIB SLA Deadline",
        badge_bg="#FDF2F8",
        badge_color="#9D174D",
        badge_border="#FBCFE8"
    )
    render_module4()


def render_settings_and_data_management():
    """Renders enterprise system settings, database management, cleaning, and clean file imports (strictly icon-free)."""
    render_unified_module_header(
        module_label="SETTINGS & DATA MANAGEMENT",
        breadcrumb_trail="Overview &nbsp;&rsaquo;&nbsp; System &nbsp;&rsaquo;&nbsp; <b>Settings, Data Cleaning & File Import</b>",
        badge_text="Data Console Active",
        badge_bg="#F1F5F9",
        badge_color="#334155",
        badge_border="#CBD5E1"
    )

    tab_clean, tab_import, tab_audit = st.tabs([
        "Data Cleaning & Reset Tools",
        "Clean File Import (Excel & CSV)",
        "System Audit Trail"
    ])

    with tab_clean:
        render_data_cleaning_panel()

    with tab_import:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="font-weight: 700; font-size: 0.95rem; color: #0F172A; margin-bottom: 4px;">
                    Clean File Import (Excel .xlsx and CSV .csv)
                </div>
                <div style="font-size: 0.80rem; color: #64748B;">
                    Upload custom spreadsheet files to update existing sites or completely replace database contents with new site records.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c_imp1, c_imp2 = st.columns([2.5, 1.5])
        with c_imp1:
            uploaded_file = st.file_uploader(
                "Select File to Import (.xlsx or .csv):",
                type=["xlsx", "csv"],
                key="uploader_data_mgmt_tab"
            )

            c_mode1, c_mode2 = st.columns(2)
            with c_mode1:
                import_mode = st.radio(
                    "Import Mode:",
                    [
                        "Update existing matching sites (Keep others)",
                        "Wipe and replace all sites with uploaded file"
                    ],
                    key="radio_import_mode_tab"
                )
                is_replace = (import_mode == "Wipe and replace all sites with uploaded file")

            with c_mode2:
                default_op = st.selectbox(
                    "Target Operator for Imported Sites:",
                    ["Telkomcel", "XLSmart", "Mitratel", "IOH", "All"],
                    key="sel_default_op_import_tab"
                )

            if uploaded_file is not None:
                if st.button("Execute File Import Now", type="primary", use_container_width=True, key="btn_execute_import_tab"):
                    with st.spinner("Processing file import..."):
                        ok, msg, stats = DataManagementService.clean_import_from_file(
                            uploaded_file,
                            replace_mode=is_replace,
                            default_operator=default_op
                        )
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        with c_imp2:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px;">
                    <div style="font-weight: 700; font-size: 0.85rem; color: #1E293B; margin-bottom: 6px;">Supported File Columns</div>
                    <div style="font-size: 0.77rem; color: #475569; line-height: 1.5;">
                        <b>Mandatory:</b><br/>
                        &bull; <code>site_id</code> (e.g. TLS001)<br/><br/>
                        <b>Optional (Smart defaults applied):</b><br/>
                        &bull; <code>site_name</code><br/>
                        &bull; <code>district</code><br/>
                        &bull; <code>lat</code>, <code>lon</code><br/>
                        &bull; <code>accessible_route_km</code><br/>
                        &bull; <code>paas_status</code><br/>
                        &bull; <code>readiness_gate</code><br/>
                        &bull; <code>rectifier</code>, <code>has_dg</code><br/>
                        &bull; <code>operator</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            excel_path = ExcelSyncService.generate_master_template()
            with open(excel_path, "rb") as f_excel:
                st.download_button(
                    "Download Master Template (.xlsx)",
                    data=f_excel.read(),
                    file_name="Samvad_Master_Tracker_Template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    with tab_audit:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #0F172A;">System Audit Trail & Operations Ledger</div>
                    <div style="font-size: 0.80rem; color: #64748B;">Complete historical ledger of data management operations, WhatsApp work orders, and sync events.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_audit_btn, _ = st.columns([2, 4])
        with col_audit_btn:
            with st.popover("Purge Audit Log History", use_container_width=True):
                st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #DC2626;'>Confirm Log Purge</div>", unsafe_allow_html=True)
                st.markdown("<div style='font-size: 0.78rem; color: #475569; margin: 6px 0 10px 0;'>Are you sure you want to delete audit history records?</div>", unsafe_allow_html=True)
                if st.button("Confirm Purge All Logs", type="primary", use_container_width=True, key="btn_confirm_purge_logs_tab"):
                    ok, msg, aff = DataManagementService.clear_audit_logs(keep_last_n=0)
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        df_logs = query_df("SELECT id, channel, recipient, message_type, payload, sent_status, sent_at FROM notification_audit_logs ORDER BY sent_at DESC LIMIT 100")
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.info("No audit logs currently recorded.")


def render_field_checkin_portal():
    """
    Dedicated Mobile Field Crew Task Confirmation & Live GPS Telemetry Check-In Page.
    Triggered when URL contains ?checkin=<team_code>&site=<site_id>.
    Captures live device GPS coordinates with user permission and updates the PMO Radar.
    Strictly icon-free enterprise typography.
    """
    import streamlit.components.v1 as components

    team_code = st.query_params.get("checkin", "TEAM-A").strip().upper()
    site_id = st.query_params.get("site", "DAX001").strip().upper()

    # Automatic capture handling when redirected from browser geolocation prompt
    url_gps_confirmed = st.query_params.get("gps_confirmed")
    url_lat = st.query_params.get("lat")
    url_lon = st.query_params.get("lon")
    url_acc = st.query_params.get("acc", "8.0")
    url_status = st.query_params.get("status", "Confirmed - En Route")

    df_team = query_df("SELECT * FROM paas_field_teams WHERE team_code = ?", (team_code,))
    if not df_team.empty:
        team = df_team.iloc[0].to_dict()
    else:
        team = {
            "team_code": team_code,
            "team_name": f"Field Crew {team_code}",
            "lead_name": "Field Lead PIC",
            "contact_number": "-",
            "crew_size": 4,
            "current_lat": None,
            "current_lon": None,
            "checkin_status": "Awaiting Confirmation"
        }

    cleaned_site_id = site_id.replace("-", "").upper()
    df_site = query_df("SELECT * FROM timor_sites_100 WHERE UPPER(site_id) = ? OR UPPER(REPLACE(site_id, '-', '')) = ? LIMIT 1", (site_id, cleaned_site_id))
    if df_site.empty:
        df_site = query_df("SELECT * FROM timor_sites_100 LIMIT 1")
    site = df_site.iloc[0].to_dict() if not df_site.empty else {
        "site_id": "DAX001",
        "site_name": "Fomento 1",
        "district": "Dili",
        "lat": -8.5621,
        "lon": 125.5382,
        "operator": "Telkomcel",
        "rectifier": "Eltek 48V/3000W Smart Hybrid",
        "accessible_route_km": 15.0,
        "est_travel_time": "1h 30m",
        "transport_mode": "4x4 Overland Truck"
    }

    # If incoming URL has GPS coordinates captured via browser permission, record them immediately
    if url_gps_confirmed == "1" and url_lat is not None and url_lon is not None:
        try:
            parsed_lat = float(url_lat)
            parsed_lon = float(url_lon)
            parsed_acc = float(url_acc)
            ok, msg = FleetTrackingService.record_team_checkin(
                team_code=team["team_code"],
                site_id=site["site_id"],
                lat=parsed_lat,
                lon=parsed_lon,
                status=url_status,
                accuracy_m=parsed_acc,
                user_agent="Mobile Browser GPS Link Permission",
                notes=f"Automated GPS telemetry captured via device permission (Accuracy: {parsed_acc:.1f}m)"
            )
            if ok:
                st.session_state["portal_checkin_success"] = True
                st.session_state["confirmed_portal_lat"] = parsed_lat
                st.session_state["confirmed_portal_lon"] = parsed_lon
                st.session_state["confirmed_portal_acc"] = parsed_acc
                st.session_state["confirmed_portal_status"] = url_status
        except Exception:
            pass

    st.markdown("""
        <style>
            html, body, .stApp, [data-testid="stAppViewContainer"] {
                background: #F8FAFC !important;
                background-image: none !important;
            }
            .main .block-container {
                max-width: 620px !important;
                margin: 0 auto !important;
                padding-top: 28px !important;
                padding-bottom: 40px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Header Card
    st.markdown(f"""
        <div style="background: #0F172A; border-radius: 8px; padding: 18px 20px; color: #FFFFFF; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(15,23,42,0.12);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 0.70rem; font-weight: 700; color: #38BDF8; letter-spacing: 1px; text-transform: uppercase;">
                    SAMVAD PMO-CC // FIELD DISPATCH
                </span>
                <span style="font-size: 0.68rem; background: #1E293B; color: #94A3B8; padding: 2px 8px; border-radius: 4px; border: 1px solid #334155;">
                    WO-PAAS-{site['site_id']}
                </span>
            </div>
            <div style="font-size: 1.15rem; font-weight: 800; letter-spacing: 0.2px;">
                Task Confirmation &amp; Live Telemetry
            </div>
            <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 4px;">
                Team PIC: <b>{team.get('lead_name')}</b> ({team.get('team_name')})
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Work Order Scope Summary Card
    st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px;">
            <div style="font-weight: 800; font-size: 0.88rem; color: #0F172A; margin-bottom: 8px; border-bottom: 1px solid #F1F5F9; padding-bottom: 6px;">
                ASSIGNED WORK ORDER DETAILS
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.78rem;">
                <div>
                    <span style="color: #64748B;">Target Site:</span><br>
                    <b style="color: #0F172A;">{site['site_id']} — {site['site_name']}</b>
                </div>
                <div>
                    <span style="color: #64748B;">District &amp; Operator:</span><br>
                    <b style="color: #0F172A;">{site.get('district')} ({site.get('operator')})</b>
                </div>
                <div>
                    <span style="color: #64748B;">Target Site GPS:</span><br>
                    <b style="color: #0F172A;">{site.get('lat', -8.5621):.5f}, {site.get('lon', 125.5382):.5f}</b>
                </div>
                <div>
                    <span style="color: #64748B;">Access &amp; ETA:</span><br>
                    <b style="color: #0F172A;">{site.get('transport_mode')} &bull; {site.get('est_travel_time')}</b>
                </div>
            </div>
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px dashed #E2E8F0; font-size: 0.75rem; color: #475569;">
                <b>Scope of Work:</b> Install DC power distribution, mount {site.get('rectifier')}, wire 48V LiFePO4 battery bank, calibrate telemetry sensors to PMO-NOC.
            </div>
        </div>
    """, unsafe_allow_html=True)

    base_host_url = FleetTrackingService.get_effective_host()

    # Interactive Option A: Direct Smartphone Live GPS Sensor
    st.markdown("""
        <div style="background: #FFFFFF; border: 1.5px solid #0284C7; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.72rem; font-weight: 800; color: #0369A1; text-transform: uppercase; letter-spacing: 0.5px;">
                    OPTION A // SMARTPHONE LIVE GPS TELEMETRY
                </span>
                <span style="background: #EFF6FF; color: #0284C7; font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; border: 1px solid #BAE6FD;">
                    DEVICE SENSOR
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #334155; line-height: 1.5;">
                Select your status and tap the button below. If your browser asks for permission, tap <b>Allow (Izinkan)</b>. (If already allowed, your GPS coordinates are locked immediately). Then tap <b>Confirm &amp; Transmit</b> to stream your live location to the <b>PMO Command Center Radar Map</b>.
            </div>
        </div>
    """, unsafe_allow_html=True)

    gps_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: transparent; padding: 2px 0 6px 0; }}
            .status-select-wrap {{
                margin-bottom: 10px;
            }}
            .status-select-wrap label {{
                display: block;
                font-size: 0.72rem;
                font-weight: 800;
                color: #475569;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }}
            .status-select {{
                width: 100%;
                padding: 10px 12px;
                font-size: 0.85rem;
                font-weight: 700;
                border-radius: 6px;
                border: 1.5px solid #CBD5E1;
                background: #FFFFFF;
                color: #0F172A;
                outline: none;
            }}
            .status-select:focus {{
                border-color: #0284C7;
            }}
            .btn-gps {{
                display: block;
                width: 100%;
                background: #0284C7;
                color: #FFFFFF;
                font-weight: 800;
                font-size: 0.90rem;
                padding: 14px 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                letter-spacing: 0.4px;
                text-transform: uppercase;
                text-align: center;
                text-decoration: none;
                transition: all 0.2s ease;
                box-shadow: 0 2px 4px rgba(2, 132, 199, 0.25);
            }}
            .btn-gps:hover {{ background: #0369A1; }}
            .btn-gps:active {{ transform: scale(0.99); }}
            .btn-gps:disabled {{ opacity: 0.75; cursor: wait; }}
            .status-box {{
                margin-top: 10px;
                padding: 10px 12px;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                font-size: 0.76rem;
                color: #475569;
                font-family: monospace;
                display: none;
                line-height: 1.5;
            }}
        </style>
    </head>
    <body>
        <form id="gps-form" action="{base_host_url}/" method="GET" target="_top" style="display:none;">
            <input type="hidden" name="checkin" value="{team['team_code']}">
            <input type="hidden" name="site" value="{site['site_id']}">
            <input type="hidden" name="lat" id="form-lat" value="">
            <input type="hidden" name="lon" id="form-lon" value="">
            <input type="hidden" name="acc" id="form-acc" value="8.0">
            <input type="hidden" name="gps_confirmed" value="1">
            <input type="hidden" name="status" id="form-status" value="Confirmed - En Route">
        </form>

        <div class="status-select-wrap">
            <label for="sel-gps-status">Operational Status:</label>
            <select id="sel-gps-status" class="status-select">
                <option value="Confirmed - En Route" selected>Confirmed - En Route</option>
                <option value="On-Site Active (WIP)">On-Site Active (WIP)</option>
                <option value="Task Completed / Ready for ATP">Task Completed / Ready for ATP</option>
                <option value="Standby / Awaiting Material">Standby / Awaiting Material</option>
            </select>
        </div>

        <button id="btn-gps-trigger" class="btn-gps" onclick="requestDeviceGps()">
            TRANSMIT MY PHONE LIVE LOCATION (GPS) TO RADAR
        </button>
        <div id="gps-feedback" class="status-box"></div>
        <a id="btn-gps-transmit" class="btn-gps" style="display:none; margin-top:10px; background:#059669; padding: 14px 16px; font-weight: 800; font-size: 0.90rem; text-decoration: none;" href="#" target="_top">
            CONFIRM &amp; TRANSMIT GPS TO RADAR
        </a>

        <script>
        function requestDeviceGps() {{
            const btn = document.getElementById('btn-gps-trigger');
            const box = document.getElementById('gps-feedback');
            const sel = document.getElementById('sel-gps-status');
            const chosenStatus = sel ? sel.value : 'Confirmed - En Route';

            btn.disabled = true;
            btn.style.background = '#0369A1';
            btn.innerText = 'ACQUIRING DEVICE LOCATION...';
            box.style.display = 'block';
            box.innerHTML = 'Acquiring smartphone GPS sensor location...<br>Please tap <b>Allow</b> (Izinkan) if prompted by your browser.';

            if (!navigator.geolocation) {{
                btn.disabled = false;
                btn.style.background = '#DC2626';
                btn.innerText = 'GPS NOT SUPPORTED ON THIS BROWSER';
                box.innerHTML = '<span style="color:#DC2626; font-weight:bold;">Browser does not support Geolocation API. Please paste WhatsApp location pin in Option B below.</span>';
                return;
            }}

            // Attempt 1: High accuracy satellite GPS (5s timeout)
            navigator.geolocation.getCurrentPosition(
                function(pos) {{
                    handleGpsSuccess(pos, chosenStatus);
                }},
                function(err) {{
                    // Fallback to cellular/network triangulation if satellite GPS timed out or weak indoors
                    if (err.code === 3 || err.code === 2) {{
                        box.innerHTML = 'Acquiring via cellular / Wi-Fi triangulation...';
                        navigator.geolocation.getCurrentPosition(
                            function(pos2) {{
                                handleGpsSuccess(pos2, chosenStatus);
                            }},
                            function(err2) {{
                                handleGpsError(err2);
                            }},
                            {{ enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }}
                        );
                    }} else {{
                        handleGpsError(err);
                    }}
                }},
                {{
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                }}
            );
        }}

        function handleGpsSuccess(pos, chosenStatus) {{
            const btn = document.getElementById('btn-gps-trigger');
            const box = document.getElementById('gps-feedback');
            const lat = pos.coords.latitude.toFixed(5);
            const lon = pos.coords.longitude.toFixed(5);
            const acc = Math.round(pos.coords.accuracy || 10);

            btn.style.background = '#059669';
            btn.innerText = 'LOCATION ACQUIRED (' + lat + ', ' + lon + ')';
            box.innerHTML = '<span style="color:#059669; font-weight:bold;">GPS LOCKED: Lat ' + lat + ', Lon ' + lon + ' (Accuracy: ' + acc + 'm).<br>Location permission is ACTIVE. Transmitting live telemetry to PMO Radar...</span>';

            document.getElementById('form-lat').value = lat;
            document.getElementById('form-lon').value = lon;
            document.getElementById('form-acc').value = acc;
            document.getElementById('form-status').value = chosenStatus;

            const targetUrl = '{base_host_url}/?checkin=' + encodeURIComponent('{team["team_code"]}') +
                              '&site=' + encodeURIComponent('{site["site_id"]}') +
                              '&lat=' + lat +
                              '&lon=' + lon +
                              '&acc=' + acc +
                              '&gps_confirmed=1' +
                              '&status=' + encodeURIComponent(chosenStatus);

            const link = document.getElementById('btn-gps-transmit');
            link.href = targetUrl;
            link.innerHTML = 'CONFIRM &amp; TRANSMIT GPS (' + lat + ', ' + lon + ') TO RADAR';
            link.style.display = 'block';

            setTimeout(function() {{
                try {{
                    window.top.location.href = targetUrl;
                }} catch(e) {{
                    try {{
                        link.click();
                    }} catch(e2) {{
                        try {{
                            document.getElementById('gps-form').submit();
                        }} catch(e3) {{}}
                    }}
                }}
            }}, 350);
        }}

        function handleGpsError(err) {{
            const btn = document.getElementById('btn-gps-trigger');
            const box = document.getElementById('gps-feedback');
            btn.disabled = false;
            btn.style.background = '#DC2626';
            btn.innerText = 'RETRY GPS LOCATION PERMISSION';

            let reason = 'Failed to acquire GPS: ';
            if (err.code === 1) {{
                reason = 'Location permission was blocked in your browser settings.<br><b>Easy Solution:</b> Use <b>Option B below</b> to paste your WhatsApp location pin without browser permission.';
            }} else if (err.code === 2) {{
                reason = 'Position unavailable. Please use Option B below to paste your WhatsApp location pin.';
            }} else if (err.code === 3) {{
                reason = 'GPS request timed out. Please tap Retry or use Option B below.';
            }} else {{
                reason += err.message;
            }}
            box.innerHTML = '<span style="color:#DC2626; font-weight:bold;">' + reason + '</span>';
        }}
        </script>
    </body>
    </html>
    """
    components.html(gps_html, height=340)

    # Option B: Paste WhatsApp Location Pin / Google Maps Link
    with st.container(border=True):
        st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.88rem; color: #0F172A; text-transform: uppercase; letter-spacing: 0.3px;">
                    OPTION B: PASTE WHATSAPP LOCATION PIN / GOOGLE MAPS LINK
                </span>
                <span style="background: #F1F5F9; color: #475569; font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; border: 1px solid #E2E8F0;">
                    100% RELIABLE // NO PERMISSION NEEDED
                </span>
            </div>
            <div style="font-size: 0.76rem; color: #64748B; margin-bottom: 10px; line-height: 1.4;">
                In WhatsApp, tap <b>Attach (+) &gt; Location &gt; Share Live Location</b> (or Send your current location). Copy that message or Google Maps link, and paste it here:
            </div>
        """, unsafe_allow_html=True)

        col_b_in, col_b_btn = st.columns([3, 1])
        with col_b_in:
            pasted_pin_text = st.text_input(
                "WhatsApp Pin or Maps Link:",
                placeholder="e.g. https://maps.google.com/?q=-7.6450,112.9050 or -7.6450, 112.9050",
                key="input_portal_pasted_pin",
                label_visibility="collapsed"
            )
        with col_b_btn:
            btn_transmit_pin = st.button("Transmit Pin to Radar", type="primary", use_container_width=True, key="btn_portal_paste_submit")

        if btn_transmit_pin:
            clean_portal_pin = pasted_pin_text.strip() if pasted_pin_text else ""
            if not clean_portal_pin:
                st.error("Please paste your WhatsApp location pin or Google Maps URL.")
            elif "checkin=" in clean_portal_pin or "trycloudflare" in clean_portal_pin or "localhost:" in clean_portal_pin:
                st.warning("That is the Field Check-In portal web address. In this box, please paste a Google Maps location link (e.g. https://maps.google.com/?q=-7.2575,112.7521) or raw coordinate numbers (e.g. -7.2575, 112.7521) from WhatsApp.")
            else:
                coords = FleetTrackingService.parse_location_string(clean_portal_pin)
                if coords:
                    p_lat, p_lon = coords
                    ok, msg = FleetTrackingService.record_team_checkin(
                        team_code=team["team_code"],
                        site_id=site["site_id"],
                        lat=p_lat,
                        lon=p_lon,
                        status="Confirmed - En Route",
                        accuracy_m=5.0,
                        user_agent="Mobile WhatsApp Pin Portal",
                        notes="Live location transmitted via WhatsApp pin paste"
                    )
                    if ok:
                        st.session_state["portal_checkin_success"] = True
                        st.session_state["confirmed_portal_lat"] = p_lat
                        st.session_state["confirmed_portal_lon"] = p_lon
                        st.session_state["confirmed_portal_acc"] = 5.0
                        st.session_state["confirmed_portal_status"] = "Confirmed - En Route"
                        st.toast("WhatsApp live location transmitted to PMO Radar.")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("Could not find valid coordinates in the pasted text. Please paste a link like https://maps.google.com/?q=-7.6450,112.9050 or '-7.6450, 112.9050'.")

    # Option C: Advanced / Manual Coordinates (Collapsed by default)
    with st.expander("Option C: Advanced / Manual Coordinate Entry", expanded=False):
        st.markdown("""
            <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 10px;">
                Use this form only if you need to manually calibrate specific test coordinates.
            </div>
        """, unsafe_allow_html=True)

        sel_status_c = st.radio(
            "Operational Status:",
            options=[
                "Confirmed - En Route",
                "On-Site Active (WIP)",
                "Task Completed / Ready for ATP",
                "Standby / Awaiting Material"
            ],
            index=0,
            key="portal_sel_status_manual"
        )

        col_pos1, col_pos2 = st.columns(2)
        default_manual_lat = float(st.session_state.get("confirmed_portal_lat") or (team.get("current_lat") if team.get("current_lat") is not None else site.get("lat", -8.5520)))
        default_manual_lon = float(st.session_state.get("confirmed_portal_lon") or (team.get("current_lon") if team.get("current_lon") is not None else site.get("lon", 125.5711)))

        with col_pos1:
            in_lat = st.number_input("GPS Latitude (Lat):", value=default_manual_lat, format="%.5f", key="input_manual_portal_lat")
        with col_pos2:
            in_lon = st.number_input("GPS Longitude (Lon):", value=default_manual_lon, format="%.5f", key="input_manual_portal_lon")

        in_notes = st.text_input(
            "Field Notes / Situational Remarks (Optional):",
            placeholder="e.g. En route via main corridor, ETA 45 mins",
            key="portal_notes_manual"
        )

        if st.button("Transmit Manual Coordinates to Radar", type="primary", use_container_width=True, key="btn_portal_manual_submit"):
            ok, msg = FleetTrackingService.record_team_checkin(
                team_code=team["team_code"],
                site_id=site["site_id"],
                lat=in_lat,
                lon=in_lon,
                status=sel_status_c,
                user_agent="Mobile Browser Manual Form",
                notes=in_notes
            )
            if ok:
                st.session_state["portal_checkin_success"] = True
                st.session_state["confirmed_portal_lat"] = in_lat
                st.session_state["confirmed_portal_lon"] = in_lon
                st.session_state["confirmed_portal_status"] = sel_status_c
                st.toast("Manual coordinates successfully transmitted to PMO.")
                st.rerun()
            else:
                st.error(msg)

    if st.session_state.get("portal_checkin_success"):
        c_lat = float(st.session_state.get("confirmed_portal_lat", site.get("lat", -8.5520)))
        c_lon = float(st.session_state.get("confirmed_portal_lon", site.get("lon", 125.5711)))
        c_acc = float(st.session_state.get("confirmed_portal_acc", 8.0))
        c_stat = str(st.session_state.get("confirmed_portal_status", "Confirmed - En Route"))

        geo = FleetTrackingService.calculate_geofence_status(
            team_lat=c_lat,
            team_lon=c_lon,
            site_lat=site.get("lat"),
            site_lon=site.get("lon"),
            checkin_status=c_stat,
            accessible_route_km=site.get("accessible_route_km")
        )

        st.markdown(f"""
            <div style="background: #F0FDF4; border: 1.5px solid #22C55E; border-left: 5px solid #16A34A; border-radius: 8px; padding: 14px 18px; margin: 14px 0;">
                <div style="font-weight: 800; font-size: 0.92rem; color: #15803D;">
                    LIVE TELEMETRY ACTIVE ON PMO COMMAND RADAR
                </div>
                <div style="font-size: 0.80rem; color: #166534; margin-top: 6px; line-height: 1.5;">
                    Crew <b>{team.get('team_name')}</b> ({team.get('team_code')}) successfully checked in with status <b>{c_stat}</b>.
                    <br>
                    Live Coordinates: <b>{c_lat:.5f}, {c_lon:.5f}</b> (Accuracy: {c_acc:.1f} m).
                    <br>
                    Geofence Audit: <span style="background: {geo['badge_bg']}; color: {geo['badge_fg']}; border: 1px solid {geo['badge_border']}; padding: 2px 6px; border-radius: 4px; font-weight: 700;">{geo['flag_label']}</span>
                    &bull; Distance to Target Site: <b>{geo['dist_km']} km</b>.
                    <br>
                    Your smartphone position is actively streaming on the PMO Command Center Radar map. Dispatchers can now track your transit in real-time.
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    def _go_to_full_dashboard():
        st.query_params.clear()
        st.query_params["nav"] = "rollout"
        st.session_state["show_welcome"] = False
        st.session_state["pending_nav"] = "Rollout"

    st.button("Open PMO Command Center Dashboard", on_click=_go_to_full_dashboard, use_container_width=True, key="btn_portal_to_dashboard")


def render_welcome_page():
    """Renders edge-to-edge minimalist executive welcome portal."""
    bg_b64 = get_base64_image("assets/welcome_bg.png")

    # 1. Full-Bleed Viewport Styling & Minimalist Button
    welcome_css = """
        <style>
            /* Render background image directly on stApp root shell */
            html, body, [data-testid="stAppViewContainer"], .stApp {
                background: #070D1E url('data:image/png;base64,__BG_B64__') center right / cover no-repeat fixed !important;
                overflow-x: hidden !important;
            }
            /* Directional gradient overlay on main section */
            [data-testid="stAppViewContainer"] > section.main {
                background: linear-gradient(90deg, rgba(7, 13, 30, 0.94) 0%, rgba(7, 13, 30, 0.80) 45%, rgba(7, 13, 30, 0.15) 75%, rgba(7, 13, 30, 0.30) 100%) !important;
                padding: 0 !important;
                margin: 0 !important;
                min-height: 100vh !important;
                overflow-x: hidden !important;
            }
            .main .block-container {
                background: transparent !important;
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
                min-height: 100vh !important;
            }
            header[data-testid="stHeader"] {
                display: none !important;
            }

            /* Prevent Streamlit's jarring dimming/ghosting when clicking Enter */
            [data-stale="true"],
            .stElementContainer[data-stale="true"],
            div[data-testid="stVerticalBlock"][data-stale="true"],
            div[data-testid="stAppViewContainer"][data-stale="true"],
            .main[data-stale="true"] {
                opacity: 1 !important;
                filter: none !important;
                transition: none !important;
            }
            div[data-testid="stStatusWidget"] {
                display: none !important;
                visibility: hidden !important;
            }

            /* Hide Streamlit default heading anchor link icons */
            a.anchor-link,
            [data-testid="stMarkdownContainer"] a.anchor-link,
            h1 a, h2 a, h3 a {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                height: 0 !important;
            }

            /* Minimalist Enter Action Button */
            div[class*="st-key-btn_welcome_enter"] {
                margin-top: clamp(160px, 35vh, 280px) !important;
                margin-left: 0 !important;
                padding-left: 0 !important;
                max-width: 220px !important;
            }
            div[class*="st-key-btn_welcome_enter"] button {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
                color: #FFFFFF !important;
                font-size: 1.15rem !important;
                font-weight: 700 !important;
                letter-spacing: 2px !important;
                text-transform: uppercase !important;
                padding: 13px 42px !important;
                border-radius: 6px !important;
                border: 1px solid rgba(56, 189, 248, 0.6) !important;
                box-shadow: 0 4px 22px rgba(2, 132, 199, 0.45) !important;
                transition: all 0.15s ease !important;
                cursor: pointer !important;
                width: 100% !important;
            }
            div[class*="st-key-btn_welcome_enter"] button:hover {
                background: linear-gradient(135deg, #0369A1 0%, #0284C7 100%) !important;
                border-color: #7DD3FC !important;
                box-shadow: 0 6px 30px rgba(56, 189, 248, 0.7) !important;
                transform: translateY(-2px) scale(1.02) !important;
            }
            div[class*="st-key-btn_welcome_enter"] button:active {
                transform: translateY(1px) scale(0.98) !important;
                box-shadow: 0 2px 10px rgba(2, 132, 199, 0.6) !important;
            }
        </style>
    """.replace("__BG_B64__", bg_b64)
    st.markdown(welcome_css, unsafe_allow_html=True)

    # 2. Main Minimalist Hero Area (Left Spacer, Hero Content, Artwork Showcase)
    col_spacer, col_hero, col_art = st.columns([0.06, 0.44, 0.50], vertical_alignment="top")
    
    with col_hero:
        st.markdown(textwrap.dedent("""
            <div style="padding-top: 5.5vh; max-width: 440px; box-sizing: border-box; margin-left: 0; padding-left: 0; text-align: left;">
                <h1 style="font-size: clamp(2.0rem, 2.7vw, 2.6rem); font-weight: 800; color: #FFFFFF; line-height: 1.18; margin: 0; letter-spacing: -0.03em; text-shadow: 0 4px 24px rgba(0,0,0,0.9); font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: left;">
                    Welcome to<br>
                    <span style="background: linear-gradient(135deg, #FFFFFF 0%, #38BDF8 55%, #0284C7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        SAMVAD PMO<br>Command Center
                    </span>
                </h1>
            </div>
        """).strip(), unsafe_allow_html=True)

        def _on_welcome_enter_click():
            st.session_state["show_welcome"] = False
            st.session_state["pending_nav"] = "Dashboard"
            st.query_params["nav"] = "dashboard"

        st.button(
            "Enter",
            key="btn_welcome_enter",
            on_click=_on_welcome_enter_click,
            use_container_width=True,
            type="primary"
        )

    with col_art:
        st.write("")

    # 3. Blended Minimalist Copyright (Ngeblend secara elegan di bagian bawah)
    st.markdown(textwrap.dedent("""
        <div style="position: fixed; bottom: 24px; left: 0; width: 100%; text-align: center; color: rgba(203, 213, 225, 0.45); font-size: 0.82rem; font-weight: 500; letter-spacing: 0.8px; font-family: 'Inter', -apple-system, sans-serif; z-index: 10; pointer-events: none;">
            SAMVAD PMO COMMAND CENTER &bull; Copyright 2026
        </div>
    """).strip(), unsafe_allow_html=True)


# Session State Initialization for Welcome Page vs Main Menu
if "show_welcome" not in st.session_state:
    if "nav" in st.query_params or "checkin" in st.query_params:
        if st.query_params.get("nav") in ["logout", "portal"]:
            st.session_state["show_welcome"] = True
        else:
            st.session_state["show_welcome"] = False
    else:
        st.session_state["show_welcome"] = True

# View Router: Welcome Landing Page vs Mobile Field Check-In vs Main Operational Modules
if "checkin" in st.query_params:
    render_field_checkin_portal()
elif st.session_state["show_welcome"]:
    render_welcome_page()
else:
    # Reset styling from welcome portal back to standard NOC dashboard with seamless fade
    st.markdown("""
        <style>
            html, body, .stApp, [data-testid="stAppViewContainer"] {
                background: #F1F3F6 !important;
                background-image: none !important;
            }
            [data-testid="stAppViewContainer"] > section.main {
                background: #F1F3F6 !important;
                background-image: none !important;
            }
            .main .block-container {
                max-width: 100% !important;
                padding-top: 56px !important;
                padding-left: 1.25rem !important;
                padding-right: 1.25rem !important;
                padding-bottom: 2rem !important;
                display: block !important;
                min-height: auto !important;
                animation: seamlessFadeIn 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
            }
            @keyframes seamlessFadeIn {
                0% {
                    opacity: 0.15;
                    transform: translateY(3px);
                }
                100% {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        </style>
    """, unsafe_allow_html=True)

    # Render Fixed Top Dark Ribbon & Obtain Selected Nav Tab
    active_nav = render_top_ribbon()

    # View Dispatcher (Instantaneous WebSocket Switching)
    if active_nav == "Dashboard":
        render_noc_control_tower()
    elif active_nav == "PaaS Rollout":
        render_plan_tab()
    elif active_nav == "Customs & Logistics":
        render_unified_module_header(
            module_label="CUSTOMS & LOGISTICS",
            breadcrumb_trail="Overview &nbsp;&rsaquo;&nbsp; Supply Chain &nbsp;&rsaquo;&nbsp; <b>Customs Inbound & Maritime AIS Cargo Vessel Radar (25%)</b>",
            badge_text="Target: 0% Logistics Delays",
            badge_bg="#EFF6FF",
            badge_color="#1D4ED8",
            badge_border="#BFDBFE"
        )
        render_module1()
    elif active_nav == "SG&A Finance":
        render_unified_module_header(
            module_label="SG&A FINANCE",
            breadcrumb_trail="Overview &nbsp;&rsaquo;&nbsp; Financial Control &nbsp;&rsaquo;&nbsp; <b>SG&A Financial Sentinel (25%)</b>",
            badge_text="Target: SG&A &le; 12.0% Revenue Cap",
            badge_bg="#ECFDF5",
            badge_color="#065F46",
            badge_border="#A7F3D0"
        )
        render_module2()
    elif active_nav in ["Site Operations", "site_ops", "operations", "module3"]:
        render_unified_module_header(
            module_label="SITE OPERATIONS",
            breadcrumb_trail="Overview &nbsp;&rsaquo;&nbsp; Field & SLA Ops &nbsp;&rsaquo;&nbsp; <b>Site SLA & Rapid Outage Recovery (25%)</b>",
            badge_text="Target: &ge; 99.0% Nationwide Availability",
            badge_bg="#FEF3C7",
            badge_color="#92400E",
            badge_border="#FDE68A"
        )
        render_module3()
    elif active_nav in ["Reports", "reports", "report", "module4"]:
        render_report_tab()
    elif active_nav in ["Update & Sync", "update", "sync", "excel"]:
        render_update_tab()
    elif active_nav in ["Settings", "settings", "audit"]:
        render_settings_and_data_management()
    else:
        render_noc_control_tower()
