"""
UI View for Module 1: Supply Chain & Customs Guardian (KPI Category A — 25% Weight).
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
from datetime import date, timedelta
from modules.module1_customs.tracker import CustomsTracker
from modules.module1_customs.competitor_hub import CompetitorHub
from services.notification_service import NotificationDispatcher

def render_clean_html(html_str: str):
    """Renders HTML in Streamlit ensuring no markdown indented code block parsing occurs."""
    cleaned = " ".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

def render_module1():
    st.markdown("## Module 1: Supply Chain & Customs Guardian")
    st.caption("KPI Category A — 25% Weight | Target: 0% Logistics Delays & Robust Supplier Pricing Database")

    tracker = CustomsTracker()
    hub = CompetitorHub()
    dispatcher = NotificationDispatcher()

    tab1, tab2, tab3 = st.tabs(["Customs Milestone Tracker & SLA Alerts", "Competitor Intelligence Hub", "Register New Shipment / Quote"])

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

        # === LIVE MARINE AIS CARGO VESSEL RADAR (VESSELFINDER & MARINETRAFFIC PROTOCOL) ===
        st.markdown("---")
        st.subheader("Live Marine AIS Cargo Vessel Radar & International Sea Corridors")
        st.caption(
            "Automatic Identification System (AIS) Live Vessel Telemetry — Equivalent to **Flightradar24 for Ocean Cargo Ships** "
            "(Powered by VesselFinder & MarineTraffic Protocol). Tracking international telecom shipments for Timor-Leste & Regional Portfolios."
        )

        # Baseline Telecom Cargo Fleet
        vessels = [
            {
                "name": "MAERSK SENTOSA",
                "imo": "9456789",
                "imo_str": "IMO 9456789",
                "mmsi": "563048000",
                "mmsi_str": "MMSI 563048000",
                "call_sign": "9V8842",
                "flag": "Singapore [SG]",
                "flag_emoji": "",
                "carrier": "Maersk Line",
                "vendor": "Amara Raja Giga Factory",
                "cargo": "LiFePO4 48V/200Ah Lithium Batteries (DG Class 9 / UN38.3)",
                "bl": "BL-AMR-2026-1042",
                "origin": "Chennai Port (Madras), India",
                "dest": "Tanjung Priok, Jakarta",
                "lat": 5.65,
                "lon": 95.80,
                "speed_knots": 16.8,
                "heading": "125° (SE)",
                "status": "Underway Using Engine",
                "sea_zone": "Strait of Malacca (Sabang / Aceh TSS)",
                "eta": "2026-09-28",
                "color": "#10B981"
            },
            {
                "name": "MSC ALESSIA",
                "imo": "9225782",
                "imo_str": "IMO 9225782",
                "mmsi": "355915000",
                "mmsi_str": "MMSI 355915000",
                "call_sign": "3EGH2",
                "flag": "Panama [PA]",
                "flag_emoji": "",
                "carrier": "Mediterranean Shipping Co (MSC)",
                "vendor": "Kirloskar Oil Engines Ltd",
                "cargo": "Telecom Silent Diesel Gensets (10-15kVA Form AIFTA)",
                "bl": "BL-KIR-2026-1088",
                "origin": "Nhava Sheva (JNPT Mumbai), India",
                "dest": "Pelabuhan Belawan, Medan",
                "lat": 4.15,
                "lon": 98.90,
                "speed_knots": 12.4,
                "heading": "195° (SSW)",
                "status": "Underway (Arriving Port)",
                "sea_zone": "Belawan Port Approach Anchorage",
                "eta": "2026-10-04",
                "color": "#3B82F6"
            },
            {
                "name": "ONE INTEGRITY",
                "imo": "9939888",
                "imo_str": "IMO 9939888",
                "mmsi": "352002368",
                "mmsi_str": "MMSI 352002368",
                "call_sign": "3FBA9",
                "flag": "Japan [JP]",
                "flag_emoji": "",
                "carrier": "Ocean Network Express (ONE)",
                "vendor": "Applied Energy Solutions",
                "cargo": "Smart Hybrid Rectifiers & Solar Controllers",
                "bl": "BL-APP-2026-1120",
                "origin": "Chennai Port (India)",
                "dest": "Port Dili, Timor-Leste (via SG)",
                "lat": 10.20,
                "lon": 86.50,
                "speed_knots": 18.2,
                "heading": "112° (ESE)",
                "status": "Underway Using Engine",
                "sea_zone": "Bay of Bengal Deepwater Corridor",
                "eta": "2026-10-12",
                "color": "#8B5CF6"
            },
            {
                "name": "CMA CGM JACQUES SAADE",
                "imo": "9839179",
                "imo_str": "IMO 9839179",
                "mmsi": "228386700",
                "mmsi_str": "MMSI 228386700",
                "call_sign": "FMSL",
                "flag": "France [FR]",
                "flag_emoji": "",
                "carrier": "CMA CGM Group",
                "vendor": "ZTE Corporation",
                "cargo": "Microwave High-Capacity Backhaul Radios (Sumatra Backbone)",
                "bl": "BL-SVD-2026-0904",
                "origin": "Shanghai Port, China",
                "dest": "Pelabuhan Belawan, Medan",
                "lat": 12.80,
                "lon": 113.40,
                "speed_knots": 19.5,
                "heading": "210° (SSW)",
                "status": "Underway Using Engine",
                "sea_zone": "South China Sea Transit Corridor",
                "eta": "2026-10-11",
                "color": "#F59E0B"
            },
            {
                "name": "EVER APEX",
                "imo": "9893890",
                "imo_str": "IMO 9893890",
                "mmsi": "352986161",
                "mmsi_str": "MMSI 352986161",
                "call_sign": "3FQC5",
                "flag": "Taiwan [TW]",
                "flag_emoji": "",
                "carrier": "Evergreen Marine",
                "vendor": "Delta Electronics",
                "cargo": "Hybrid Solar Inverters & LiFePO4 Battery Systems",
                "bl": "BL-SVD-2026-0870",
                "origin": "Keelung, Taiwan",
                "dest": "Tanjung Priok, Jakarta",
                "lat": -5.95,
                "lon": 106.92,
                "speed_knots": 0.5,
                "heading": "0° (Anchored)",
                "status": "Moored / Discharging",
                "sea_zone": "Tanjung Priok Basin 3 Anchorage",
                "eta": "2026-09-29",
                "color": "#06B6D4"
            },
            {
                "name": "ONE OLYMPUS",
                "imo": "9318163",
                "imo_str": "IMO 9318163",
                "mmsi": "563004000",
                "mmsi_str": "MMSI 563004000",
                "call_sign": "9V2190",
                "flag": "Singapore [SG]",
                "flag_emoji": "",
                "carrier": "ONE Ocean Network",
                "vendor": "Rosenberger Telecommunications",
                "cargo": "Low-PIM Feeder Cables & RF Jumper Kits",
                "bl": "BL-SVD-2026-0915",
                "origin": "Singapore Port Hub",
                "dest": "Tanjung Perak, Surabaya",
                "lat": -3.80,
                "lon": 110.50,
                "speed_knots": 15.1,
                "heading": "145° (SE)",
                "status": "Underway Using Engine",
                "sea_zone": "Java Sea Marine Corridor",
                "eta": "2026-10-09",
                "color": "#EC4899"
            }
        ]

        # === 1. VESSEL SEARCH & INSPECTOR COMMAND BAR ("Menu Nyari Kapal") ===
        with st.container(border=True):
            scol_search, scol_select, scol_mode = st.columns([3.6, 3.4, 3.0], vertical_alignment="center")

            with scol_search:
                search_query = st.text_input(
                    "Search Vessel (Name / IMO / MMSI / B/L)",
                    value="",
                    placeholder="e.g. MAERSK, 9225782, BL-AMR, Kirloskar...",
                    key="vessel_search_text",
                    help="Search by vessel name, IMO (7 digits), MMSI (9 digits), vendor, or Bill of Lading number."
                )

            with scol_select:
                fleet_names = ["All Fleet Vessels (Overview)"] + [
                    f"{v['name']} ({v['imo_str']}) - {v['vendor'][:24]}..."
                    for v in vessels
                ]
                selected_vessel_option = st.selectbox(
                    "Select Project Cargo Vessel",
                    options=fleet_names,
                    index=0,
                    key="vessel_select_dropdown",
                    help="Select active cargo vessel carrying telecommunications power equipment."
                )

            with scol_mode:
                radar_mode = st.radio(
                    "Radar Display Mode:",
                    options=["VesselFinder Live AIS", "Telecom Sea Corridor"],
                    horizontal=True,
                    key="vessel_radar_mode",
                    help="Switch between satellite AIS live radar and Samvad maritime corridor view."
                )

        # Resolve active vessel filter
        active_vessel = None
        is_custom_search = False
        sq = search_query.strip().lower()

        if sq:
            # First match against fleet
            matched = [
                v for v in vessels
                if sq in v["name"].lower()
                or sq in v["imo"].lower()
                or sq in v["mmsi"].lower()
                or sq in v["vendor"].lower()
                or sq in v["cargo"].lower()
                or sq in v["bl"].lower()
                or sq in v["carrier"].lower()
            ]
            if matched:
                active_vessel = matched[0]
            else:
                # Custom vessel lookup
                imo_candidate = re.search(r'\b\d{7}\b', sq)
                custom_imo = imo_candidate.group(0) if imo_candidate else (sq if sq.isdigit() and len(sq) in [7, 9] else "")
                active_vessel = {
                    "name": search_query.strip().upper(),
                    "imo": custom_imo or "9456789",
                    "imo_str": f"IMO {custom_imo}" if custom_imo else "Live Query",
                    "mmsi": "",
                    "mmsi_str": "Per AIS",
                    "call_sign": "N/A",
                    "call_sign": "N/A",
                    "flag": "International",
                    "flag_emoji": "",
                    "carrier": "Global Ocean Carrier",
                    "vendor": "Direct Maritime Cargo Query",
                    "cargo": f"Live Vessel AIS Telemetry for '{search_query.strip()}'",
                    "bl": "CUSTOM-LOOKUP",
                    "origin": "International Origin Port",
                    "dest": "Destination Port",
                    "lat": 1.28,
                    "lon": 103.85,
                    "speed_knots": "Live AIS",
                    "heading": "AIS Telemetry",
                    "status": "Tracking via VesselFinder",
                    "sea_zone": "Malacca Strait / Singapore Hub",
                    "eta": "Per VesselFinder AIS Live",
                    "color": "#0284C7"
                }
                is_custom_search = True
        elif selected_vessel_option != "All Fleet Vessels (Overview)":
            for v in vessels:
                if v["name"] in selected_vessel_option:
                    active_vessel = v
                    break

        # === 2. ACTIVE VESSEL INSPECTOR CARD ("trus bisa terlihat") ===
        if active_vessel:
            v = active_vessel
            render_clean_html(
                f"""
                <div style="background: #FFFFFF; border: 1.5px solid {v['color']}; border-left: 6px solid {v['color']}; border-radius: 8px; padding: 14px 18px; margin: 10px 0 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div>
                                <b style="font-size: 1.05rem; color: #0F172A; letter-spacing: 0.3px;">{v['name']}</b>
                                <span style="font-size: 0.78rem; color: #64748B; margin-left: 8px;">{v['carrier']} &bull; {v['imo_str']} &bull; {v['mmsi_str']} &bull; Call: {v['call_sign']}</span>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="background: #ECFDF5; color: #065F46; font-size: 0.74rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #A7F3D0;">● {v['status'].upper()}</span>
                            <a href="https://www.vesselfinder.com/vessels/details/{v['imo']}" target="_blank" style="text-decoration: none; font-size: 0.74rem; background: #0284C7; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                                Open in VesselFinder ->
                            </a>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 12px; margin-bottom: 10px;">
                        <div>
                            <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Speed &amp; Course</span><br/>
                            <b style="font-size: 0.88rem; color: {v['color']};">{v['speed_knots']} Knots</b> <span style="font-size: 0.78rem; color: #475569;">({v['heading']})</span>
                        </div>
                        <div>
                            <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Coordinates &amp; Zone</span><br/>
                            <b style="font-size: 0.84rem; color: #0F172A;">{v['lat']}° N, {v['lon']}° E</b><br/>
                            <span style="font-size: 0.72rem; color: #64748B;">{v['sea_zone']}</span>
                        </div>
                        <div>
                            <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Maritime Route Corridor</span><br/>
                            <span style="font-size: 0.8rem; color: #1E293B;">{v['origin']}</span> &rarr; <b style="font-size: 0.8rem; color: #0F172A;">{v['dest']}</b>
                        </div>
                        <div>
                            <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Estimated Arrival (ETA)</span><br/>
                            <b style="font-size: 0.88rem; color: #0F172A;">{v['eta']}</b>
                        </div>
                    </div>
                    <div style="font-size: 0.78rem; color: #1E293B; line-height: 1.4; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <b>Vendor / OEM:</b> <span style="color: #0284C7; font-weight: 600;">{v['vendor']}</span> &nbsp;|&nbsp; 
                            <b>Cargo Manifest:</b> {v['cargo']} &nbsp;|&nbsp; 
                            <b>B/L Reference:</b> <code>{v['bl']}</code>
                        </div>
                        <div style="display: flex; gap: 6px;">
                            <a href="https://www.marinetraffic.com/en/ais/details/ships/imo:{v['imo']}" target="_blank" style="text-decoration: none; font-size: 0.72rem; background: #475569; color: white; padding: 2px 8px; border-radius: 4px; font-weight: 600;">MarineTraffic -></a>
                        </div>
                    </div>
                </div>
                """
            )

        # === 3. RADAR DISPLAY (VESSELFINDER LIVE AIS vs TELECOM CORRIDOR) ===
        if radar_mode == "VesselFinder Live AIS":
            # Center map coordinates on active vessel or regional maritime corridor
            center_lat = active_vessel["lat"] if active_vessel else 5.00
            center_lon = active_vessel["lon"] if active_vessel else 98.00
            zoom_lvl = 6 if active_vessel else 4
            imo_script = f'var imo = "{active_vessel["imo"]}";' if (active_vessel and active_vessel["imo"].isdigit()) else ""
            mmsi_script = f'var mmsi = "{active_vessel["mmsi"]}";' if (active_vessel and active_vessel["mmsi"].isdigit() and not imo_script) else ""

            st.caption(
                f"**VesselFinder Live AIS Radar Engine** &bull; "
                f"Displaying real-time cargo vessel telemetry via satellite & coastal AIS stations. "
                + (f"Target: **{active_vessel['name']} (IMO {active_vessel['imo']})**." if active_vessel else "Target: Southeast Asia & Indian Ocean Maritime Corridors.")
            )

            # VesselFinder AIS Map HTML Component
            vf_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        background: #0E1A2B;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    }}
                    #map-wrapper {{
                        width: 100%;
                        height: 480px;
                        border-radius: 8px;
                        overflow: hidden;
                        border: 1px solid #334155;
                        background: #0F172A;
                    }}
                </style>
            </head>
            <body>
                <div id="map-wrapper">
                    <script type="text/javascript">
                        var width = "100%";
                        var height = 480;
                        var latitude = {center_lat};
                        var longitude = {center_lon};
                        var zoom = {zoom_lvl};
                        var names = true;
                        {imo_script}
                        {mmsi_script}
                        var show_track = true;
                    </script>
                    <script type="text/javascript" src="https://www.vesselfinder.com/aismap.js"></script>
                </div>
            </body>
            </html>
            """
            components.html(vf_html, height=500, scrolling=False)

            # Live Action Quick Bar for VesselFinder
            vf_target_imo = active_vessel["imo"] if active_vessel else "9456789"
            vf_target_name = active_vessel["name"] if active_vessel else "Project Fleet"
            render_clean_html(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: center; background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 12px; margin-top: 6px; font-size: 0.78rem;">
                    <div style="color: #334155;">
                        <span style="color: #0284C7; font-weight: 700;">● Live Stream AIS:</span> Connected to VesselFinder satellite AIS feed. For 24h historical tracks and vessel photos, access the official portal.
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <a href="https://www.vesselfinder.com/vessels/details/{vf_target_imo}" target="_blank" style="text-decoration: none; background: #0284C7; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 600;">
                            Track {vf_target_name} on VesselFinder ->
                        </a>
                        <a href="https://www.vesselfinder.com" target="_blank" style="text-decoration: none; background: #475569; color: white; padding: 4px 10px; border-radius: 4px; font-weight: 600;">
                            VesselFinder Global AIS Radar ->
                        </a>
                    </div>
                </div>
                """
            )

        else:
            # === TELECOM SUPPLY CHAIN CORRIDOR RADAR (PLOTLY GEO MAP) ===
            fig_marine = go.Figure()

            # 1. Shipping Sea Lanes
            corridors = [
                {
                    "name": "Corridor: Chennai -> Tg. Priok (Maersk Sentosa)",
                    "lats": [13.085, 9.50, 5.65, 2.50, 1.25, -6.10],
                    "lons": [80.298, 88.00, 95.80, 101.50, 103.85, 106.88],
                    "color": "#10B981",
                    "text": "Chennai -> Strait of Malacca -> Tanjung Priok (Jakarta)"
                },
                {
                    "name": "Corridor: Nhava Sheva -> Belawan (MSC Alessia)",
                    "lats": [18.950, 6.95, 5.50, 4.15, 3.785],
                    "lons": [72.950, 79.85, 90.00, 98.90, 98.690],
                    "color": "#3B82F6",
                    "text": "Nhava Sheva (Mumbai) -> Sri Lanka -> Belawan (Medan)"
                },
                {
                    "name": "Corridor: Chennai -> Port Dili (ONE Integrity)",
                    "lats": [13.085, 10.20, 4.00, 1.25, -5.50, -8.20, -8.555],
                    "lons": [80.298, 86.50, 96.00, 103.85, 112.50, 122.50, 125.574],
                    "color": "#8B5CF6",
                    "text": "Chennai -> Bay of Bengal -> Singapore Hub -> Port Dili (Timor-Leste)"
                },
                {
                    "name": "Corridor: Shanghai -> Belawan (CMA CGM)",
                    "lats": [31.230, 22.00, 16.50, 12.80, 5.00, 3.785],
                    "lons": [121.500, 119.50, 116.00, 113.40, 105.00, 98.690],
                    "color": "#F59E0B",
                    "text": "Shanghai Port -> South China Sea -> Singapore -> Belawan (Medan)"
                },
                {
                    "name": "Corridor: Keelung -> Tg. Priok (Ever Apex)",
                    "lats": [25.130, 18.00, 10.00, 1.25, -3.00, -6.10],
                    "lons": [121.740, 118.00, 112.00, 104.00, 106.00, 106.88],
                    "color": "#06B6D4",
                    "text": "Keelung (Taiwan) -> South China Sea -> Karimata Strait -> Tanjung Priok"
                },
                {
                    "name": "Corridor: Singapore -> Surabaya (ONE Olympus)",
                    "lats": [1.280, -0.50, -2.50, -3.80, -6.00, -7.195],
                    "lons": [103.850, 105.50, 108.00, 110.50, 112.00, 112.735],
                    "color": "#EC4899",
                    "text": "Singapore Port -> Java Sea -> Tanjung Perak (Surabaya)"
                }
            ]

            for c in corridors:
                # If active vessel selected, highlight matching corridor and subtly fade others
                is_active_corridor = active_vessel and (active_vessel["name"] in c["name"])
                line_width = 3.5 if is_active_corridor else 2.0
                opacity = 1.0 if (not active_vessel or is_active_corridor) else 0.45

                fig_marine.add_trace(go.Scattermap(
                    lat=c["lats"],
                    lon=c["lons"],
                    mode="lines",
                    line=dict(width=line_width, color=c["color"]),
                    opacity=opacity,
                    name=c["name"].split(":")[1].strip(),
                    hoverinfo="text",
                    text=f"Sea Corridor: {c['text']}"
                ))

            # 2. Key Commercial Seaports
            port_lats = [18.950, 13.085, 31.230, 25.130, 1.280, 3.785, -6.100, -7.195, -1.272, -8.555]
            port_lons = [72.950, 80.298, 121.500, 121.740, 103.850, 98.690, 106.880, 112.735, 116.818, 125.574]
            port_names = [
                "Nhava Sheva (Mumbai)", "Chennai Port (Madras)", "Shanghai Port", "Keelung Port",
                "Singapore Port Hub", "Pelabuhan Belawan (Medan)", "Tanjung Priok (Jakarta)",
                "Tanjung Perak (Surabaya)", "Pelabuhan Semayang (Balikpapan)", "Port Dili (Timor-Leste)"
            ]
            fig_marine.add_trace(go.Scattermap(
                lat=port_lats,
                lon=port_lons,
                mode="markers+text",
                marker=dict(size=12, color="#0F172A"),
                text=port_names,
                textposition="top right",
                name="International Ports",
                hoverinfo="text"
            ))

            # 3. Live Vessel Positions
            for v in vessels:
                is_selected = active_vessel and active_vessel["name"] == v["name"]
                marker_size = 24 if is_selected else 18
                text_label = f"{v['name']} ({v['speed_knots']} kts)" if is_selected else f"{v['name']}"

                fig_marine.add_trace(go.Scattermap(
                    lat=[v["lat"]],
                    lon=[v["lon"]],
                    mode="markers+text",
                    marker=dict(size=marker_size, color=v["color"]),
                    text=[text_label],
                    textposition="bottom right",
                    name=f"{v['name']} ({v['carrier']})",
                    hoverinfo="text",
                    hovertext=(
                        f"<b>Vessel: {v['name']}</b> ({v['imo_str']})<br>"
                        f"Operator: {v['carrier']}<br>"
                        f"Payload: {v['cargo']}<br>"
                        f"Vendor: {v['vendor']}<br>"
                        f"B/L Ref: {v['bl']}<br>"
                        f"Route: {v['origin']} -> {v['dest']}<br>"
                        f"Speed: {v['speed_knots']} Knots &bull; Heading: {v['heading']}<br>"
                        f"Sea Zone: {v['sea_zone']}<br>"
                        f"ETA: {v['eta']}"
                    )
                ))

            # Center on active vessel if chosen, else regional view
            map_center_lat = active_vessel["lat"] if active_vessel else 6.5
            map_center_lon = active_vessel["lon"] if active_vessel else 98.0
            map_zoom = 5.8 if active_vessel else 3.6

            fig_marine.update_layout(
                height=450,
                margin=dict(l=0, r=0, t=10, b=10),
                map=dict(
                    style="open-street-map",
                    center=dict(lat=map_center_lat, lon=map_center_lon),
                    zoom=map_zoom
                ),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10)
                )
            )
            st.plotly_chart(fig_marine, use_container_width=True)

        # === 4. FLEET SUMMARY TELEMETRY CARDS ===
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.markdown("##### Project Maritime Fleet Telemetry (AIS Realtime Fleet)")

        # Render 3-column grid for fleet
        row1_cols = st.columns(3)
        for idx, v in enumerate(vessels[:3]):
            with row1_cols[idx]:
                render_clean_html(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 4px solid {v['color']}; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <b style="font-size: 0.92rem; color: #0F172A;">{v['name']}</b>
                            <span style="background: #ECFDF5; color: #065F46; font-size: 0.68rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; border: 1px solid #A7F3D0;">LIVE AIS</span>
                        </div>
                        <div style="font-size: 0.74rem; color: #64748B; margin: 3px 0 6px 0;">
                            {v['imo_str']} &bull; {v['carrier']}
                        </div>
                        <div style="font-size: 0.76rem; color: #1E293B; line-height: 1.4; background: #F8FAFC; padding: 6px 8px; border-radius: 4px; margin-bottom: 6px;">
                            <b>Vendor:</b> {v['vendor']}<br/>
                            <b>Payload:</b> {v['cargo'][:42]}...<br/>
                            <b>B/L Ref:</b> <code>{v['bl']}</code>
                        </div>
                        <div style="font-size: 0.75rem; color: #334155; line-height: 1.4;">
                            • <b>Route:</b> {v['origin'].split(',')[0]} &rarr; <b>{v['dest'].split(',')[0]}</b><br/>
                            • <b>Speed:</b> <b style="color: {v['color']};">{v['speed_knots']} Knots</b> ({v['heading']})<br/>
                            • <b>ETA Port:</b> <b style="color: #0F172A;">{v['eta']}</b>
                        </div>
                        <div style="margin-top: 8px; display: flex; gap: 6px;">
                            <a href="https://www.vesselfinder.com/vessels/details/{v['imo']}" target="_blank" style="text-decoration: none; font-size: 0.72rem; background: #0284C7; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600;">VesselFinder -></a>
                            <a href="https://www.marinetraffic.com/en/ais/details/ships/imo:{v['imo']}" target="_blank" style="text-decoration: none; font-size: 0.72rem; background: #475569; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600;">MarineTraffic -></a>
                        </div>
                    </div>
                    """
                )

        row2_cols = st.columns(3)
        for idx, v in enumerate(vessels[3:6]):
            with row2_cols[idx]:
                render_clean_html(
                    f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 4px solid {v['color']}; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <b style="font-size: 0.92rem; color: #0F172A;">{v['name']}</b>
                            <span style="background: #ECFDF5; color: #065F46; font-size: 0.68rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; border: 1px solid #A7F3D0;">LIVE AIS</span>
                        </div>
                        <div style="font-size: 0.74rem; color: #64748B; margin: 3px 0 6px 0;">
                            {v['imo_str']} &bull; {v['carrier']}
                        </div>
                        <div style="font-size: 0.76rem; color: #1E293B; line-height: 1.4; background: #F8FAFC; padding: 6px 8px; border-radius: 4px; margin-bottom: 6px;">
                            <b>Vendor:</b> {v['vendor']}<br/>
                            <b>Payload:</b> {v['cargo'][:42]}...<br/>
                            <b>B/L Ref:</b> <code>{v['bl']}</code>
                        </div>
                        <div style="font-size: 0.75rem; color: #334155; line-height: 1.4;">
                            • <b>Route:</b> {v['origin'].split(',')[0]} &rarr; <b>{v['dest'].split(',')[0]}</b><br/>
                            • <b>Speed:</b> <b style="color: {v['color']};">{v['speed_knots']} Knots</b> ({v['heading']})<br/>
                            • <b>ETA Port:</b> <b style="color: #0F172A;">{v['eta']}</b>
                        </div>
                        <div style="margin-top: 8px; display: flex; gap: 6px;">
                            <a href="https://www.vesselfinder.com/vessels/details/{v['imo']}" target="_blank" style="text-decoration: none; font-size: 0.72rem; background: #0284C7; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600;">VesselFinder -></a>
                            <a href="https://www.marinetraffic.com/en/ais/details/ships/imo:{v['imo']}" target="_blank" style="text-decoration: none; font-size: 0.72rem; background: #475569; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600;">MarineTraffic -></a>
                        </div>
                    </div>
                    """
                )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.subheader("Active International B/L Milestone Status")

        if not df_shipments.empty:
            for _, row in df_shipments.iterrows():
                risk = row["calculated_delay_risk"]
                status_badge = "[ON TRACK]" if risk == "GREEN" else ("[WATCHLIST]" if risk == "YELLOW" else "[CRITICAL]")
                
                with st.expander(f"{status_badge} B/L: **{row['bl_number']}** — {row['item_description']} ({row['vendor_name']})"):
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
                        if bcol1.button("Trigger Customs Push Alert", key=f"btn_alert_{row['bl_number']}"):
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
        st.markdown("#### Interactive Supplier Cost Pushback Calculator")
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
        st.subheader("Register New B/L Shipment")
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
