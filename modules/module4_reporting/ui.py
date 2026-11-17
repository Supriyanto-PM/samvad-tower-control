"""
UI View for Module 4: SLA Reporting & Presales Engine (KPI Category D — 25% Weight).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from modules.module4_reporting.auto_reporter import FridayAutoReporter
from modules.module4_reporting.poc_tracker import POCTracker

def render_module4():
    st.markdown("## Module 4: SLA Reporting & Presales Engine")
    st.caption("KPI Category D — 25% Weight | Target: 100% On-Time Weekly Reports by Friday 17:00 WIB & 5-Days Ahead POC Deliveries")

    reporter = FridayAutoReporter()
    poc_tracker = POCTracker()

    tab1, tab2, tab3 = st.tabs([
        "Friday 14:00 Auto-Reporter & Export Center",
        "POC Gantt & 5-Days Ahead Milestone Tracker",
        "Register Presales POC Milestone"
    ])

    with tab1:
        st.subheader("Friday 14:00 WIB Automated SLA Status Reporter")
        st.info(
            "**Automated Extraction Protocol:** Consolidates live operational performance data from "
            "**Module 1 (Customs)**, **Module 2 (SG&A & Financials)**, and **Module 3 (Site Operations)** "
            "every Friday at **14:00 WIB**, ensuring full compliance with the strict **17:00 WIB contract deadline**."
        )

        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Automated Trigger Time", "Friday 14:00 WIB", delta="Active Schedule")
        rc2.metric("Contract SLA Deadline", "Friday 17:00 WIB", delta="3-Hour Buffer")
        rc3.metric("Historical Delivery SLA", "100.0% On-Time", delta="Zero Penalties")

        st.markdown("---")
        st.markdown("#### Trigger & Compile Current Week's PMO Report Bundle")
        
        col_run, col_week = st.columns([2, 1])
        with col_week:
            target_week = st.number_input("Reporting Week Number", value=36, min_value=1, max_value=53)
        
        with col_run:
            st.write("")
            st.write("")
            if st.button("Execute Friday 14:00 Auto-Run & Compile Bundle (PDF, Word, Excel)", type="primary"):
                with st.spinner("Aggregating multidisciplinary modules and compiling executive files..."):
                    bundle = reporter.generate_friday_weekly_bundle(week_num=target_week)
                    st.success(f"Report Bundle `{bundle['report_code']}` successfully compiled! Compliance: {bundle['compliance_status']}")
                    
                    st.markdown("##### Executive Deliverables for President Director & Clients:")
                    dcol1, dcol2, dcol3 = st.columns(3)

                    # PDF
                    with open(bundle["pdf_path"], "rb") as f_pdf:
                        dcol1.download_button(
                            "Download PDF Status Report",
                            data=f_pdf.read(),
                            file_name=f"Samvad_PMO_Weekly_Report_W{target_week}.pdf",
                            mime="application/pdf"
                        )

                    # Word
                    with open(bundle["docx_path"], "rb") as f_docx:
                        dcol2.download_button(
                            "Download Word Briefing (.docx)",
                            data=f_docx.read(),
                            file_name=f"Samvad_PMO_Briefing_W{target_week}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

                    # Excel
                    with open(bundle["xlsx_path"], "rb") as f_xlsx:
                        dcol3.download_button(
                            "Download Multi-Sheet Excel (.xlsx)",
                            data=f_xlsx.read(),
                            file_name=f"Samvad_PMO_Audit_W{target_week}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

        st.markdown("---")
        st.subheader("Historical SLA Report Submissions")
        df_hist = reporter.get_report_history()
        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.write("No prior report archives.")

    with tab2:
        st.subheader("POC Gantt Timeline & '5-Days Ahead' Stretch Performance")
        st.markdown(
            "Traces technical presentations and pilot setups against the contract's **'5-days ahead' stretch target**. "
            "Milestones achieving completion 5 days ahead receive a 120% KPI bonus multiplier."
        )

        df_poc = poc_tracker.get_all_poc_milestones()
        if not df_poc.empty:
            # Interactive Timeline Gantt Chart
            # Prepare start and finish for Gantt
            df_gantt = df_poc.copy()
            # Start date proxy: created_at or 15 days before target
            df_gantt["Start"] = pd.to_datetime(df_gantt["target_deadline"]) - pd.to_timedelta(14, unit='d')
            df_gantt["Finish"] = pd.to_datetime(df_gantt["target_deadline"])
            df_gantt["Milestone"] = df_gantt["client_name"] + ": " + df_gantt["milestone_name"]

            fig_gantt = px.timeline(
                df_gantt,
                x_start="Start",
                x_end="Finish",
                y="Milestone",
                color="stretch_status_evaluated",
                title="Presales POC Execution Timeline & Milestone Buffers",
                color_discrete_map={
                    "5-Day Ahead Stretch Met": "#10B981",
                    "Ahead / On Pace for Stretch": "#3B82F6",
                    "Standard Pace (Stretch at Risk)": "#F59E0B",
                    "Lagging Behind Contract Target": "#EF4444"
                }
            )
            fig_gantt.update_yaxes(autorange="reversed")
            fig_gantt.update_layout(height=340, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gantt, use_container_width=True)

            st.dataframe(
                df_poc[[
                    "poc_code", "client_name", "milestone_name", "target_deadline",
                    "stretch_target_deadline", "stretch_status_evaluated", "status", "lead_presales_engineer"
                ]],
                use_container_width=True
            )

    with tab3:
        st.subheader("Register New Presales POC Milestone")
        with st.form("form_new_poc"):
            pc1, pc2 = st.columns(2)
            poc_code = pc1.text_input("POC Code (e.g. POC-2026-CLIENT-04)")
            client_name = pc2.selectbox("Client Operator", ["Telkomsel", "Indosat Ooredoo Hutchison", "XL Axiata", "Smartfren", "Private Enterprise"])
            scope = pc1.text_input("POC Scope / Objective", "Private 5G Factory Automation Pilot")
            engineer = pc2.text_input("Lead Presales Engineer", "Supriyanto")
            milestone = pc1.text_input("Milestone Title", "Phase 1: Spectrum & Hardware Staging")
            deadline = pc2.date_input("Target Contract Deadline", value=date.today() + timedelta(days=20))
            notes = pc1.text_area("Milestone Notes", "Key client demonstration planned.")

            if st.form_submit_button("Register POC Milestone"):
                if poc_code and milestone:
                    poc_tracker.add_poc_milestone({
                        "poc_code": poc_code,
                        "client_name": client_name,
                        "poc_scope": scope,
                        "lead_presales_engineer": engineer,
                        "milestone_name": milestone,
                        "target_deadline": deadline.isoformat(),
                        "notes": notes
                    })
                    st.success(f"POC Milestone `{poc_code}` registered with auto-calculated 5-day stretch target!")
                    st.rerun()
                else:
                    st.error("Please fill in POC code and milestone name.")
