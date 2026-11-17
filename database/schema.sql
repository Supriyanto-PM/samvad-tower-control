-- Samvad PMO Command Center (PMO-CC) Database Schema

-- Module 1: Supply Chain & Customs Guardian
CREATE TABLE IF NOT EXISTS customs_shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bl_number TEXT UNIQUE NOT NULL,
    vendor_name TEXT NOT NULL,
    item_description TEXT NOT NULL,
    port_of_origin TEXT NOT NULL,
    destination_port TEXT NOT NULL DEFAULT 'Tanjung Priok, Jakarta',
    ocean_freight_carrier TEXT,
    etd DATE NOT NULL,
    eta DATE NOT NULL,
    project_commissioning_deadline DATE NOT NULL,
    current_milestone TEXT NOT NULL DEFAULT 'Ocean Freight Transit',
    customs_channel TEXT DEFAULT 'Green', -- Green, Yellow, Red
    cleared_date DATE,
    delay_risk_status TEXT NOT NULL DEFAULT 'GREEN', -- GREEN, YELLOW, RED
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitor_intelligence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_name TEXT NOT NULL,
    product_category TEXT NOT NULL,
    model_or_part_number TEXT NOT NULL,
    technical_specs TEXT,
    quoted_unit_price_usd REAL NOT NULL,
    samvad_target_price_usd REAL,
    quote_date DATE NOT NULL,
    source_reference TEXT,
    negotiation_tactics_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Module 2: SG&A & Manpower Financial Sentinel
CREATE TABLE IF NOT EXISTS sga_budget_baseline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fiscal_year INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    total_project_revenue REAL NOT NULL,
    allocated_sga_budget REAL NOT NULL,
    sga_ceiling_percent REAL NOT NULL DEFAULT 12.0, -- Max 12% Year 1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sga_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_date DATE NOT NULL,
    category TEXT NOT NULL, -- 'Site Travel', 'Local Logistics', 'Admin & Office', 'Other OPEX'
    description TEXT NOT NULL,
    amount_idr REAL NOT NULL,
    site_id TEXT,
    logged_by TEXT DEFAULT 'PMO Lead',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS field_engineers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engineer_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    specialization TEXT NOT NULL,
    contract_type TEXT NOT NULL DEFAULT 'Daily Rate', -- 'Daily Rate' or 'Fixed Monthly Retainer'
    daily_rate_idr REAL NOT NULL,
    fixed_monthly_rate_idr REAL NOT NULL,
    status TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS engineer_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engineer_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    visit_date DATE NOT NULL,
    duration_days INTEGER NOT NULL DEFAULT 1,
    task_description TEXT NOT NULL,
    FOREIGN KEY(engineer_id) REFERENCES field_engineers(engineer_id)
);

CREATE TABLE IF NOT EXISTS client_margin_initiatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    site_id TEXT NOT NULL,
    initiative_title TEXT NOT NULL,
    category TEXT NOT NULL, -- 'Site Energy Efficiency', 'Solar Hybrid Upgrade', 'Fiber Routing Optimization', 'Passive Infrastructure'
    capex_saving_idr REAL DEFAULT 0,
    opex_saving_annual_idr REAL DEFAULT 0,
    gross_margin_impact_percent REAL NOT NULL,
    implementation_status TEXT NOT NULL DEFAULT 'In Progress', -- 'Proposed', 'In Progress', 'Completed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Module 3: Site Availability & SLA Operations
CREATE TABLE IF NOT EXISTS tower_sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT UNIQUE NOT NULL,
    site_name TEXT NOT NULL,
    region TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    ip_address TEXT,
    is_poc_pilot INTEGER DEFAULT 0, -- 1 = POC, 0 = Active Production Site
    current_status TEXT NOT NULL DEFAULT 'ONLINE', -- 'ONLINE', 'DEGRADED', 'DOWN'
    uptime_percent REAL NOT NULL DEFAULT 99.5,
    last_ping_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS site_incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id TEXT NOT NULL,
    incident_start TIMESTAMP NOT NULL,
    incident_end TIMESTAMP,
    duration_minutes INTEGER DEFAULT 0,
    root_cause TEXT,
    emergency_alert_sent INTEGER DEFAULT 0, -- 1 if sent after 15 min threshold
    resolved INTEGER DEFAULT 0,
    FOREIGN KEY(site_id) REFERENCES tower_sites(site_id)
);

CREATE TABLE IF NOT EXISTS sop_ic_checklists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_code TEXT UNIQUE NOT NULL,
    site_id TEXT NOT NULL,
    client_name TEXT NOT NULL,
    lead_technician TEXT NOT NULL,
    inspection_date DATE NOT NULL,
    checklist_data_json TEXT NOT NULL, -- JSON string of all items
    overall_status TEXT NOT NULL DEFAULT 'In Progress', -- 'In Progress', 'Approved & Signed'
    pdf_report_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Module 4: SLA Reporting & Presales Engine
CREATE TABLE IF NOT EXISTS poc_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poc_code TEXT UNIQUE NOT NULL,
    client_name TEXT NOT NULL,
    poc_scope TEXT NOT NULL,
    lead_presales_engineer TEXT NOT NULL,
    milestone_name TEXT NOT NULL,
    target_deadline DATE NOT NULL,
    stretch_target_deadline DATE NOT NULL, -- 5 days ahead
    actual_completion_date DATE,
    status TEXT NOT NULL DEFAULT 'On Track', -- 'On Track', 'Ahead (5-Day Target Met)', 'Lagging', 'Completed'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weekly_sla_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code TEXT UNIQUE NOT NULL,
    week_number INTEGER NOT NULL,
    reporting_year INTEGER NOT NULL,
    scheduled_run_at TIMESTAMP NOT NULL,
    actual_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_kpi_score REAL NOT NULL,
    kpi_tier TEXT NOT NULL, -- 'Maximum 120% Tier', '100% Target Met', 'Below Target'
    file_pdf_path TEXT,
    file_docx_path TEXT,
    file_xlsx_path TEXT,
    distribution_status TEXT DEFAULT 'Ready'
);

CREATE TABLE IF NOT EXISTS notification_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL, -- 'Telegram', 'WhatsApp'
    recipient TEXT NOT NULL,
    message_type TEXT NOT NULL, -- 'EMERGENCY_OUTAGE', 'CUSTOMS_ALERT', 'WEEKLY_REPORT'
    payload TEXT NOT NULL,
    sent_status TEXT NOT NULL, -- 'SUCCESS', 'SIMULATED', 'FAILED'
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Timor-Leste 100-Site National Rollout & Operational Routing Table
CREATE TABLE IF NOT EXISTS timor_sites_100 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    no INTEGER,
    site_id TEXT UNIQUE NOT NULL,
    site_name TEXT NOT NULL,
    district TEXT NOT NULL,
    site_type TEXT NOT NULL,
    rectifier TEXT NOT NULL,
    backup_hours REAL NOT NULL,
    revenue_tier TEXT NOT NULL,
    quadrant TEXT NOT NULL,
    has_dg TEXT NOT NULL,
    program TEXT NOT NULL,
    lon REAL NOT NULL,
    lat REAL NOT NULL,
    notes TEXT,
    haversine_distance_km REAL NOT NULL,
    accessible_route_km REAL NOT NULL,
    transport_mode TEXT NOT NULL,
    est_travel_time TEXT NOT NULL,
    assigned_forward_hub TEXT NOT NULL,
    deployment_zone TEXT NOT NULL,
    delivery_wave TEXT NOT NULL,
    priority_index REAL NOT NULL,
    priority_tier TEXT NOT NULL,
    readiness_gate TEXT NOT NULL,
    paas_status TEXT NOT NULL,
    operator TEXT DEFAULT 'Telkomcel',
    is_extreme INTEGER DEFAULT 0,
    assigned_team TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT NULL,
    last_updated_by TEXT DEFAULT NULL,
    blocker_reason TEXT DEFAULT NULL
);
