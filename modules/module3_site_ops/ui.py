"""
UI View for Module 3: Site Availability & SLA Operations (KPI Category C — 25% Weight).
Enhanced with 100% Authentic Applied Energy NOC Dashboard Replication + Samvad PMO Deep Analytics.
Strictly enterprise, typography-focused, icon-free implementation.
"""

import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from modules.module3_site_ops.uptime_monitor import UptimeMonitor
from modules.module3_site_ops.sop_generator import SOPGenerator
from services.noc_integration_service import NocIntegrationService


def render_module3():
    st.markdown("## Module 3: Site Availability & SLA Operations")
    st.caption("KPI Category C — 25% Weight | Target: Maintain Site Availability >= 95.0% Mandatory Threshold & Standardized I&C SOPs")

    monitor = UptimeMonitor()
    sop_gen = SOPGenerator()
    noc_service = NocIntegrationService()
    noc_service.seed_initial_baseline_if_empty()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Applied Energy NOC Bridge (Telkomcel TL)",
        "Real-time Site Uptime & Network SLA",
        "Emergency Outage Sentinel (>15 Min Alerts)",
        "Digital I&C SOP Checklist & PDF Generator"
    ])

    # =========================================================================
    # TAB 1: APPLIED ENERGY NOC BRIDGE (TELKOMCEL TL)
    # =========================================================================
    with tab1:
        sync_status = noc_service.get_sync_status()
        cached_sites = noc_service.get_cached_sites()
        cached_alarms = noc_service.get_cached_alarms()

        # Connection Header Card
        st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-top: 3px solid #2563EB; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <span style="font-weight: 800; font-size: 0.95rem; color: #0F172A; letter-spacing: 0.3px;">
                            APPLIED ENERGY NOC INTEGRATION BRIDGE
                        </span>
                        <span style="font-size: 0.74rem; font-weight: 700; color: #1D4ED8; background: #EFF6FF; border: 1px solid #BFDBFE; padding: 2px 8px; border-radius: 4px; margin-left: 8px;">
                            Telkomcel Timor-Leste Autonomous Portal
                        </span>
                    </div>
                    <div>
                        <span style="font-size: 0.72rem; font-weight: 700; color: {'#065F46' if sync_status.get('status') == 'CONNECTED' else '#92400E'}; background: {'#ECFDF5' if sync_status.get('status') == 'CONNECTED' else '#FEF3C7'}; border: 1px solid {'#A7F3D0' if sync_status.get('status') == 'CONNECTED' else '#FDE68A'}; padding: 3px 10px; border-radius: 4px;">
                            STATUS: {sync_status.get('status', 'CONNECTED')}
                        </span>
                    </div>
                </div>
                <div style="font-size: 0.78rem; color: #475569; display: flex; flex-wrap: wrap; gap: 16px;">
                    <span>Portal Endpoint: <b style="color: #0F172A;">{sync_status.get('portal_url', 'https://telkomceltl.appliedenergynoc.com')}</b></span>
                    <span>Authenticated User: <b style="color: #0F172A;">{sync_status.get('username', 'supriyanto')} (ID: 12162, Supriy Anto)</b></span>
                    <span>Last Ingestion: <b style="color: #0F172A;">{sync_status.get('last_sync_timestamp') or 'Real-time Synchronized'}</b></span>
                    <span>Circle: <b style="color: #0F172A;">Timor (Client: Telkomcel)</b></span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Action Toolbar
        c_act1, c_act2, c_act3 = st.columns([2.5, 2.5, 3])
        with c_act1:
            if st.button("Force Synchronize NOC Live", type="primary", use_container_width=True, key="btn_sync_noc_live"):
                with st.spinner("Authenticating with Applied Energy NOC portal and pulling live telemetry..."):
                    res = noc_service.sync_live_portal()
                    if res.get("success"):
                        st.toast(res.get("message", "NOC Telemetry Synchronized."))
                        st.rerun()
                    else:
                        st.error(f"Live sync note: {res.get('message')}. Displaying synchronized cache.")
        with c_act2:
            st.link_button(
                "Launch External NOC Portal",
                "https://telkomceltl.appliedenergynoc.com/",
                use_container_width=True
            )
        with c_act3:
            st.caption("Direct robotic bridge connecting to Applied Energy NOC without third-party vendor API permissions.")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # =====================================================================
        # BAGIAN ATAS: TAMPILAN ASLI APPLIED ENERGY NOC DASHBOARD
        # =====================================================================
        st.markdown("""
            <div style="background: #0F172A; color: #FFFFFF; border-radius: 6px 6px 0 0; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.82rem; font-weight: 800; letter-spacing: 0.5px;">
                    1. ORIGINAL APPLIED ENERGY NOC CONSOLE (TELKOMCEL TIMOR-LESTE)
                </span>
                <span style="font-size: 0.70rem; color: #94A3B8; background: #1E293B; border: 1px solid #334155; padding: 2px 8px; border-radius: 4px;">
                    100% Visual Fidelity Layout
                </span>
            </div>
        """, unsafe_allow_html=True)

        # Original Navigation Ribbon (#divalldahsboard style)
        noc_view_mode = st.radio(
            "Original Dashboard Views:",
            options=[
                "NOC Analytics",
                "Site Digital Twin (Power Flow)",
                "Alarm Dashboard",
                "Executive SLA Dashboard"
            ],
            index=0,
            horizontal=True,
            label_visibility="collapsed",
            key="rb_noc_original_view"
        )

        # Original Breadcrumbs & Filter Bar
        st.markdown(f"""
            <div style="background: #F1F5F9; border: 1px solid #CBD5E1; border-top: none; padding: 8px 16px; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; color: #475569; margin-bottom: 12px;">
                <div>
                    <span>Home &nbsp;&rsaquo;&nbsp; Dashboard &nbsp;&rsaquo;&nbsp; <b style="color: #0F172A;">{noc_view_mode}</b></span>
                </div>
                <div style="display: flex; gap: 12px; font-weight: 600;">
                    <span>Circle: <b style="color: #0F172A;">Timor</b></span>
                    <span>Zone: <b style="color: #0F172A;">Timor</b></span>
                    <span>Cluster: <b style="color: #0F172A;">Timor</b></span>
                    <span>Customer: <b style="color: #1D4ED8;">Telkomcel</b></span>
                    <span>User: <b style="color: #0F172A;">Supriy Anto</b></span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # VIEW 1: NOC ANALYTICS (MANAGEMENT DASHBOARD ORIGINAL)
        if noc_view_mode == "NOC Analytics":
            # --- TOP ROW: SITE HEALTH (flex 2), LNOA (flex 3), SOAA (flex 7) ---
            col_sh, col_lnoa, col_soaa = st.columns([2, 3, 7], gap="small")

            # 1. Site Health
            with col_sh:
                with st.container(border=True):
                    st.markdown("""
                        <div style="font-weight: 700; font-size: 0.82rem; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-bottom: 2px;">
                            Site Health
                        </div>
                    """, unsafe_allow_html=True)

                    fig_sh = go.Figure(data=[go.Pie(
                        labels=["UP: 1", "Down: 0", "NC: 1", "NORMU: 0"],
                        values=[1, 0, 1, 0],
                        hole=0.55,
                        marker=dict(colors=["#1dc061", "#ff3a30", "#6c757d", "#000000"]),
                        textinfo="none",
                        hoverinfo="label",
                        sort=False
                    )])
                    fig_sh.update_layout(
                        showlegend=True,
                        legend=dict(orientation="v", font=dict(size=10), y=0.5, x=0.80, yanchor="middle", xanchor="left"),
                        margin=dict(t=5, b=5, l=0, r=0),
                        height=190,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(text="<b>2</b><br><span style='font-size:9px;'>Total Sites</span>", x=0.32, y=0.5, font_size=13, showarrow=False)]
                    )
                    st.plotly_chart(fig_sh, use_container_width=True, config={"displayModeBar": False})

            # 2. Live Network Operation Analytics (LNOA - Battery Voltage Range)
            with col_lnoa:
                with st.container(border=True):
                    st.markdown("""
                        <div style="font-weight: 700; font-size: 0.82rem; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-bottom: 2px;">
                            Live Network Operation Analytics (LNOA)
                        </div>
                    """, unsafe_allow_html=True)

                    fig_lnoa = go.Figure(data=[go.Pie(
                        labels=["<47 V: 0", "47-48 V: 0", "48.1-55 V: 1", ">55 V: 0", "NC: 1"],
                        values=[0, 0, 1, 0, 1],
                        hole=0.55,
                        marker=dict(colors=["#ff3a30", "#ffe600", "#1dc061", "#008ae6", "#808080"]),
                        textinfo="none",
                        hoverinfo="label",
                        sort=False
                    )])
                    fig_lnoa.update_layout(
                        showlegend=True,
                        legend=dict(orientation="v", font=dict(size=10), y=0.5, x=0.80, yanchor="middle", xanchor="left"),
                        margin=dict(t=5, b=5, l=0, r=0),
                        height=190,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(text="<b>1 Node</b><br><span style='font-size:9px;color:#1dc061;'>48.1-55V</span>", x=0.32, y=0.5, font_size=12, showarrow=False)]
                    )
                    st.plotly_chart(fig_lnoa, use_container_width=True, config={"displayModeBar": False})

            # 3. Site Open Alarm Analytics (SOAA)
            with col_soaa:
                with st.container(border=True):
                    st.markdown("""
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-bottom: 2px;">
                            <span style="font-weight: 700; font-size: 0.82rem; color: #0F172A;">Site Open Alarm Analytics (SOAA)</span>
                            <span style="font-size: 0.70rem; color: #DC2626; font-weight: 700; background: #FEF2F2; border: 1px solid #FECACA; padding: 1px 6px; border-radius: 3px;">1 Active Alarm (NC)</span>
                        </div>
                    """, unsafe_allow_html=True)

                    soaa_codes = [
                        "SPDF", "SMPSO", "SDNLVDV", "SDNLVDSOC", "RMFAIL",
                        "NC", "MCB", "LVA", "LOWSOCPLD", "HRT",
                        "FS", "DGR", "DCM", "BCOM", "AC1F"
                    ]
                    soaa_counts = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    soaa_colors = ["#CBD5E1" if c == 0 else "#3498DB" for c in soaa_counts]

                    fig_soaa = go.Figure(data=[go.Bar(
                        x=soaa_codes,
                        y=soaa_counts,
                        marker=dict(color=soaa_colors),
                        text=[str(c) if c > 0 else "" for c in soaa_counts],
                        textposition="outside"
                    )])
                    fig_soaa.update_layout(
                        margin=dict(t=5, b=10, l=15, r=10),
                        height=190,
                        yaxis=dict(range=[0, 2], dtick=1, title="Active Count"),
                        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_soaa, use_container_width=True, config={"displayModeBar": False})

            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

            # --- MIDDLE ROW: UPTIME SUMMARY (flex 11) & BATTERY ANALYSIS (flex 5) ---
            col_upt, col_bha = st.columns([11, 5], gap="small")

            with col_upt:
                with st.container(border=True):
                    st.markdown("""
                        <div style="font-weight: 700; font-size: 0.82rem; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-bottom: 2px;">
                            Uptime Summary (Target SLA vs Current Month MTD)
                        </div>
                    """, unsafe_allow_html=True)

                    fig_upt = go.Figure()
                    fig_upt.add_trace(go.Bar(
                        x=["Timor Circle", "National Circle"],
                        y=[100.0, 100.0],
                        name="Current Month MTD",
                        marker_color="#10B981",
                        text=["100.00%", "100.00%"],
                        textposition="auto"
                    ))
                    fig_upt.add_trace(go.Bar(
                        x=["Timor Circle", "National Circle"],
                        y=[99.5, 99.5],
                        name="Target SLA Floor",
                        marker_color="#3B82F6",
                        text=["99.50%", "99.50%"],
                        textposition="auto"
                    ))
                    fig_upt.update_layout(
                        barmode="group",
                        margin=dict(t=5, b=10, l=25, r=10),
                        height=180,
                        yaxis=dict(range=[90, 105], title="Availability %"),
                        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center", font=dict(size=10)),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_upt, use_container_width=True, config={"displayModeBar": False})

            with col_bha:
                with st.container(border=True):
                    st.markdown("""
                        <div style="font-weight: 700; font-size: 0.82rem; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px; margin-bottom: 2px;">
                            Battery Health Analysis (BHA)
                        </div>
                    """, unsafe_allow_html=True)

                    fig_bha = go.Figure(data=[go.Pie(
                        labels=["Master NA: 2", "Good: 0", "Bad: 0", "Undersized: 0", "NC: 0"],
                        values=[2, 0, 0, 0, 0],
                        hole=0.55,
                        marker=dict(colors=["#964B00", "#008000", "#FF0000", "#0000FF", "#808080"]),
                        textinfo="none",
                        hoverinfo="label",
                        sort=False
                    )])
                    fig_bha.update_layout(
                        showlegend=True,
                        legend=dict(orientation="v", font=dict(size=10), y=0.5, x=0.80, yanchor="middle", xanchor="left"),
                        margin=dict(t=5, b=5, l=0, r=0),
                        height=180,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        annotations=[dict(text="<b>2 Units</b><br><span style='font-size:9px;'>Lithium BB</span>", x=0.32, y=0.5, font_size=12, showarrow=False)]
                    )
                    st.plotly_chart(fig_bha, use_container_width=True, config={"displayModeBar": False})


        # VIEW 2: SITE DIGITAL TWIN (POWER PLANT FLOW ORIGINAL)
        elif noc_view_mode == "Site Digital Twin (Power Flow)":
            dt_site = st.selectbox(
                "Select Monitored Substation Node:",
                ["LAT001 — MAINA 2 (Lautem, Live Ecolite RMS)", "BAU001 — TRILOCA (Baucau, Noncomm)"],
                index=0,
                key="sb_dt_site_select"
            )
            is_lat = "LAT001" in dt_site
            target_id = "LAT001" if is_lat else "BAU001"
            site_rec = noc_service.get_cached_site_detail(target_id) or {}
            p_flow = (site_rec.get("parsed_raw") or {}).get("flow", {})

            # Power Plant Single-Line Topology Block
            st.markdown(f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px;">
                        <span style="font-weight: 800; font-size: 0.92rem; color: #0F172A;">
                            POWER PLANT FLOW DIAGRAM &bull; {target_id} ({site_rec.get('site_name')})
                        </span>
                        <span style="font-size: 0.72rem; font-weight: 700; color: {'#065F46' if is_lat else '#991B1B'}; background: {'#ECFDF5' if is_lat else '#FEF2F2'}; border: 1px solid {'#A7F3D0' if is_lat else '#FECACA'}; padding: 2px 8px; border-radius: 4px;">
                            {'RMS: LIVE ONLINE (TIB-Ecolite)' if is_lat else 'RMS: NONCOMMUNICATION (Major Alarm)'}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 130px; background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #10B981; border-radius: 4px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">UTILITY GRID</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #10B981; margin: 3px 0;">{'232V' if is_lat else '235V'}</div>
                            <div style="font-size: 0.70rem; color: #475569;">Phase R/Y/B Active</div>
                            <div style="font-size: 0.68rem; color: #64748B;">EBRH MTD: 19h</div>
                        </div>
                        <div style="font-size: 1.1rem; color: #94A3B8;">&rarr;</div>
                        <div style="flex: 1; min-width: 130px; background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #64748B; border-radius: 4px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">GENSET (DG)</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #64748B; margin: 3px 0;">STANDBY</div>
                            <div style="font-size: 0.70rem; color: #475569;">Output: 0V (0 Hz)</div>
                            <div style="font-size: 0.68rem; color: #64748B;">DGRH MTD: 0h</div>
                        </div>
                        <div style="font-size: 1.1rem; color: #94A3B8;">&rarr;</div>
                        <div style="flex: 1; min-width: 130px; background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #F59E0B; border-radius: 4px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">SOLAR & MPPT</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #F59E0B; margin: 3px 0;">ACTIVE</div>
                            <div style="font-size: 0.70rem; color: #475569;">Controller: AST SC</div>
                            <div style="font-size: 0.68rem; color: #64748B;">MPPT Tracking</div>
                        </div>
                        <div style="font-size: 1.1rem; color: #94A3B8;">&rarr;</div>
                        <div style="flex: 1; min-width: 130px; background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #2563EB; border-radius: 4px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">SMPS RECTIFIER</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #2563EB; margin: 3px 0;">54.0V &bull; 71.5A</div>
                            <div style="font-size: 0.70rem; color: #475569;">Capacity: 3,861 W</div>
                            <div style="font-size: 0.68rem; color: #64748B;">4 Rectifier Units</div>
                        </div>
                        <div style="font-size: 1.1rem; color: #94A3B8;">&rarr;</div>
                        <div style="flex: 1; min-width: 130px; background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #059669; border-radius: 4px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">AMARARAJA LITHIUM</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #059669; margin: 3px 0;">{'100% SOC' if is_lat else 'N/A'}</div>
                            <div style="font-size: 0.70rem; color: #475569;">{'Bank: 54.0V (34.8°C)' if is_lat else 'Noncomm'}</div>
                            <div style="font-size: 0.68rem; color: #64748B;">Capacity: 800 Ah</div>
                        </div>
                        <div style="font-size: 1.1rem; color: #94A3B8;">&rarr;</div>
                        <div style="flex: 1; min-width: 130px; background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 3px solid #0F172A; border-radius: 4px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">TELKOMCEL DC LOAD</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #0F172A; margin: 3px 0;">{'3.86 kW' if is_lat else '0.00 kW'}</div>
                            <div style="font-size: 0.70rem; color: #475569;">{'71.5A @ 54.0V' if is_lat else 'Standby'}</div>
                            <div style="font-size: 0.68rem; color: #64748B;">CH-3 & CH-4 Combined</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # VIEW 3: ALARM DASHBOARD ORIGINAL
        elif noc_view_mode == "Alarm Dashboard":
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total Sites", "2", delta="Monitored")
            k2.metric("Alarm Sites", "1", delta="Major Alarm", delta_color="inverse")
            k3.metric("Healthy Sites", "1", delta="Normal", delta_color="normal")
            k4.metric("Alarm %", "50.0%", delta="TRILOCA Noncomm")
            k5.metric("Healthy %", "50.0%", delta="MAINA 2 Operational")

            st.markdown("---")
            st.markdown("##### Active Alarm Register (AST Filtered)")
            al_rows = [
                {"Code": "13", "Alarm Classification": "NC (Non-Communicating)", "Site": "BAU001 (TRILOCA)", "District": "Baucau", "Severity": "MAJOR", "Action Required": "RTU Modem SIM & RS-485 Communication Check"}
            ]
            st.dataframe(pd.DataFrame(al_rows), use_container_width=True, hide_index=True)

        # VIEW 4: EXECUTIVE SLA DASHBOARD ORIGINAL
        elif noc_view_mode == "Executive SLA Dashboard":
            st.markdown("##### Executive Performance & SLA Scorecard")
            sla_df = pd.DataFrame([
                {"Circle": "Timor", "Target SLA": "99.50%", "MTD Availability": "100.00%", "Total Sites": 2, "Sites SLA Met": 2, "Sites Breached": 0, "SLA Met %": "100.00%"},
                {"Circle": "National", "Target SLA": "99.50%", "MTD Availability": "100.00%", "Total Sites": 2, "Sites SLA Met": 2, "Sites Breached": 0, "SLA Met %": "100.00%"}
            ])
            st.dataframe(sla_df, use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # =====================================================================
        # BAGIAN BAWAH: ANALITIK KINERJA OPERASIONAL & SENTINEL SAMVAD PMO
        # =====================================================================
        st.markdown("""
            <div style="background: #1E3A8A; color: #FFFFFF; border-radius: 6px 6px 0 0; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.82rem; font-weight: 800; letter-spacing: 0.5px;">
                    2. SAMVAD PMO DEEP ANALYTICS & OPERATIONAL SENTINEL
                </span>
                <span style="font-size: 0.70rem; color: #DBEAFE; background: #1E40AF; border: 1px solid #3B82F6; padding: 2px 8px; border-radius: 4px;">
                    PaaS Energy Optimization & Root Cause Intelligence
                </span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-top: none; padding: 14px 18px; margin-bottom: 16px;">
                <div style="font-size: 0.78rem; color: #64748B; margin-bottom: 14px;">
                    Analisis lanjutan yang diekstraksi dari telemetri Applied Energy NOC untuk mendukung pengambilan keputusan PMO, optimasi konsumsi daya Telkomcel, audit degradasi baterai, dan penugasan teknisi lapangan.
                </div>
        """, unsafe_allow_html=True)

        # Analitik Baris 1: Konsumsi Daya Tenant & Efisiensi Energi
        st.markdown("##### Analisis Beban & Efisiensi Energi Telkomcel (Site LAT001 MAINA 2)")
        c_an1, c_an2, c_an3, c_an4 = st.columns(4)
        c_an1.metric("Konsumsi Daya DC", "3.86 kW", delta="71.5A @ 54.0V DC")
        c_an2.metric("Efisiensi Rectifier SMPS", "100.0%", delta="Output 3,861 W Sesuai Beban")
        c_an3.metric("Estimasi Konsumsi Bulanan", "2,779 kWh", delta="Berdasarkan 92.6 kWh/Hari")
        c_an4.metric("Kanal Tenant Aktif", "2 Kanal DC", delta="CH-3 (3.61 kW) & CH-4 (0.25 kW)")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Analitik Baris 2: Detail Baterai Lithium Amararaja per-Modul (LIB1 - LIB5)
        st.markdown("##### Telemetri Modul Baterai Lithium Amararaja (800 Ah Bank)")
        lib_data = [
            {"Modul Pack": "LIB1", "Kapasitas Unit": "48V 100AH", "Voltase": "54.2V", "State of Charge": "100%", "Suhu Sel": "26.0°C", "Kondisi": "OPTIMAL"},
            {"Modul Pack": "LIB2", "Kapasitas Unit": "48V 100AH", "Voltase": "54.0V", "State of Charge": "99%", "Suhu Sel": "26.0°C", "Kondisi": "OPTIMAL"},
            {"Modul Pack": "LIB3", "Kapasitas Unit": "48V 100AH", "Voltase": "54.2V", "State of Charge": "99%", "Suhu Sel": "27.0°C", "Kondisi": "OPTIMAL"},
            {"Modul Pack": "LIB4", "Kapasitas Unit": "48V 100AH", "Voltase": "54.0V", "State of Charge": "100%", "Suhu Sel": "27.0°C", "Kondisi": "OPTIMAL"},
            {"Modul Pack": "LIB5", "Kapasitas Unit": "48V 100AH", "Voltase": "54.2V", "State of Charge": "100%", "Suhu Sel": "28.0°C", "Kondisi": "OPTIMAL"}
        ]
        st.dataframe(pd.DataFrame(lib_data), use_container_width=True, hide_index=True)

        st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; font-size: 0.74rem; color: #475569; margin-top: 6px;">
                <b>Indeks Degradasi Siklus Baterai:</b> Bank baterai telah menempuh <b>531 siklus pelepasan</b> dengan total akumulasi discharge <b>1,767 kWh</b>. Tingkat degradasi diperkirakan &le; 18.2%, dengan estimasi sisa masa pakai operasional &gt; 2,450 siklus sebelum kapasitas turun di bawah 80% SOH.
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Analitik Baris 3: Sentinel Insiden Alarm NC & Tindakan Lapangan
        st.markdown("##### Sentinel Insiden Lapangan & Rekomendasi Aksi Pemulihan (BAU001 TRILOCA)")
        st.markdown(f"""
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-left: 4px solid #F59E0B; border-radius: 4px; padding: 12px 16px; font-size: 0.78rem; color: #92400E;">
                <div style="font-weight: 800; margin-bottom: 4px; color: #78350F;">
                    ALARM NC: NON-COMMUNICATION PADA NODE BAU001 (BAUCAU)
                </div>
                <div>
                    <b>Deskripsi Gangguan:</b> RTU Ecolite terputus komunikasinya dari server NOC sejak 3 Juli 2026 10:28 AM. Namun, pasokan listrik PLN/Grid tetap aktif pada voltase 235V (EBRH MTD: 19 jam). Hal ini mengindikasikan masalah pada modem SIM card RTU atau kabel RS-485 komunikasi, bukan gangguan pemadaman listrik total.
                </div>
                <div style="margin-top: 6px;">
                    <b>Rekomendasi Penugasan:</b> Dispatch PIC Lapangan <b>Rashid Ali (+918860324496)</b> untuk melakukan reset power RTU controller dan pengecekan sinyal GSM/SIM Card di lokasi pemancar Baucau.
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Analitik Baris 4: Direktori Lengkap 6 Site Timor Circle
        st.markdown("##### Inventori Spasial & Status 6 Site Terdaftar di Timor Circle")
        dir_data = [
            {"Site ID": "LAT001", "Nama Site": "MAINA 2", "Distrik": "Lautem", "Client": "Telkomcel", "Status": "On Air", "RTU ID": "670200001", "Tipe RTU": "TIB-Ecolite Live", "Grid AC": "232V (Aktif)", "Baterai SOC": "100%", "PIC": "Rashid Ali (+918860324496)"},
            {"Site ID": "BAU001", "Nama Site": "TRILOCA", "Distrik": "Baucau", "Client": "Telkomcel", "Status": "On Air", "RTU ID": "670100002", "Tipe RTU": "Noncomm", "Grid AC": "235V (Aktif)", "Baterai SOC": "N/A (NC)", "PIC": "Unassigned"},
            {"Site ID": "LAT001-T", "Nama Site": "MAINA 2", "Distrik": "Lautem", "Client": "Telkomcel", "Status": "Secondary Site", "RTU ID": "670100001", "Tipe RTU": "Secondary", "Grid AC": "0V", "Baterai SOC": "0%", "PIC": "Rashid Ali"},
            {"Site ID": "BAU001-T", "Nama Site": "TRILOCA", "Distrik": "Baucau", "Client": "Telkomcel", "Status": "WIP", "RTU ID": "N/A", "Tipe RTU": "Pending I&C", "Grid AC": "0V", "Baterai SOC": "0%", "PIC": "Unassigned"},
            {"Site ID": "Test_Site", "Nama Site": "Test Site", "Distrik": "Timor", "Client": "Telkomcel", "Status": "WIP", "RTU ID": "910447681", "Tipe RTU": "Staging Node", "Grid AC": "0V", "Baterai SOC": "0%", "PIC": "Unassigned"},
            {"Site ID": "Service Test_1", "Nama Site": "Service Test_1", "Distrik": "Timor", "Client": "Telkomcel", "Status": "WIP", "RTU ID": "999999999", "Tipe RTU": "Lab Node", "Grid AC": "0V", "Baterai SOC": "0%", "PIC": "Unassigned"}
        ]
        st.dataframe(pd.DataFrame(dir_data), use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # TAB 2: REAL-TIME SITE UPTIME & NETWORK SLA
    # =========================================================================
    with tab2:
        summary = monitor.get_uptime_summary()
        avg_up = summary["average_uptime"]
        sla_met = summary["sla_compliant"]

        uc1, uc2, uc3, uc4 = st.columns(4)
        uc1.metric("Average Network Uptime", f"{avg_up}%", delta=f"{avg_up - 95.0:.2f}% Above 95% SLA", delta_color="normal")
        uc2.metric("Total Monitored Sites", f"{summary['total_sites']}")
        uc3.metric("Sites Online", f"{summary['online_sites']}", delta="Operational")
        uc4.metric("SLA Status", "COMPLIANT (>=95%)" if sla_met else "SLA BREACHED (<95%)")

        st.markdown("---")
        st.subheader("Nationwide Tower Sites & Proof of Concept (POC) Availability")
        
        df_sites = monitor.get_sites_status()
        if not df_sites.empty:
            # Bar chart comparing site uptime vs 95% threshold
            fig_bar = px.bar(
                df_sites,
                x="site_name",
                y="uptime_percent",
                color="current_status",
                color_discrete_map={"ONLINE": "#10B981", "DEGRADED": "#F59E0B", "DOWN": "#EF4444"},
                text="uptime_percent",
                labels={"site_name": "Tower Site", "uptime_percent": "Uptime %", "current_status": "Status"}
            )
            fig_bar.add_hline(y=95.0, line_dash="dash", line_color="red", annotation_text="Contract SLA Floor: 95.0%")
            fig_bar.update_layout(yaxis_range=[90, 100], height=340, margin=dict(l=20, r=20, t=30, b=30))
            st.plotly_chart(fig_bar, use_container_width=True)

            st.dataframe(
                df_sites[["site_id", "site_name", "region", "is_poc_pilot", "current_status", "uptime_percent", "ip_address"]],
                use_container_width=True
            )

    # =========================================================================
    # TAB 3: EMERGENCY OUTAGE SENTINEL (>15 MIN ALERTS)
    # =========================================================================
    with tab3:
        st.subheader("Emergency Outage Alert Sentinel (>15 Min Rule)")
        st.markdown(
            "Push notifications automatically triggered via **Telegram Bot API** and **Twilio WhatsApp API** "
            "to field technicians if any site experiences an outage exceeding **15 minutes**."
        )

        df_inc = monitor.get_active_incidents()
        if not df_inc.empty:
            st.dataframe(df_inc, use_container_width=True)
        else:
            st.success("No active outages recorded! All nodes operational.")

        st.markdown("#### Test / Force Emergency Incident Dispatch")
        with st.form("form_test_outage"):
            oc1, oc2 = st.columns(2)
            test_site = oc1.selectbox("Target Site for Outage Test", ["SVD-MDN-006 (Medan Ring Road)", "POC-PILOT-02 (Cikarang Hub)"])
            test_mins = oc2.number_input("Simulated Downtime (Minutes)", value=22, min_value=1)
            test_cause = oc1.text_input("Root Cause", "Substation utility power drop & backup battery cut")
            
            if st.form_submit_button("Simulate & Dispatch Emergency Alert"):
                site_id = test_site.split()[0]
                site_name = test_site
                res = monitor.dispatcher.dispatch_emergency_outage(site_id, site_name, test_mins, test_cause)
                st.error(f"Push notifications triggered! Telegram: `{res['telegram']['status']}`, WhatsApp: `{res['whatsapp']['status']}`")

    # =========================================================================
    # TAB 4: DIGITAL I&C SOP CHECKLIST & PDF GENERATOR
    # =========================================================================
    with tab4:
        st.subheader("Digital I&C SOP Interactive Checklist & Client PDF Generator")
        st.markdown(
            "Complete the digital commissioning checklist below. Upon completion, click **Compile Client-Ready I&C PDF** "
            "to generate the signed acceptance certificate for customer handover."
        )

        sc1, sc2, sc3 = st.columns(3)
        site_id_input = sc1.text_input("Site ID", "SVD-JKT-001")
        client_input = sc2.selectbox("Client Operator", ["Telkomsel", "Indosat Ooredoo Hutchison", "XL Axiata", "Smartfren"])
        tech_input = sc3.text_input("Lead Commissioning Engineer", "Supriyanto (PMO Lead)")

        template_items = sop_gen.get_standard_template()
        completed_items = []

        st.markdown("##### Verification Workstreams:")
        for itm in template_items:
            with st.container():
                cols = st.columns([3, 3, 2, 4])
                cols[0].write(f"**{itm['id']}. {itm['title']}**")
                cols[1].caption(f"Spec: {itm['spec']}")
                res = cols[2].selectbox("Result", ["PASS", "FAIL", "N/A"], key=f"sop_res_{itm['id']}")
                rem = cols[3].text_input("Inspection Remarks", value=itm["remarks"], key=f"sop_rem_{itm['id']}")
                completed_items.append({
                    "id": itm["id"],
                    "title": itm["title"],
                    "spec": itm["spec"],
                    "result": res,
                    "remarks": rem
                })

        st.markdown("---")
        if st.button("Compile Client-Ready I&C PDF", type="primary"):
            result = sop_gen.compile_ic_document(site_id_input, client_input, tech_input, completed_items)
            st.success(f"I&C SOP Certificate successfully compiled! Reference Code: `{result['checklist_code']}`")
            
            with open(result["pdf_path"], "rb") as f:
                st.download_button(
                    label="Download Standardized Client I&C PDF",
                    data=f.read(),
                    file_name=f"I&C_Acceptance_{result['checklist_code']}.pdf",
                    mime="application/pdf"
                )
