"""
Samvad PMO & NOC Operations Command Center.
100-Site Timor-Leste National Rollout | RAID-led Prioritization, Territorial Routing & Execution Waves.
Origin Starting Point: Port Dili Terminal (Lat: -8.5520, Lon: 125.5711).
"""
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date

from config.settings import (
    APP_TITLE,
    APP_SUBTITLE,
    VERSION,
    COMPANY_NAME,
    DOCUMENT_OWNER,
    DATABASE_PATH
)
from database.connection import init_db, query_df, execute_write
from database.seed_data import seed_all_data
from database.timor_sites_data import seed_timor_100_sites, PORT_DILI_COORDS, get_timor_100_sites_dataframe
from services.kpi_engine import KPICalculator
from services.excel_sync_service import ExcelSyncService
from modules.module1_customs.ui import render_module1
from modules.module2_sga.ui import render_module2
from modules.module3_site_ops.ui import render_module3
from modules.module4_reporting.ui import render_module4

# Streamlit Page Setup
st.set_page_config(
    page_title=f"Samvad NOC & PMO Command Center - Timor-Leste 100 Sites",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast NOC Styling
st.markdown("""
<style>
    .noc-header {
        font-size: 1.9rem;
        font-weight: 900;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
    }
    .noc-sub {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 16px;
    }
    .kpi-pill {
        border-radius: 10px;
        padding: 12px 16px;
        border: 1px solid #E2E8F0;
        background: #F8FAFC;
    }
    .stat-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

# Bootstrap Database & Seed 100 Sites
@st.cache_resource
def bootstrap_all_data():
    seed_all_data(DATABASE_PATH)
    seed_timor_100_sites(DATABASE_PATH)
    ExcelSyncService.generate_master_template()
    return True

bootstrap_all_data()

# Sidebar Navigation
with st.sidebar:
    st.markdown(f"### 📡 SAMVAD NOC CONTROL TOWER")
    st.caption(f"**Timor-Leste 100-Site Rollout** &bull; v{VERSION}")
    st.markdown("---")

    menu_selection = st.radio(
        "NOC Command Center Workflow:",
        [
            "🖥️ NOC Control Tower (100 Sites & Distance)",
            "📅 PLAN (Cadence, Waves & Forward Hubs)",
            "⚡ UPDATE (Quick Actions & Master Excel Sync)",
            "📄 REPORT (Friday 14:00 Auto-Run & I&C)",
            "🚢 Module 1: Customs & Logistics (25%)",
            "💰 Module 2: SG&A Financial Sentinel (25%)",
            "📡 Module 3: Site SLA Dashboard (25%)",
            "⚙️ System Settings & Audit Logs"
        ]
    )

    st.markdown("---")
    st.markdown("#### ⚓ Central Staging Anchor")
    st.caption("**Port Dili Terminal (Origin):** `-8.5520, 125.5711`")
    st.caption("**Forward Hubs:** Baucau, Suai, Oecusse")
    st.caption(f"**PMO Lead / Maintainer:** {DOCUMENT_OWNER}")
    st.caption(f"**Live Time:** {datetime.now().strftime('%d %b %Y | %H:%M WIB')}")


def render_noc_control_tower():
    st.markdown("<div class='noc-header'>TIMOR-LESTE 100-SITE NOC CONTROL TOWER</div>", unsafe_allow_html=True)
    st.markdown("<div class='noc-sub'>National PaaS Delivery Blueprint &bull; Accessible Route Distances from <b>Port Dili (Central Staging)</b></div>", unsafe_allow_html=True)

    # 1. High-Level Executive KPI Header
    kpi_calc = KPICalculator()
    summary = kpi_calc.get_overall_kpi_summary()
    score = summary["overall_score"]
    tier_label = summary["tier_label"]

    st.markdown(
        f"""
        <div style="background: linear-gradient(90deg, #0F172A 0%, #1E293B 100%); color: white; padding: 18px 22px; border-radius: 12px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div>
                    <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; color: #38BDF8; font-weight: bold;">Executive KPI Scorecard</span>
                    <h2 style="margin: 4px 0 0 0; color: white; font-size: 1.6rem; font-weight: 900;">{tier_label}</h2>
                    <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #94A3B8;">
                        Annex B Employment Agreement Compliance &bull; 100 Sites Across 11 Districts in Timor-Leste
                    </p>
                </div>
                <div style="text-align: right; background: rgba(15, 23, 42, 0.7); padding: 10px 18px; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.25);">
                    <div style="font-size: 2.3rem; font-weight: 900; color: #10B981; line-height: 1;">{score:.1f}%</div>
                    <div style="font-size: 0.75rem; font-weight: 700; color: #E2E8F0; margin-top: 3px;">Composite KPI Health</div>
                    <span style="background-color: #10B981; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; display: inline-block; margin-top: 3px;">MAXIMUM 120% TIER</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Key Baseline Portfolio Metrics (from Blueprint Page 1-3)
    df_100 = query_df("SELECT * FROM timor_sites_100 ORDER BY accessible_route_km ASC")
    
    total_sites = len(df_100)
    q1_cnt = len(df_100[df_100["quadrant"] == "Q1-Critical"])
    no_dg_cnt = len(df_100[df_100["has_dg"] == "No DG"])
    zero_bk_cnt = len(df_100[df_100["backup_hours"] == 0.0])
    dili_cnt = len(df_100[df_100["district"] == "Dili"])
    extreme_cnt = len(df_100[df_100["is_extreme"] == 1])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Sites", f"{total_sites}", delta="11 Districts")
    c2.metric("Q1 Critical", f"{q1_cnt}", delta="Primary Priority", delta_color="inverse")
    c3.metric("Without DG", f"{no_dg_cnt}", delta="Power Fragile", delta_color="inverse")
    c4.metric("0h Backup", f"{zero_bk_cnt}", delta="High Risk", delta_color="inverse")
    c5.metric("Dili Cluster", f"{dili_cnt}", delta="63% of Portfolio")
    c6.metric("Extreme Sites", f"{extreme_cnt}", delta="Contingency Alert", delta_color="inverse")

    st.markdown("---")

    # 3. Interactive Timor-Leste GIS Map
    m_col1, m_col2 = st.columns([3, 1])
    with m_col1:
        st.subheader("🗺️ Geographic Wallboard: 100 Telecom Sites & Distance from Port Dili")
        st.caption("Point size indicates Priority Index. Hover to inspect Accessible Road / Ferry Route Distance and Estimated Travel Time from Port Dili.")
    with m_col2:
        map_style_opt = st.selectbox(
            "🗺️ Base Map Layer:",
            ["OpenStreetMap (Full GIS & Roads)", "Carto Darkmatter (NOC Dark)", "Carto Positron (Clean Light)"],
            index=0
        )

    # Determine map style code
    if "OpenStreetMap" in map_style_opt:
        selected_style = "open-street-map"
    elif "Darkmatter" in map_style_opt:
        selected_style = "carto-darkmatter"
    else:
        selected_style = "carto-positron"

    # Scatter map with real geographical tiles
    fig_map = px.scatter_map(
        df_100,
        lat="lat",
        lon="lon",
        color="priority_tier",
        size="priority_index",
        size_max=18,
        hover_name="site_name",
        hover_data={
            "site_id": True,
            "district": True,
            "accessible_route_km": ":.1f km",
            "est_travel_time": True,
            "transport_mode": True,
            "assigned_forward_hub": True,
            "quadrant": True,
            "has_dg": True,
            "backup_hours": True,
            "lon": False,
            "lat": False
        },
        color_discrete_map={
            "P0 | Immediate": "#EF4444",      # Red
            "P1 | Early wave": "#F59E0B",     # Amber
            "P2 | Planned": "#3B82F6",        # Blue
            "P3 | Monitor": "#64748B"         # Slate Grey
        },
        zoom=7.9,
        center=dict(lat=-8.78, lon=125.72),
        map_style=selected_style,
        title=None
    )

    # Maritime Ferry Route 1: Port Dili to Atauro Island (36.5 km)
    fig_map.add_trace(go.Scattermap(
        lat=[-8.5520, -8.2700],
        lon=[125.5711, 125.6000],
        mode="lines",
        line=dict(width=2.5, color="#A855F7"),
        name="🚢 Ferry: Dili ↔ Atauro (36.5 km)",
        hoverinfo="text",
        text="Maritime Corridor: Port Dili to Atauro Island (1.5 - 2 hrs)"
    ))

    # Maritime Ferry Route 2: Port Dili to Oecusse Enclave (~148 km via Berlin Nakroma)
    fig_map.add_trace(go.Scattermap(
        lat=[-8.5520, -8.60, -9.00, -9.2000],
        lon=[125.5711, 125.00, 124.60, 124.3700],
        mode="lines",
        line=dict(width=2.5, color="#EC4899"),
        name="🚢 Nakroma: Dili ↔ Oecusse (148 km)",
        hoverinfo="text",
        text="Maritime Enclave Corridor: Port Dili to Lifau/Oecusse (8.5 - 10 hrs)"
    ))

    # Forward Hub Markers (Baucau, Suai, Oecusse)
    fig_map.add_trace(go.Scattermap(
        lat=[-8.4710, -9.3130, -9.2000],
        lon=[126.4580, 125.2570, 124.3700],
        mode="markers+text",
        name="🏢 Forward Hubs (3)",
        text=["🏢 HUB BAUCAU", "🏢 HUB SUAI", "🏢 HUB OECUSSE"],
        textposition="bottom right",
        marker=dict(size=14, color="#F59E0B")
    ))

    # Add Star Marker for Port Dili (Origin)
    fig_map.add_trace(go.Scattermap(
        lat=[PORT_DILI_COORDS[0]],
        lon=[PORT_DILI_COORDS[1]],
        mode="markers+text",
        name="⚓ Port Dili Origin",
        text=["⚓ PORT DILI (ORIGIN)"],
        textposition="top right",
        marker=dict(size=22, color="#10B981")
    ))

    fig_map.update_layout(
        title=None,
        height=560,
        margin=dict(l=0, r=0, t=10, b=50),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.03,
            xanchor="center",
            x=0.5,
            title_text="",
            font=dict(size=11)
        )
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # 4. Filters & Operational Distance Matrix
    st.markdown("---")
    st.subheader("📊 Operational Master Matrix: Accessible Routes & Dispatch Readiness")

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    with fcol1:
        sel_dist = st.multiselect("Filter by District:", sorted(df_100["district"].unique()), default=[])
    with fcol2:
        sel_tier = st.multiselect("Filter by Priority Tier:", ["P0 | Immediate", "P1 | Early wave", "P2 | Planned", "P3 | Monitor"], default=[])
    with fcol3:
        sel_zone = st.multiselect("Filter by Deployment Zone:", sorted(df_100["deployment_zone"].unique()), default=[])
    with fcol4:
        search_query = st.text_input("🔍 Search Site ID or Name:", "")

    df_filtered = df_100.copy()
    if sel_dist:
        df_filtered = df_filtered[df_filtered["district"].isin(sel_dist)]
    if sel_tier:
        df_filtered = df_filtered[df_filtered["priority_tier"].isin(sel_tier)]
    if sel_zone:
        df_filtered = df_filtered[df_filtered["deployment_zone"].isin(sel_zone)]
    if search_query:
        df_filtered = df_filtered[
            df_filtered["site_name"].str.contains(search_query, case=False, na=False) |
            df_filtered["site_id"].str.contains(search_query, case=False, na=False)
        ]

    # Show count
    st.caption(f"Showing **{len(df_filtered)}** of 100 sites. Sorted by Accessible Distance from Port Dili.")

    display_cols = [
        "site_id", "site_name", "district", "accessible_route_km", "est_travel_time",
        "transport_mode", "assigned_forward_hub", "priority_tier", "priority_index",
        "quadrant", "revenue_tier", "has_dg", "backup_hours", "readiness_gate", "notes"
    ]

    st.dataframe(
        df_filtered[display_cols].style.format({
            "accessible_route_km": "{:,.1f} km",
            "priority_index": "{:.2f}",
            "backup_hours": "{:.1f} h"
        }),
        use_container_width=True,
        hide_index=True
    )


def render_plan_tab():
    st.markdown("<div class='noc-header'>📅 PLAN: 12-MONTH ROLLOUT CADENCE & FORWARD HUBS</div>", unsafe_allow_html=True)
    st.markdown("<div class='noc-sub'>RAID Delivery Sequencing: Dili Scale &rarr; Insulate Remote High-Risk Clusters &rarr; Forward Hub Discipline</div>", unsafe_allow_html=True)

    # Blueprint 12-Month Cadence Diagram
    st.subheader("1. 12-Month Indicative Delivery Cadence (Blueprint Page 11)")
    cadence_data = [
        {"Phase": "Mobilize / Validate", "Start": "Month 1", "Finish": "Month 2", "Target Sites": 100, "Scope": "Baseline engineering gates & coordinate validation"},
        {"Phase": "Dili Execution Factory", "Start": "Month 2", "Finish": "Month 6", "Target Sites": 63, "Scope": "32 Q1 + 4 Q2 urban sites (Repeatable execution)"},
        {"Phase": "Remote Cluster Rollout", "Start": "Month 4", "Finish": "Month 9", "Target Sites": 19, "Scope": "Southern Lowlands (Suai Hub) & Northern Coastal (Baucau Hub)"},
        {"Phase": "Oecusse & Mountain Spine", "Start": "Month 6", "Finish": "Month 10", "Target Sites": 8, "Scope": "Enclave ferry logistics & extreme mountain access window"},
        {"Phase": "Stabilize & Local Handover", "Start": "Month 9", "Finish": "Month 12", "Target Sites": 100, "Scope": "Local L1/L2 capability transfer & digital sign-off"}
    ]
    st.dataframe(pd.DataFrame(cadence_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("2. Central Staging & Forward Hub Architecture (Page 9)")
    
    hc1, hc2, hc3, hc4 = st.columns(4)
    with hc1:
        st.markdown(
            """
            <div style="background: #1E293B; color: white; padding: 14px; border-radius: 10px; border-top: 4px solid #38BDF8;">
                <h4 style="margin: 0; color: #38BDF8;">CENTRAL STAGING</h4>
                <h3 style="margin: 4px 0 8px 0; color: white;">DILI PORT</h3>
                <p style="font-size: 0.8rem; color: #94A3B8; margin: 0;">
                    Bulk staging &bull; Inbound customs QA &bull; Inventory buffer &bull; Digital onboarding
                </p>
                <div style="margin-top: 8px; font-size: 0.75rem; color: #E2E8F0; font-weight: bold;">Coverage: 63 Sites (Dili & Transition)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with hc2:
        st.markdown(
            """
            <div style="background: #1E293B; color: white; padding: 14px; border-radius: 10px; border-top: 4px solid #3B82F6;">
                <h4 style="margin: 0; color: #60A5FA;">FORWARD HUB</h4>
                <h3 style="margin: 4px 0 8px 0; color: white;">BAUCAU</h3>
                <p style="font-size: 0.8rem; color: #94A3B8; margin: 0;">
                    Northern coastal coverage via Estrada Nacional 1 &bull; Buffer for Lautem & Viqueque
                </p>
                <div style="margin-top: 8px; font-size: 0.75rem; color: #E2E8F0; font-weight: bold;">Road Dist: 125 km (3.5 hrs from Port Dili)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with hc3:
        st.markdown(
            """
            <div style="background: #1E293B; color: white; padding: 14px; border-radius: 10px; border-top: 4px solid #F59E0B;">
                <h4 style="margin: 0; color: #FBBF24;">FORWARD HUB</h4>
                <h3 style="margin: 4px 0 8px 0; color: white;">SUAI</h3>
                <p style="font-size: 0.8rem; color: #94A3B8; margin: 0;">
                    Southern coverage &bull; Protect Zone 3 during dry-season execution window
                </p>
                <div style="margin-top: 8px; font-size: 0.75rem; color: #E2E8F0; font-weight: bold;">Road Dist: 153 km (5.5 hrs from Port Dili)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with hc4:
        st.markdown(
            """
            <div style="background: #1E293B; color: white; padding: 14px; border-radius: 10px; border-top: 4px solid #EF4444;">
                <h4 style="margin: 0; color: #F87171;">FORWARD HUB</h4>
                <h3 style="margin: 4px 0 8px 0; color: white;">OECUSSE</h3>
                <p style="font-size: 0.8rem; color: #94A3B8; margin: 0;">
                    Enclave coverage &bull; Scheduled Berlin Nakroma Ferry maritime staging
                </p>
                <div style="margin-top: 8px; font-size: 0.75rem; color: #E2E8F0; font-weight: bold;">Ferry Route: 145 km (9 hrs from Port Dili)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("3. ⚠️ 4 Extreme Access Sites Flagged for Contingency Staging")
    st.markdown(
        "These 4 sites are explicitly marked **Extreme** due to mountain elevation, steep terrain, or seasonal weather risk. "
        "Strict readiness gates require **pre-allocated contingency spares and 4x4 transport** before dispatch."
    )

    df_ext = query_df("SELECT site_id, site_name, district, accessible_route_km, est_travel_time, transport_mode, priority_tier, notes FROM timor_sites_100 WHERE is_extreme = 1")
    st.dataframe(df_ext, use_container_width=True, hide_index=True)


def render_update_tab():
    st.markdown("<div class='noc-header'>⚡ UPDATE: NOC DISPATCH & MASTER EXCEL SYNC</div>", unsafe_allow_html=True)
    st.markdown("<div class='noc-sub'>Low-Tech Friendly Two-Way Excel Sync or Rapid 1-Click Field Toggles</div>", unsafe_allow_html=True)

    tab_gsheet, tab_sync, tab_action = st.tabs([
        "🌐 Live Google Sheets Cloud Sync", 
        "📋 Master Excel File (Upload / Download)", 
        "🎯 1-Click Field Dispatch Toggles"
    ])

    with tab_gsheet:
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; padding: 18px; border-radius: 10px; margin-bottom: 16px;">
                <h4 style="margin: 0; color: #0284C7;">🌐 Live Google Sheets Cloud Sync (Ideal for Field PICs)</h4>
                <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 0 0;">
                    Field PICs in Dili, Baucau, Suai, and Oecusse can edit rows directly in Google Sheets from any smartphone or laptop. 
                    Paste your Google Sheets link below to pull updates directly into the NOC Command Center in real-time.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        gsheet_url_input = st.text_input(
            "🔗 Google Sheets Share Link:",
            placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit?usp=sharing",
            help="Ensure the Google Sheet link sharing is set to 'Anyone with the link can view'."
        )

        col_gs1, col_gs2 = st.columns([2, 3])
        with col_gs1:
            if st.button("🔄 Sync Live from Google Sheets Now", type="primary", use_container_width=True):
                if gsheet_url_input:
                    with st.spinner("Fetching and synchronizing live data from Google Sheets..."):
                        success, msg, stats = ExcelSyncService.sync_from_google_sheets(gsheet_url_input)
                        if success:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.warning("Please enter a valid Google Sheets URL first.")

        with col_gs2:
            st.caption("💡 **Tip for Low-Tech Field PICs**: Lock columns A–H (Site ID, Coordinates, Rectifier) and let PICs only edit column **Readiness Gate (GO / HOLD / ESCALATE)** and **Notes**.")

    with tab_sync:
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; padding: 16px; border-radius: 10px;">
                    <h4 style="margin: 0; color: #1E3A8A;">1. Download Complete Master Tracker (.xlsx)</h4>
                    <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 12px 0;">
                        Contains 5 pre-formatted sheets: Customs, SG&A Expenses, Site Uptime, POC Milestones, and the 
                        <b>100 Timor-Leste Sites with Accessible Route Distances from Port Dili</b>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            excel_path = ExcelSyncService.generate_master_template()
            with open(excel_path, "rb") as f_excel:
                st.download_button(
                    "📥 Download Samvad_Master_Tracker.xlsx",
                    data=f_excel.read(),
                    file_name="Samvad_Master_Tracker_100Sites.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

        with sc2:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; padding: 16px; border-radius: 10px;">
                    <h4 style="margin: 0; color: #0F766E;">2. Upload Updated Spreadsheet</h4>
                    <p style="font-size: 0.85rem; color: #475569; margin: 6px 0 12px 0;">
                        Edit rows offline in Microsoft Excel or Google Sheets, then drop the file here to auto-update the database and recalculate KPI scores.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            up_file = st.file_uploader("Drop updated .xlsx file here", type=["xlsx"], key="noc_uploader")
            if up_file:
                success, msg, stats = ExcelSyncService.sync_from_uploaded_excel(up_file)
                if success:
                    st.success(f"✅ {msg}")
                    st.balloons()
                else:
                    st.error(f"❌ {msg}")

    with tab_action:
        st.subheader("Quick Field Action Toggles")
        df_sites = query_df("SELECT site_id, site_name, readiness_gate, district FROM timor_sites_100 LIMIT 100")
        opts = [f"{r['site_id']} - {r['site_name']} ({r['district']}) [Gate: {r['readiness_gate']}]" for _, r in df_sites.iterrows()]
        
        tc1, tc2 = st.columns(2)
        with tc1:
            chosen = st.selectbox("Select Site to Update Gate:", opts)
            chosen_id = chosen.split()[0]
        with tc2:
            new_gate = st.selectbox("New Readiness Decision (Page 13):", ["GO (Dispatch Ready)", "HOLD (Dependency)", "ESCALATE (High Risk)", "RESEQUENCE (Area Constraint)"])

        if st.button("Apply Readiness Decision", type="primary"):
            execute_write(
                "UPDATE timor_sites_100 SET readiness_gate = ? WHERE site_id = ?",
                (new_gate, chosen_id)
            )
            st.success(f"Site {chosen_id} decision updated to: {new_gate}")
            st.rerun()


def render_report_tab():
    st.markdown("<div class='noc-header'>📄 REPORT: AUTOMATED EXECUTIVE REPORTING</div>", unsafe_allow_html=True)
    st.markdown("<div class='noc-sub'>Friday 14:00 WIB Auto-Reporter & Standardized Client-Ready Acceptance Certificates</div>", unsafe_allow_html=True)
    render_module4()


# Router
if "NOC Control Tower" in menu_selection:
    render_noc_control_tower()
elif "PLAN" in menu_selection:
    render_plan_tab()
elif "UPDATE" in menu_selection:
    render_update_tab()
elif "REPORT" in menu_selection:
    render_report_tab()
elif "Module 1" in menu_selection:
    render_module1()
elif "Module 2" in menu_selection:
    render_module2()
elif "Module 3" in menu_selection:
    render_module3()
elif "Settings" in menu_selection:
    st.markdown("## ⚙️ Settings & System Audit Trail")
    df_logs = query_df("SELECT * FROM notification_audit_logs ORDER BY sent_at DESC LIMIT 50")
    st.dataframe(df_logs, use_container_width=True)
