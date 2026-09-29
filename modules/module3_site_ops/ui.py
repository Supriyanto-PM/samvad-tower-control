"""
UI View for Module 3: Site Availability & SLA Operations (KPI Category C — 25% Weight).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.module3_site_ops.uptime_monitor import UptimeMonitor
from modules.module3_site_ops.sop_generator import SOPGenerator

def render_module3():
    st.markdown("## 📡 Module 3: Site Availability & SLA Operations")
    st.caption("KPI Category C — 25% Weight | Target: Maintain Site Availability >= 95.0% Mandatory Threshold & Standardized I&C SOPs")

    monitor = UptimeMonitor()
    sop_gen = SOPGenerator()

    tab1, tab2, tab3 = st.tabs([
        "📶 Real-time Site Uptime & Network SLA",
        "🚨 Emergency Outage Sentinel (>15 Min Alerts)",
        "📋 Digital I&C SOP Checklist & PDF Generator"
    ])

    with tab1:
        summary = monitor.get_uptime_summary()
        avg_up = summary["average_uptime"]
        sla_met = summary["sla_compliant"]

        uc1, uc2, uc3, uc4 = st.columns(4)
        uc1.metric("Average Network Uptime", f"{avg_up}%", delta=f"{avg_up - 95.0:.2f}% Above 95% SLA", delta_color="normal")
        uc2.metric("Total Monitored Sites", f"{summary['total_sites']}")
        uc3.metric("Sites Online", f"{summary['online_sites']}", delta="Operational")
        uc4.metric("SLA Status", "✅ COMPLIANT (>=95%)" if sla_met else "⚠️ SLA BREACHED (<95%)")

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

    with tab2:
        st.subheader("🚨 Emergency Outage Alert Sentinel (>15 Min Rule)")
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
                st.error(f"🚨 Push notifications triggered! Telegram: `{res['telegram']['status']}`, WhatsApp: `{res['whatsapp']['status']}`")

    with tab3:
        st.subheader("📋 Digital I&C SOP Interactive Checklist & Client PDF Generator")
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
        if st.button("📄 Compile Client-Ready I&C PDF", type="primary"):
            result = sop_gen.compile_ic_document(site_id_input, client_input, tech_input, completed_items)
            st.success(f"I&C SOP Certificate successfully compiled! Reference Code: `{result['checklist_code']}`")
            
            with open(result["pdf_path"], "rb") as f:
                st.download_button(
                    label="⬇️ Download Standardized Client I&C PDF",
                    data=f.read(),
                    file_name=f"I&C_Acceptance_{result['checklist_code']}.pdf",
                    mime="application/pdf"
                )
