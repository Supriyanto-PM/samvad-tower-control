"""
UI View for Module 1: Supply Chain & Customs Guardian (KPI Category A — 25% Weight).
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from modules.module1_customs.tracker import CustomsTracker
from modules.module1_customs.competitor_hub import CompetitorHub
from services.notification_service import NotificationDispatcher

def render_module1():
    st.markdown("## 🚢 Module 1: Supply Chain & Customs Guardian")
    st.caption("KPI Category A — 25% Weight | Target: 0% Logistics Delays & Robust Supplier Pricing Database")

    tracker = CustomsTracker()
    hub = CompetitorHub()
    dispatcher = NotificationDispatcher()

    tab1, tab2, tab3 = st.tabs(["📦 Customs Milestone Tracker & SLA Alerts", "💡 Competitor Intelligence Hub", "➕ Register New Shipment / Quote"])

    with tab1:
        df_shipments = tracker.get_all_shipments()
        
        # Summary KPI cards
        col1, col2, col3, col4 = st.columns(4)
        total_ship = len(df_shipments)
        green_cnt = len(df_shipments[df_shipments["calculated_delay_risk"] == "GREEN"]) if not df_shipments.empty else 0
        yellow_cnt = len(df_shipments[df_shipments["calculated_delay_risk"] == "YELLOW"]) if not df_shipments.empty else 0
        red_cnt = len(df_shipments[df_shipments["calculated_delay_risk"] == "RED"]) if not df_shipments.empty else 0

        col1.metric("Total Active Shipments", f"{total_ship} B/Ls")
        col2.metric("Healthy Buffer (Green)", f"{green_cnt}", delta="On Track")
        col3.metric("Watch List (Yellow)", f"{yellow_cnt}", delta="-5 Days Buffer", delta_color="normal")
        col4.metric("Critical Delay Risk (Red)", f"{red_cnt}", delta="Action Required", delta_color="inverse")

        st.markdown("---")
        st.subheader("Active International B/L Milestone Status")

        if not df_shipments.empty:
            for _, row in df_shipments.iterrows():
                risk = row["calculated_delay_risk"]
                badge_color = "🟢" if risk == "GREEN" else ("🟡" if risk == "YELLOW" else "🔴")
                
                with st.expander(f"{badge_color} B/L: **{row['bl_number']}** — {row['item_description']} ({row['vendor_name']})"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Origin Port:** {row['port_of_origin']}")
                    c1.write(f"**Destination Port:** {row['destination_port']}")
                    c1.write(f"**Carrier:** {row['ocean_freight_carrier']}")

                    c2.write(f"**ETD:** {row['etd']}")
                    c2.write(f"**ETA Port:** {row['eta']}")
                    c2.write(f"**Commissioning Deadline:** {row['project_commissioning_deadline']}")

                    c3.write(f"**Current Milestone:** `{row['current_milestone']}`")
                    c3.write(f"**Customs Channel:** `{row['customs_channel']}`")
                    c3.markdown(f"**Remaining Buffer:** `{row['buffer_days']} Days`")

                    st.info(f"**Operational PMO Notes:** {row['notes']}")

                    # Action buttons
                    bcol1, bcol2 = st.columns([1, 4])
                    if risk == "RED":
                        if bcol1.button("🚨 Trigger Customs Push Alert", key=f"btn_alert_{row['bl_number']}"):
                            res = dispatcher.dispatch_customs_warning(
                                row["bl_number"],
                                row["item_description"],
                                row["eta"],
                                row["project_commissioning_deadline"],
                                row["buffer_days"]
                            )
                            st.success(f"Customs alert sent via Telegram! Status: {res.get('status')}")
        else:
            st.info("No active shipments logged.")

    with tab2:
        st.subheader("Competitor Pricing & Supplier Cost Pushback Hub")
        df_comp = hub.get_all_intelligence()

        # Pushback Calculator Sandbox
        st.markdown("#### 🧮 Interactive Supplier Cost Pushback Calculator")
        pcol1, pcol2, pcol3 = st.columns(3)
        vendor_quote = pcol1.number_input("Vendor Quoted Price (USD)", value=14500.0, step=100.0)
        comp_benchmark = pcol2.number_input("Competitor / Target Benchmark (USD)", value=12800.0, step=100.0)
        quantity = pcol3.number_input("Procurement Volume (Units)", value=25, step=1)

        pushback_result = hub.calculate_cost_pushback_matrix(vendor_quote, comp_benchmark, quantity)
        
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Unit Cost Delta", f"${pushback_result['unit_delta_usd']:,.2f}", f"{pushback_result['delta_percentage']}% Variance")
        mcol2.metric("Total Negotiation Savings", f"${pushback_result['total_savings_usd']:,.2f}", delta="Potential Margin Gain")
        mcol3.metric("Negotiation Posture", pushback_result['negotiation_posture'])

        st.warning(f"**PMO Lead Tactical Talking Point:** {pushback_result['recommended_strategy']}")

        st.markdown("---")
        st.subheader("Historical Competitor Intelligence Database")
        if not df_comp.empty:
            st.dataframe(
                df_comp[[
                    "competitor_name", "product_category", "model_or_part_number", 
                    "quoted_unit_price_usd", "samvad_target_price_usd", "potential_pushback_pct", 
                    "quote_date", "source_reference"
                ]],
                use_container_width=True
            )
        else:
            st.info("No competitor quotes recorded yet.")

    with tab3:
        st.subheader("➕ Register New B/L Shipment")
        with st.form("form_new_shipment"):
            fc1, fc2 = st.columns(2)
            bl_num = fc1.text_input("B/L Number (e.g., BL-SVD-2026-0920)")
            vendor = fc2.text_input("Supplier / Vendor Name", "Huawei Technologies Co.")
            desc = fc1.text_input("Item Description", "5G RRU & Antenna Subsystem")
            origin = fc2.text_input("Port of Origin", "Shenzhen, China")
            dest = fc1.text_input("Destination Port", "Tanjung Priok, Jakarta")
            carrier = fc2.text_input("Ocean Carrier", "Maersk Line")
            
            etd_val = fc1.date_input("ETD Port of Origin", value=date.today())
            eta_val = fc2.date_input("ETA Destination Port", value=date.today() + timedelta(days=14))
            deadline_val = fc1.date_input("Project Commissioning Deadline", value=date.today() + timedelta(days=25))
            notes_val = fc2.text_area("Logistics Notes / Channel Risk", "Normal customs clearance anticipated.")

            submit_shipment = st.form_submit_button("Register Shipment")
            if submit_shipment:
                if bl_num and desc:
                    tracker.add_shipment({
                        "bl_number": bl_num,
                        "vendor_name": vendor,
                        "item_description": desc,
                        "port_of_origin": origin,
                        "destination_port": dest,
                        "ocean_freight_carrier": carrier,
                        "etd": etd_val.isoformat(),
                        "eta": eta_val.isoformat(),
                        "project_commissioning_deadline": deadline_val.isoformat(),
                        "notes": notes_val
                    })
                    st.success(f"Shipment {bl_num} registered successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in B/L Number and Description.")
