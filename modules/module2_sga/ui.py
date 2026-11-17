"""
UI View for Module 2: SG&A & Manpower Financial Sentinel (KPI Category B — 25% Weight).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from modules.module2_sga.sga_calculator import SGACalculator
from modules.module2_sga.manpower_optimizer import ManpowerOptimizer
from modules.module2_sga.margin_optimizer import ClientMarginOptimizer

def render_module2():
    st.markdown("## Module 2: SG&A & Manpower Financial Sentinel")
    st.caption("KPI Category B — 25% Weight | Target: Maintain Year 1 Project SG&A < 12.0% & Optimize Manpower Cost Structures")

    sga_calc = SGACalculator()
    manpower_opt = ManpowerOptimizer()
    margin_opt = ClientMarginOptimizer()

    tab1, tab2, tab3, tab4 = st.tabs([
        "SG&A Ratio & Budget Sentinel",
        "Manpower Cost Optimizer",
        "Client Margin Initiatives",
        "Log New Expense / Visit"
    ])

    with tab1:
        summary = sga_calc.get_expenses_summary()
        ratio = summary["sga_ratio_pct"]
        ceiling = summary["sga_ceiling_pct"]

        # Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=ratio,
            number={'suffix': "%", 'font': {'size': 36}},
            delta={'reference': ceiling, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge={
                'axis': {'range': [0, 20], 'ticksuffix': "%"},
                'bar': {'color': "#10B981" if ratio < 10 else ("#F59E0B" if ratio <= 12 else "#EF4444")},
                'steps': [
                    {'range': [0, 10], 'color': '#ECFDF5'},
                    {'range': [10, 12], 'color': '#FFFBEB'},
                    {'range': [12, 20], 'color': '#FEF2F2'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 12.0
                }
            },
            title={'text': "Current Cumulative SG&A Ratio (Max 12.0% Ceiling)"}
        ))
        fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=10))

        c1, c2 = st.columns([1, 1])
        with c1:
            st.plotly_chart(fig_gauge, use_container_width=True)
        with c2:
            st.markdown(f"### Status: `{summary['status']}`")
            st.write(summary['status_desc'])
            st.metric("Total SG&A Spend", f"IDR {summary['total_spent_idr']:,.0f}")
            st.metric("Allocated Budget", f"IDR {summary['allocated_sga_budget_idr']:,.0f}")
            st.metric("Remaining Buffer", f"IDR {summary['remaining_budget_idr']:,.0f}", delta=f"{12.0 - ratio:.2f}% Margin Under Ceiling")

        st.markdown("---")
        st.subheader("SG&A Spend Distribution by Category")
        cat_data = summary["category_breakdown"]
        if cat_data:
            df_cat = pd.DataFrame(list(cat_data.items()), columns=["Category", "Amount_IDR"])
            fig_pie = px.pie(df_cat, names="Category", values="Amount_IDR", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10))
            
            pcol1, pcol2 = st.columns([1, 1])
            with pcol1:
                st.plotly_chart(fig_pie, use_container_width=True)
            with pcol2:
                st.dataframe(df_cat.style.format({"Amount_IDR": "IDR {:,.0f}"}), use_container_width=True)

        st.subheader("Recent SG&A Expense Transactions")
        st.dataframe(summary["expenses_df"], use_container_width=True)

    with tab2:
        st.subheader("Field Engineer Utilization & Retainer Cost Optimizer")
        st.markdown(
            "Automated audit tracker that cross-references field engineer visits with daily rates. "
            "Engineers whose daily rate spend exceeds fixed retainer are flagged for **immediate contract package conversion**."
        )

        df_audit = manpower_opt.audit_engineer_utilization()
        if not df_audit.empty:
            total_savings = df_audit["potential_saving_idr"].sum()
            st.success(f"**Total Identified Optimization Savings:** **IDR {total_savings:,.0f} / month** through retainer package conversion.")

            for _, eng in df_audit.iterrows():
                is_alert = eng["status_flag"] == "OVER_BUDGET_DAILY"
                box = st.error if is_alert else st.info
                with box(f"**{eng['name']}** ({eng['specialization']}) — Current: `{eng['current_contract']}`"):
                    ec1, ec2, ec3 = st.columns(3)
                    ec1.write(f"**Total Site Visits:** {eng['visit_count']} visits ({eng['total_visit_days']} days)")
                    ec1.write(f"**Daily Rate:** IDR {eng['daily_rate_idr']:,.0f}")
                    
                    ec2.write(f"**Equivalent Incurred Cost:** IDR {eng['daily_cost_equivalent_idr']:,.0f}")
                    ec2.write(f"**Fixed Retainer Package:** IDR {eng['monthly_retainer_idr']:,.0f}")

                    ec3.markdown(f"**Recommendation:** `{eng['recommendation']}`")
                    if eng['potential_saving_idr'] > 0:
                        ec3.metric("Net Monthly Savings", f"IDR {eng['potential_saving_idr']:,.0f}", delta="Cost Cut")

    with tab3:
        st.subheader("Client-Side Margin Improvement Tracker")
        st.markdown("Logs CAPEX / OPEX efficiency implementations at client sites to track gross margin improvement.")
        
        m_summary = margin_opt.get_summary_metrics()
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Total CAPEX Savings", f"IDR {m_summary['total_capex_savings_idr']:,.0f}")
        sc2.metric("Annual OPEX Reductions", f"IDR {m_summary['total_opex_savings_annual_idr']:,.0f}")
        sc3.metric("Cumulative Gross Margin Gain", f"+{m_summary['cumulative_margin_improvement_pct']}%", delta="Profitability Boost")

        st.markdown("---")
        df_margin = margin_opt.get_all_initiatives()
        st.dataframe(df_margin, use_container_width=True)

    with tab4:
        st.subheader("Log Operational Spend or Engineer Visit")
        subtab1, subtab2 = st.tabs(["Add SG&A Expense", "Log Engineer Site Visit"])
        
        with subtab1:
            with st.form("form_log_sga"):
                ec1, ec2 = st.columns(2)
                exp_date = ec1.date_input("Expense Date", value=date.today())
                exp_cat = ec2.selectbox("Category", ["Site Travel", "Local Logistics", "Admin & Office", "Other OPEX"])
                exp_desc = ec1.text_input("Description", "Vehicle rental and toll fees for tower cluster")
                exp_amt = ec2.number_input("Amount (IDR)", value=15000000.0, step=500000.0)
                exp_site = ec1.text_input("Related Site ID (Optional)", "SVD-BDG-003")

                if st.form_submit_button("Submit SG&A Expense"):
                    sga_calc.log_expense(exp_date.isoformat(), exp_cat, exp_desc, exp_amt, exp_site)
                    st.success("Expense successfully recorded into audit trail!")
                    st.rerun()

        with subtab2:
            with st.form("form_log_visit"):
                vc1, vc2 = st.columns(2)
                v_eng = vc1.selectbox("Field Engineer", ["FE-001 (Bambang Pamungkas)", "FE-002 (Ahmad Fauzi)", "FE-003 (Rian Hidayat)", "FE-004 (Dodi Prasetyo)"])
                v_site = vc2.text_input("Tower Site ID", "SVD-JKT-001")
                v_date = vc1.date_input("Visit Date", value=date.today())
                v_days = vc2.number_input("Intervention Duration (Days)", value=2, min_value=1, max_value=30)
                v_task = vc1.text_input("Task Detail", "Routine RF maintenance and link test")

                if st.form_submit_button("Log Field Intervention"):
                    eng_id = v_eng.split()[0]
                    manpower_opt.log_visit(eng_id, v_site, v_date.isoformat(), v_days, v_task)
                    st.success("Field intervention recorded! Utilization audit updated.")
                    st.rerun()
