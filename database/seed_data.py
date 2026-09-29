"""
Seed sample data for Samvad PMO Command Center (PMO-CC).
Populates realistic operational records for testing and out-of-the-box demonstration.
"""
from datetime import date, timedelta
from database.connection import get_connection, init_db

def seed_all_data(db_path: str = None):
    """Seed comprehensive initial data into the SQLite database."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM customs_shipments")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # Already seeded

    today = date.today()

    # 1. Customs Shipments (B/L Tracker & SLA Buffer)
    shipments = [
        (
            "BL-SVD-2026-0891",
            "Huawei Technologies Co.",
            "5G Massive MIMO AAU & BBU Cabinets (Site Cluster Jakarta South)",
            "Shenzhen, China",
            "Tanjung Priok, Jakarta",
            "Maersk Line",
            (today - timedelta(days=12)).isoformat(),
            (today + timedelta(days=2)).isoformat(),
            (today + timedelta(days=10)).isoformat(),
            "Customs Inbound Inspection",
            "Yellow",
            None,
            "YELLOW",
            "Slight congestion at Tanjung Priok Port Terminal 3. Buffer = 8 days (Healthy but in watch list).",
        ),
        (
            "BL-SVD-2026-0904",
            "ZTE Corporation",
            "Microwave High-Capacity Backhaul Radios (Sumatra Backbone)",
            "Shanghai, China",
            "Belawan Port, Medan",
            "CMA CGM",
            (today - timedelta(days=8)).isoformat(),
            (today + timedelta(days=6)).isoformat(),
            (today + timedelta(days=7)).isoformat(),
            "Ocean Freight Transit",
            "Red",
            None,
            "RED",
            "CRITICAL: ETA is only 1 day before commissioning deadline! Red channel alert flagged.",
        ),
        (
            "BL-SVD-2026-0870",
            "Delta Electronics",
            "Hybrid Solar Inverters & LiFePO4 Battery Systems",
            "Keelung, Taiwan",
            "Tanjung Priok, Jakarta",
            "Evergreen Marine",
            (today - timedelta(days=25)).isoformat(),
            (today - timedelta(days=5)).isoformat(),
            (today + timedelta(days=15)).isoformat(),
            "Released to Warehouse",
            "Green",
            (today - timedelta(days=3)).isoformat(),
            "GREEN",
            "Customs cleared smoothly under Green channel. Delivered to Cikarang central staging.",
        ),
        (
            "BL-SVD-2026-0915",
            "Rosenberger Telecommunications",
            "Low-PIM Feeder Cables & RF Jumper Kits",
            "Singapore Port",
            "Tanjung Perak, Surabaya",
            "ONE Ocean Network",
            (today - timedelta(days=3)).isoformat(),
            (today + timedelta(days=5)).isoformat(),
            (today + timedelta(days=22)).isoformat(),
            "Ocean Freight Transit",
            "Green",
            None,
            "GREEN",
            "Ample buffer of 17 days. On schedule.",
        ),
    ]
    cursor.executemany(
        """
        INSERT INTO customs_shipments 
        (bl_number, vendor_name, item_description, port_of_origin, destination_port, ocean_freight_carrier,
         etd, eta, project_commissioning_deadline, current_milestone, customs_channel, cleared_date, delay_risk_status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        shipments,
    )

    # 2. Competitor Intelligence Hub
    competitor_quotes = [
        (
            "Vendor Alpha Telecom",
            "Massive MIMO Antennas 64T64R",
            "AAU-6400X",
            "C-band 3.5GHz, 320W output, integrated antenna array",
            14500.0,
            12800.0,
            (today - timedelta(days=40)).isoformat(),
            "RFP Telco Project Alpha Q2-2026",
            "Competitor offered 11% lower on volume > 50 units. Use for pushback on Huawei quote.",
        ),
        (
            "Vendor Beta Wireless",
            "Rectifier & Power Plant 48V/300A",
            "PWR-300-HYB",
            "Solar hybrid input capable, remote SNMP monitoring, 96.5% efficiency",
            4200.0,
            3750.0,
            (today - timedelta(days=20)).isoformat(),
            "Direct Vendor Price Sheet July 2026",
            "Leverage Delta Electronics quotes against Beta to gain additional 8% concession.",
        ),
        (
            "Vendor Gamma Optical",
            "Dense WDM 100G Transceivers",
            "DWDM-QSFP28-100G",
            "100G ZR4, 80km reach, duplex LC interface",
            1850.0,
            1600.0,
            (today - timedelta(days=15)).isoformat(),
            "Tender Reference Central Java",
            "Benchmark shows market price softening by 12% in Q3.",
        ),
    ]
    cursor.executemany(
        """
        INSERT INTO competitor_intelligence 
        (competitor_name, product_category, model_or_part_number, technical_specs, quoted_unit_price_usd,
         samvad_target_price_usd, quote_date, source_reference, negotiation_tactics_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        competitor_quotes,
    )

    # 3. SG&A Baseline Budget & Expenses
    # Project revenue: IDR 10,000,000,000 (10 Miliar). SG&A ceiling 12% = Max IDR 1,200,000,000.
    cursor.execute(
        """
        INSERT INTO sga_budget_baseline (fiscal_year, project_name, total_project_revenue, allocated_sga_budget, sga_ceiling_percent)
        VALUES (2026, 'Samvad Nationwide Tower Modernization', 10000000000.0, 1150000000.0, 12.0)
        """
    )

    sga_expenses = [
        ((today - timedelta(days=28)).isoformat(), "Site Travel", "Flight & lodging for PMO Lead and Lead FE to Surabaya clusters", 42500000.0, "SUB-CLUST-01"),
        ((today - timedelta(days=24)).isoformat(), "Local Logistics", "Inland trucking of antenna brackets & ground rods to Bandung sites", 28000000.0, "BDG-004"),
        ((today - timedelta(days=20)).isoformat(), "Admin & Office", "PMO operational software subscriptions & safety equipment PPE certification", 19500000.0, "HQ-JAKARTA"),
        ((today - timedelta(days=15)).isoformat(), "Site Travel", "Site inspection vehicle rental & fuel for West Java tower clusters", 35000000.0, "WJ-CLUST-02"),
        ((today - timedelta(days=10)).isoformat(), "Local Logistics", "Urgent crane & rigging equipment rental for Rooftop Tower 45M", 52000000.0, "JKT-ROOF-12"),
        ((today - timedelta(days=5)).isoformat(), "Admin & Office", "Project coordination meetings and client alignment workshop refreshments", 14000000.0, "HQ-JAKARTA"),
    ]
    cursor.executemany(
        """
        INSERT INTO sga_expenses (expense_date, category, description, amount_idr, site_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        sga_expenses,
    )

    # 4. Field Engineers & Visit Logs (Manpower Optimizer)
    engineers = [
        ("FE-001", "Bambang Pamungkas", "RF / Microwave Specialist", "Daily Rate", 2500000.0, 38000000.0, "Active"),
        ("FE-002", "Ahmad Fauzi", "Power, Solar & Rectifier Engineer", "Daily Rate", 2200000.0, 35000000.0, "Active"),
        ("FE-003", "Rian Hidayat", "Tower Rigger & Structural Inspector", "Fixed Monthly Retainer", 1800000.0, 28000000.0, "Active"),
        ("FE-004", "Dodi Prasetyo", "NOC & Fiber Optic Splicing Expert", "Daily Rate", 2400000.0, 36000000.0, "Active"),
    ]
    cursor.executemany(
        """
        INSERT INTO field_engineers (engineer_id, name, specialization, contract_type, daily_rate_idr, fixed_monthly_rate_idr, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        engineers,
    )

    visits = [
        # FE-001 has 18 visits this month -> 18 * 2.5jt = 45 jt! High utilization -> recommend retainer package (38 jt, save 7 jt/mo!)
        ("FE-001", "JKT-TWR-01", (today - timedelta(days=22)).isoformat(), 2, "Microwave link realigning"),
        ("FE-001", "JKT-TWR-04", (today - timedelta(days=18)).isoformat(), 3, "Interference audit"),
        ("FE-001", "BDG-TWR-09", (today - timedelta(days=12)).isoformat(), 4, "High-capacity backhaul upgrade"),
        ("FE-001", "SUB-TWR-03", (today - timedelta(days=6)).isoformat(), 5, "5G AAU RF calibration"),
        ("FE-001", "SUB-TWR-07", (today - timedelta(days=2)).isoformat(), 4, "Post-installation VSWR test"),
        # FE-002 has 16 visits -> 16 * 2.2jt = 35.2 jt -> Retainer is 35 jt
        ("FE-002", "JKT-ROOF-12", (today - timedelta(days=20)).isoformat(), 4, "Solar hybrid inverter wiring"),
        ("FE-002", "BDG-004", (today - timedelta(days=14)).isoformat(), 4, "Lithium battery bank installation"),
        ("FE-002", "SMG-TWR-02", (today - timedelta(days=8)).isoformat(), 4, "Rectifier controller replacement"),
        ("FE-002", "YOG-TWR-05", (today - timedelta(days=3)).isoformat(), 4, "Earthing and surge arrester check"),
        # FE-003 has 8 visits (already on retainer)
        ("FE-003", "JKT-TWR-01", (today - timedelta(days=15)).isoformat(), 4, "Tower painting & bolt tightening"),
        ("FE-003", "JKT-TWR-04", (today - timedelta(days=5)).isoformat(), 4, "Climbing safety line inspection"),
        # FE-004 has 5 visits
        ("FE-004", "BDG-004", (today - timedelta(days=10)).isoformat(), 3, "OTDR fiber trace & splice"),
        ("FE-004", "JKT-ROOF-12", (today - timedelta(days=4)).isoformat(), 2, "SFP transceiver replacement"),
    ]
    cursor.executemany(
        """
        INSERT INTO engineer_visits (engineer_id, site_id, visit_date, duration_days, task_description)
        VALUES (?, ?, ?, ?, ?)
        """,
        visits,
    )

    # 5. Client Margin Initiatives (CAPEX/OPEX Reduction)
    margin_initiatives = [
        (
            "Indosat Ooredoo Hutchison",
            "JKT-ROOF-12",
            "Smart Lithium Solar Hybridization",
            "Site Energy Efficiency",
            45000000.0,
            68000000.0,
            2.4,
            "Completed",
        ),
        (
            "Telkomsel Regional 2",
            "BDG-CLUST-ALL",
            "DC Aircon Intelligent Variable Speed Drive",
            "Site Energy Efficiency",
            28000000.0,
            42000000.0,
            1.8,
            "In Progress",
        ),
        (
            "XL Axiata Java-Bali",
            "SUB-TWR-03",
            "Passive Tower Sharing Bracket Optimization",
            "Passive Infrastructure",
            32000000.0,
            18000000.0,
            1.2,
            "Completed",
        ),
        (
            "Smartfren Telecom",
            "SMG-TWR-02",
            "High-Efficiency Dual-Band Microwave Dishes",
            "Site Energy Efficiency",
            15000000.0,
            24000000.0,
            0.9,
            "Proposed",
        ),
    ]
    cursor.executemany(
        """
        INSERT INTO client_margin_initiatives 
        (client_name, site_id, initiative_title, category, capex_saving_idr, opex_saving_annual_idr, gross_margin_impact_percent, implementation_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        margin_initiatives,
    )

    # 6. Tower Sites & Uptime Dashboard (KPI Category C - 95.0% threshold)
    sites = [
        ("SVD-JKT-001", "Kuningan Hub Tower", "DKI Jakarta", -6.2255, 106.8285, "10.200.1.10", 0, "ONLINE", 99.82),
        ("SVD-JKT-002", "Sudirman Central Rooftop", "DKI Jakarta", -6.2150, 106.8150, "10.200.1.11", 0, "ONLINE", 99.95),
        ("SVD-BDG-003", "Dago Highlands Microcell", "West Java", -6.8720, 107.6180, "10.200.2.14", 0, "ONLINE", 98.45),
        ("SVD-SUB-004", "Gubeng Gateway Site", "East Java", -7.2650, 112.7520, "10.200.3.20", 0, "ONLINE", 99.10),
        ("SVD-SMG-005", "Simpang Lima Rooftop", "Central Java", -6.9920, 110.4220, "10.200.4.15", 0, "ONLINE", 97.80),
        ("SVD-MDN-006", "Medan Ring Road Tower", "North Sumatra", 3.5850, 98.6750, "10.200.5.18", 0, "ONLINE", 96.25),
        ("POC-PILOT-01", "Telkomsel 5G Private Pilot", "Karawang Industrial", -6.3200, 107.3100, "10.200.9.1", 1, "ONLINE", 99.90),
        ("POC-PILOT-02", "Indosat Enterprise Edge POC", "Cikarang Hub", -6.3100, 107.1600, "10.200.9.2", 1, "DEGRADED", 95.40),
    ]
    cursor.executemany(
        """
        INSERT INTO tower_sites (site_id, site_name, region, latitude, longitude, ip_address, is_poc_pilot, current_status, uptime_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sites,
    )

    # 7. Site Incidents & Outage Audit
    incidents = [
        ("SVD-MDN-006", (today - timedelta(days=3)).isoformat() + " 03:15:00", (today - timedelta(days=3)).isoformat() + " 03:42:00", 27, "PLN Grid Failure & Generator Auto-transfer Delay", 1, 1),
        ("SVD-SMG-005", (today - timedelta(days=7)).isoformat() + " 14:10:00", (today - timedelta(days=7)).isoformat() + " 14:24:00", 14, "Fiber link jitter & packet drop", 0, 1),
        ("POC-PILOT-02", (today - timedelta(days=1)).isoformat() + " 09:20:00", (today - timedelta(days=1)).isoformat() + " 09:38:00", 18, "DC power controller firmware reset", 1, 1),
    ]
    cursor.executemany(
        """
        INSERT INTO site_incidents (site_id, incident_start, incident_end, duration_minutes, root_cause, emergency_alert_sent, resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        incidents,
    )

    # 8. POC Milestones (KPI Category D - '5-days ahead' stretch target)
    poc_milestones = [
        (
            "POC-2026-TELKOMSEL-01",
            "Telkomsel",
            "Autonomous Guided Vehicle (AGV) 5G Private Network",
            "Dodi Prasetyo",
            "Phase 1: Core Network & AAU Commissioning",
            (today + timedelta(days=15)).isoformat(),
            (today + timedelta(days=10)).isoformat(),
            (today - timedelta(days=2)).isoformat(),
            "Ahead (5-Day Target Met)",
            "Completed 7 days ahead of standard contract schedule! Exemplary performance.",
        ),
        (
            "POC-2026-INDOSAT-02",
            "Indosat Ooredoo Hutchison",
            "Smart AI Tower Video Analytics & Intrusion Edge",
            "Supriyanto",
            "Phase 2: Live Pilot Demo to Enterprise VP",
            (today + timedelta(days=12)).isoformat(),
            (today + timedelta(days=7)).isoformat(),
            None,
            "On Track",
            "Presentation deck approved. Edge servers mounted.",
        ),
        (
            "POC-2026-XL-03",
            "XL Axiata",
            "High-Capacity Millimeter Wave Mesh POC",
            "Bambang Pamungkas",
            "Phase 1: Radio Link Alignment & Benchmarking",
            (today + timedelta(days=5)).isoformat(),
            (today).isoformat(),
            None,
            "Lagging",
            "Pending customs release of mmWave backup antenna (Ref BL-SVD-2026-0904).",
        ),
    ]
    cursor.executemany(
        """
        INSERT INTO poc_milestones 
        (poc_code, client_name, poc_scope, lead_presales_engineer, milestone_name, target_deadline, stretch_target_deadline, actual_completion_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        poc_milestones,
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_all_data()
    print("Database schema initialized and seed data successfully loaded.")
