"""
Multi-Tenant Portfolio Dataset & Seeding Engine.
Provides realistic operational datasets for regional telecom operators:
- Telkomcel: 100 sites strictly in Timor-Leste (baseline seeded via timor_sites_data.py)
- XLSmart: 25 sites in Sumatera Utara & Aceh (Origin: Pelabuhan Belawan, Medan)
- Mitratel: 35 macro sites in Jawa Timur & Jawa Tengah (Origin: Pelabuhan Tanjung Perak, Surabaya)
- IOH (Indosat Ooredoo Hutchison): 20 sites in Kalimantan & IKN (Origin: Pelabuhan Semayang, Balikpapan)
Total: 180 sites forming the unified enterprise PMO Command Center.
"""
from typing import List, Dict, Any
import math
import pandas as pd
from database.connection import get_connection
from database.timor_sites_data import seed_timor_100_sites, calculate_haversine_km

# Origin Central Hubs
BELAWAN_PORT_COORDS = (3.7845, 98.6820)       # Belawan, Medan (XLSmart: Sumut & Aceh)
TANJUNG_PERAK_COORDS = (-7.1950, 112.7350)   # Tanjung Perak, Surabaya (Mitratel: Jatim & Jateng)
BALIKPAPAN_PORT_COORDS = (-1.2720, 116.8180) # Semayang, Balikpapan (IOH: Kalimantan & IKN)


# ==========================================
# 1. XLSMART: SUMATERA UTARA & ACEH (25 SITES)
# ==========================================
XLSMART_SITES_RAW: List[Dict[str, Any]] = [
    # Sumatera Utara (13 Sites)
    {"no": 101, "site_id": "XLS001", "site_name": "XLS Medan Merdeka Central", "district": "Kota Medan", "site_type": "Hub Site", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 98.6780, "lat": 3.5925, "notes": "Medan Core Fiber Node", "operator": "XLSmart", "paas_status": "🟢 Handover XLSmart"},
    {"no": 102, "site_id": "XLS002", "site_name": "XLS Belawan Port Gateway", "district": "Kota Medan", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 98.6820, "lat": 3.7845, "notes": "Belawan Harbor Inbound Terminal", "operator": "XLSmart", "paas_status": "🟢 Handover XLSmart"},
    {"no": 103, "site_id": "XLS003", "site_name": "XLS Kualanamu Airport Hub", "district": "Deli Serdang", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 98.8750, "lat": 3.5590, "notes": "Aviation Transit Corridor", "operator": "XLSmart", "paas_status": "🟢 Handover XLSmart"},
    {"no": 104, "site_id": "XLS007", "site_name": "XLS Berastagi Mountain Ridge", "district": "Karo", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 98.5120, "lat": 3.1880, "notes": "High Altitude Volcano View 1,350m", "operator": "XLSmart", "paas_status": "🟣 Power I&C Active"},
    {"no": 105, "site_id": "XLS008", "site_name": "XLS Pematang Siantar Sutomo", "district": "Pematang Siantar", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 99.0650, "lat": 2.9620, "notes": "Cross-Sumatra Distribution Hub", "operator": "XLSmart", "paas_status": "🟣 Power I&C Active"},
    {"no": 106, "site_id": "XLS009", "site_name": "XLS Parapat Danau Toba", "district": "Simalungun", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 98.9340, "lat": 2.6640, "notes": "Lake Toba Super Priority Tourism", "operator": "XLSmart", "paas_status": "🟣 Power I&C Active"},
    {"no": 107, "site_id": "XLS012", "site_name": "XLS Binjai Superblock", "district": "Binjai", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 98.4870, "lat": 3.6040, "notes": "Urban Micro-Cell Infill", "operator": "XLSmart", "paas_status": "🟡 Testing & QA"},
    {"no": 108, "site_id": "XLS015", "site_name": "XLS Sibolga Port Coastal", "district": "Sibolga", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 98.7860, "lat": 1.7450, "notes": "West Coast Harbor & Nias Gateway", "operator": "XLSmart", "paas_status": "🟡 Testing & QA"},
    {"no": 109, "site_id": "XLS016", "site_name": "XLS Kisaran Asahan Central", "district": "Asahan", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 99.6250, "lat": 2.9850, "notes": "Plantation Belt Corridor", "operator": "XLSmart", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 110, "site_id": "XLS017", "site_name": "XLS Stabat Langkat Bypass", "district": "Langkat", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 98.4520, "lat": 3.7460, "notes": "Tol Trans-Sumatera Access", "operator": "XLSmart", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 111, "site_id": "XLS020", "site_name": "XLS Rantau Prapat Hub", "district": "Labuhanbatu", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 99.8270, "lat": 2.0980, "notes": "South Sumut Distribution Node", "operator": "XLSmart", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 112, "site_id": "XLS023", "site_name": "XLS Gunungsitoli Nias Island", "district": "Nias", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 97.6160, "lat": 1.2910, "notes": "Maritime Ro-Ro Access via Sibolga", "operator": "XLSmart", "paas_status": "Shipping & Customs"},
    {"no": 113, "site_id": "XLS025", "site_name": "XLS Balige Toba Samosir", "district": "Toba", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 99.0620, "lat": 2.3350, "notes": "South Toba Highway Node", "operator": "XLSmart", "paas_status": "Shipping & Customs"},

    # Aceh (12 Sites)
    {"no": 114, "site_id": "XLS004", "site_name": "XLS Banda Aceh Baiturrahman", "district": "Banda Aceh", "site_type": "Hub Site", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 95.3180, "lat": 5.5535, "notes": "Banda Aceh Regional Center", "operator": "XLSmart", "paas_status": "🟢 Handover XLSmart"},
    {"no": 115, "site_id": "XLS005", "site_name": "XLS Ulee Lheue Port Terminal", "district": "Banda Aceh", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 95.2860, "lat": 5.5620, "notes": "Sabang Ferry Gateway Terminal", "operator": "XLSmart", "paas_status": "🟢 Handover XLSmart"},
    {"no": 116, "site_id": "XLS006", "site_name": "XLS Lhokseumawe Cunda Hub", "district": "Lhokseumawe", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q2-High", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 97.1350, "lat": 5.1760, "notes": "Industrial Petrochemical Zone", "operator": "XLSmart", "paas_status": "🟢 Handover XLSmart"},
    {"no": 117, "site_id": "XLS010", "site_name": "XLS Langsa Merdeka Terminal", "district": "Langsa", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 97.9650, "lat": 4.4750, "notes": "Sumut-Aceh Highway Node", "operator": "XLSmart", "paas_status": "🟣 Power I&C Active"},
    {"no": 118, "site_id": "XLS011", "site_name": "XLS Sigli Pidie Highway", "district": "Pidie", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q2-High", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 95.9640, "lat": 5.3820, "notes": "Jalinsum Transit Node", "operator": "XLSmart", "paas_status": "🟣 Power I&C Active"},
    {"no": 119, "site_id": "XLS013", "site_name": "XLS Sabang Balohan Ferry Mast", "district": "Sabang", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 95.3340, "lat": 5.8450, "notes": "Pulau Weh Island Ferry Terminal", "operator": "XLSmart", "paas_status": "🟡 Testing & QA"},
    {"no": 120, "site_id": "XLS014", "site_name": "XLS Bireuen Kota Juang", "district": "Bireuen", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 96.7030, "lat": 5.2040, "notes": "Central Aceh Transit Point", "operator": "XLSmart", "paas_status": "🟡 Testing & QA"},
    {"no": 121, "site_id": "XLS018", "site_name": "XLS Kualasimpang Tamiang", "district": "Aceh Tamiang", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 98.0550, "lat": 4.2860, "notes": "Provincial Border Gateway", "operator": "XLSmart", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 122, "site_id": "XLS019", "site_name": "XLS Takengon Danau Laut Tawar", "district": "Aceh Tengah", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 96.8480, "lat": 4.6280, "notes": "Gayo Highland Coffee Belt 1,200m", "operator": "XLSmart", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 123, "site_id": "XLS021", "site_name": "XLS Meulaboh West Beach", "district": "Aceh Barat", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 96.1260, "lat": 4.1410, "notes": "Indian Ocean Coastal Route", "operator": "XLSmart", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 124, "site_id": "XLS022", "site_name": "XLS Jantho Aceh Besar", "district": "Aceh Besar", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "XLSmart PaaS", "lon": 95.6230, "lat": 5.2710, "notes": "Government Corridor Node", "operator": "XLSmart", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 125, "site_id": "XLS024", "site_name": "XLS Tapaktuan Dragon Head", "district": "Aceh Selatan", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "XLSmart PaaS", "lon": 97.1790, "lat": 3.2610, "notes": "South Aceh Coastal Spine", "operator": "XLSmart", "paas_status": "Shipping & Customs"},
]

GOOGLE_MAPS_ROUTING_BELAWAN: Dict[str, Dict[str, Any]] = {
    "XLS001": {"route_km": 26.4, "eta": "35 - 45 mins", "mode": "Tol Belmera (GT Belawan ➔ GT H. Anif) & Ring Road", "hub": "Medan Central Logistics Hub", "zone": "Zone 1 | Medan Metropolitan Core", "wave": "Wave 1 | Medan Metropolitan Core"},
    "XLS002": {"route_km": 3.2, "eta": "8 - 12 mins", "mode": "Jl. Pelabuhan Raya & Akses Dermaga Bandar Deli", "hub": "Medan Central Logistics Hub", "zone": "Zone 1 | Medan Metropolitan Core", "wave": "Wave 1 | Medan Metropolitan Core"},
    "XLS003": {"route_km": 46.8, "eta": "45 - 55 mins", "mode": "Tol Belmera ➔ Tol Medan-Kualanamu-Tebing Tinggi (MKTT)", "hub": "Medan Central Logistics Hub", "zone": "Zone 1 | Medan Metropolitan Core", "wave": "Wave 1 | Medan Metropolitan Core"},
    "XLS007": {"route_km": 88.5, "eta": "2.7 - 3.2 hrs", "mode": "Tol Belmera ➔ Jl. Jamin Ginting ➔ Pegunungan Sembahe-Berastagi (1,350m)", "hub": "Medan Central Logistics Hub", "zone": "Zone 3 | Bukit Barisan Highlands", "wave": "Wave 3 | Highlands & Lake Toba"},
    "XLS008": {"route_km": 142.0, "eta": "2.2 - 2.8 hrs", "mode": "Tol MKTT ➔ Tol Tebing Tinggi ➔ Jalinsum Siantar (Expressway)", "hub": "Medan Central Logistics Hub", "zone": "Zone 2 | North Sumatra Corridors", "wave": "Wave 2 | North Sumatra Corridors"},
    "XLS009": {"route_km": 186.5, "eta": "3.2 - 3.8 hrs", "mode": "Tol MKTT ➔ Tol Sinaksak ➔ Jalinsum Danau Toba Parapat", "hub": "Medan Central Logistics Hub", "zone": "Zone 3 | Bukit Barisan Highlands", "wave": "Wave 3 | Highlands & Lake Toba"},
    "XLS012": {"route_km": 36.2, "eta": "40 - 50 mins", "mode": "Tol Belmera ➔ Tol Medan-Binjai (Mebi Expressway)", "hub": "Medan Central Logistics Hub", "zone": "Zone 1 | Medan Metropolitan Core", "wave": "Wave 1 | Medan Metropolitan Core"},
    "XLS015": {"route_km": 358.0, "eta": "8.5 - 9.5 hrs", "mode": "Jalinsum Tengah ➔ Tarutung ➔ Cadas Batu Lubang Sibolga", "hub": "Sibolga Forward Hub", "zone": "Zone 4 | Southern & Western Outliers", "wave": "Wave 4 | Southern & Western Outliers"},
    "XLS016": {"route_km": 168.0, "eta": "2.3 - 2.8 hrs", "mode": "Tol MKTT ➔ Tol Indrapura-Kisaran (GT Kisaran Direct)", "hub": "Medan Central Logistics Hub", "zone": "Zone 2 | North Sumatra Corridors", "wave": "Wave 2 | North Sumatra Corridors"},
    "XLS017": {"route_km": 52.4, "eta": "55 - 70 mins", "mode": "Tol Medan-Binjai ➔ Tol Binjai-Stabat Expressway", "hub": "Medan Central Logistics Hub", "zone": "Zone 2 | North Sumatra Corridors", "wave": "Wave 2 | North Sumatra Corridors"},
    "XLS020": {"route_km": 284.0, "eta": "5.2 - 6.0 hrs", "mode": "Tol Indrapura-Kisaran ➔ Jalinsum Lintas Timur Rantau Prapat", "hub": "Medan Central Logistics Hub", "zone": "Zone 2 | North Sumatra Corridors", "wave": "Wave 4 | Southern & Western Outliers"},
    "XLS023": {"route_km": 478.0, "eta": "17 - 19 hrs (Overland + Ro-Ro Ferry)", "mode": "Jalinsum Sibolga (358 km) + Feri Ro-Ro ASDP Nias (120 km)", "hub": "Sibolga Forward Hub", "zone": "Zone 5 | Island Enclaves (Nias & Sabang)", "wave": "Wave 5 | Island Enclaves"},
    "XLS025": {"route_km": 242.0, "eta": "4.7 - 5.5 hrs", "mode": "Tol MKTT ➔ Siantar ➔ Parapat ➔ Jalinsum Toba Balige", "hub": "Sibolga Forward Hub", "zone": "Zone 3 | Bukit Barisan Highlands", "wave": "Wave 3 | Highlands & Lake Toba"},
    "XLS004": {"route_km": 586.0, "eta": "11.5 - 13.0 hrs", "mode": "Jalan Nasional Lintas Timur Sumatera ➔ Tol Sibanceh", "hub": "Banda Aceh Forward Hub", "zone": "Zone 2 | Banda Aceh Metropolitan", "wave": "Wave 2 | Banda Aceh & North Corridor"},
    "XLS005": {"route_km": 592.5, "eta": "11.8 - 13.2 hrs", "mode": "Jalan Nasional Banda Aceh ➔ Akses Pelabuhan Ulee Lheue", "hub": "Banda Aceh Forward Hub", "zone": "Zone 2 | Banda Aceh Metropolitan", "wave": "Wave 2 | Banda Aceh & North Corridor"},
    "XLS006": {"route_km": 298.0, "eta": "5.7 - 6.5 hrs", "mode": "Jalan Nasional Medan-Banda Aceh (Koridor Industri Lhokseumawe)", "hub": "Lhokseumawe Industrial Hub", "zone": "Zone 3 | Aceh Northern Coastal", "wave": "Wave 2 | North Sumatra & Aceh Corridors"},
    "XLS010": {"route_km": 152.0, "eta": "3.2 - 3.8 hrs", "mode": "Tol Stabat ➔ Pangkalan Brandan ➔ Jalinsum Langsa", "hub": "Lhokseumawe Industrial Hub", "zone": "Zone 3 | Aceh Northern Coastal", "wave": "Wave 2 | North Sumatra & Aceh Corridors"},
    "XLS011": {"route_km": 472.0, "eta": "9.2 - 10.5 hrs", "mode": "Jalan Nasional Medan-Banda Aceh (Koridor Sigli Pidie)", "hub": "Banda Aceh Forward Hub", "zone": "Zone 2 | Banda Aceh Metropolitan", "wave": "Wave 2 | Banda Aceh & North Corridor"},
    "XLS013": {"route_km": 625.5, "eta": "13.5 - 15.0 hrs (Overland + Fast Boat)", "mode": "Overland ke Ulee Lheue (592.5 km) + Fast Boat Express Bahari (33 km)", "hub": "Banda Aceh Forward Hub", "zone": "Zone 5 | Island Enclaves (Nias & Sabang)", "wave": "Wave 5 | Island Enclaves"},
    "XLS014": {"route_km": 352.0, "eta": "6.7 - 7.7 hrs", "mode": "Jalan Nasional Medan-Banda Aceh (Kota Juang Bireuen)", "hub": "Lhokseumawe Industrial Hub", "zone": "Zone 3 | Aceh Northern Coastal", "wave": "Wave 2 | North Sumatra & Aceh Corridors"},
    "XLS018": {"route_km": 118.0, "eta": "2.5 - 3.0 hrs", "mode": "Tol Stabat ➔ Pangkalan Brandan ➔ Kualasimpang Tamiang", "hub": "Medan Central Logistics Hub", "zone": "Zone 3 | Aceh Northern Coastal", "wave": "Wave 2 | North Sumatra & Aceh Corridors"},
    "XLS019": {"route_km": 408.0, "eta": "8.5 - 9.8 hrs", "mode": "Jalan Nasional Bireuen-Takengon (Tanjakan Pegunungan Gayo 1,200m)", "hub": "Lhokseumawe Industrial Hub", "zone": "Zone 4 | Gayo & Bukit Barisan Highlands", "wave": "Wave 4 | Highlands & West Coast"},
    "XLS021": {"route_km": 465.0, "eta": "10.0 - 11.5 hrs", "mode": "Tol Binjai ➔ Kabanjahe ➔ Sidikalang ➔ Subulussalam ➔ Meulaboh", "hub": "Banda Aceh Forward Hub", "zone": "Zone 4 | Gayo & Bukit Barisan Highlands", "wave": "Wave 4 | Highlands & West Coast"},
    "XLS022": {"route_km": 542.0, "eta": "10.2 - 11.5 hrs", "mode": "Jalan Nasional Aceh ➔ Tol Sibanceh (Seksi Seulimeum-Jantho)", "hub": "Banda Aceh Forward Hub", "zone": "Zone 2 | Banda Aceh Metropolitan", "wave": "Wave 2 | Banda Aceh & North Corridor"},
    "XLS024": {"route_km": 382.0, "eta": "8.7 - 10.0 hrs", "mode": "Tol Binjai ➔ Kabanjahe ➔ Sidikalang ➔ Subulussalam ➔ Tapaktuan", "hub": "Sibolga Forward Hub", "zone": "Zone 4 | Gayo & Bukit Barisan Highlands", "wave": "Wave 4 | Highlands & West Coast"}
}


# ==========================================
# 2. MITRATEL: JAWA TIMUR & JAWA TENGAH (35 SITES)
# ==========================================
MITRATEL_SITES_RAW: List[Dict[str, Any]] = [
    # Jawa Timur (20 Sites)
    {"no": 146, "site_id": "MTL001", "site_name": "Mitratel Surabaya Perak Macro 1", "district": "Surabaya", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.7310, "lat": -7.2010, "notes": "Surabaya Harbor Logistics SST", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 147, "site_id": "MTL002", "site_name": "Mitratel Surabaya Gubeng Central", "district": "Surabaya", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.7520, "lat": -7.2650, "notes": "Surabaya CBD Central Node", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 148, "site_id": "MTL003", "site_name": "Mitratel Sidoarjo Waru Industrial", "district": "Sidoarjo", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.7280, "lat": -7.3520, "notes": "Waru Transport & Industrial Hub", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 149, "site_id": "MTL004", "site_name": "Mitratel Gresik Manyar Port Access", "district": "Gresik", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 5.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.5890, "lat": -7.1210, "notes": "JIIPE Manyar Industrial Gateway", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 150, "site_id": "MTL005", "site_name": "Mitratel Mojokerto Bypass Macro", "district": "Mojokerto", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.4410, "lat": -7.4720, "notes": "Tol Surabaya-Mojokerto Arterial", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 151, "site_id": "MTL006", "site_name": "Mitratel Pasuruan Pier Corridor", "district": "Pasuruan", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.9050, "lat": -7.6450, "notes": "Kawasan Industri PIER Pasuruan", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 152, "site_id": "MTL007", "site_name": "Mitratel Probolinggo Bromo Gateway", "district": "Probolinggo", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 113.2180, "lat": -7.7580, "notes": "Bromo Tengger Semeru Access", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 153, "site_id": "MTL008", "site_name": "Mitratel Malang Singosari High Mast", "district": "Malang", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Gold", "quadrant": "Q2-High", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.6650, "lat": -7.8920, "notes": "Tol Pandaan-Malang Corridor", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 154, "site_id": "MTL009", "site_name": "Mitratel Batu Mountain Ridge", "district": "Batu", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 112.5280, "lat": -7.8710, "notes": "Batu Highlands 850m", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 155, "site_id": "MTL010", "site_name": "Mitratel Kediri Dhoho Airport Corridor", "district": "Kediri", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 112.0120, "lat": -7.8150, "notes": "Bandara Dhoho Kediri Ingress", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 156, "site_id": "MTL011", "site_name": "Mitratel Madiun Caruban Junction", "district": "Madiun", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 111.6580, "lat": -7.5450, "notes": "Tol Trans-Jawa Kertosono-Ngawi", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 157, "site_id": "MTL012", "site_name": "Mitratel Jombang Tembelang Macro", "district": "Jombang", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 112.2350, "lat": -7.5180, "notes": "Central Jatim Transit Spine", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 158, "site_id": "MTL013", "site_name": "Mitratel Tuban Pantura Macro", "district": "Tuban", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.0620, "lat": -6.8980, "notes": "Pantura Coast Industrial Node", "operator": "Mitratel", "paas_status": "🟡 Testing & QA"},
    {"no": 159, "site_id": "MTL014", "site_name": "Mitratel Lamongan Babat Transit", "district": "Lamongan", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 112.1640, "lat": -7.1120, "notes": "Babat River Interlink", "operator": "Mitratel", "paas_status": "🟡 Testing & QA"},
    {"no": 160, "site_id": "MTL015", "site_name": "Mitratel Banyuwangi Ketapang Port", "district": "Banyuwangi", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 114.3980, "lat": -8.1480, "notes": "Bali Strait Ferry Interlink", "operator": "Mitratel", "paas_status": "🟡 Testing & QA"},
    {"no": 161, "site_id": "MTL016", "site_name": "Mitratel Jember Kota Mast", "district": "Jember", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 113.7010, "lat": -8.1720, "notes": "East Tapal Kuda Backbone", "operator": "Mitratel", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 162, "site_id": "MTL017", "site_name": "Mitratel Bojonegoro Cepu Basin", "district": "Bojonegoro", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 111.8820, "lat": -7.1520, "notes": "Cepu Energy Sector Relay", "operator": "Mitratel", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 163, "site_id": "MTL018", "site_name": "Mitratel Bangkalan Suramadu Node", "district": "Bangkalan", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 112.7950, "lat": -7.0420, "notes": "Jembatan Suramadu Madura Gateway", "operator": "Mitratel", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 164, "site_id": "MTL019", "site_name": "Mitratel Sampang Madura Central", "district": "Sampang", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 113.2420, "lat": -7.1850, "notes": "Madura Island Trans-Highway", "operator": "Mitratel", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 165, "site_id": "MTL020", "site_name": "Mitratel Sumenep Kalianget Port", "district": "Sumenep", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 113.9180, "lat": -7.0480, "notes": "East Madura Kalianget Ferry", "operator": "Mitratel", "paas_status": "Shipping & Customs"},

    # Jawa Tengah (15 Sites)
    {"no": 166, "site_id": "MTL021", "site_name": "Mitratel Semarang Tanjung Emas Harbor", "district": "Semarang", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 110.4210, "lat": -6.9530, "notes": "Pelabuhan Tanjung Emas Node", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 167, "site_id": "MTL022", "site_name": "Mitratel Semarang Simpang Lima Core", "district": "Semarang", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 110.4230, "lat": -6.9920, "notes": "Central Java Capital Hub", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 168, "site_id": "MTL023", "site_name": "Mitratel Surakarta Manahan Node", "district": "Surakarta", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 110.8120, "lat": -7.5560, "notes": "Solo Metropolitan Core", "operator": "Mitratel", "paas_status": "🟢 Handover Mitratel"},
    {"no": 169, "site_id": "MTL024", "site_name": "Mitratel Boyolali Tol Rest Area", "district": "Boyolali", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q2-High", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 110.5980, "lat": -7.5320, "notes": "Tol Trans-Jawa Solo-Semarang", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 170, "site_id": "MTL025", "site_name": "Mitratel Klaten Prambanan Corridor", "district": "Klaten", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 110.6050, "lat": -7.7120, "notes": "Solo-Jogja Arterial Interlink", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 171, "site_id": "MTL026", "site_name": "Mitratel Magelang Borobudur Tourism", "district": "Magelang", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 110.2040, "lat": -7.6080, "notes": "Borobudur Super Priority Tourism", "operator": "Mitratel", "paas_status": "🟣 Power I&C Active"},
    {"no": 172, "site_id": "MTL027", "site_name": "Mitratel Salatiga Exit Tol Macro", "district": "Salatiga", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 110.5050, "lat": -7.3320, "notes": "GT Salatiga Panorama Transit", "operator": "Mitratel", "paas_status": "🟡 Testing & QA"},
    {"no": 173, "site_id": "MTL028", "site_name": "Mitratel Kudus Kota Kretek", "district": "Kudus", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q2-High", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 110.8420, "lat": -6.8050, "notes": "Jalur Pantura Timur Jateng", "operator": "Mitratel", "paas_status": "🟡 Testing & QA"},
    {"no": 174, "site_id": "MTL029", "site_name": "Mitratel Demak Sayung Pantura", "district": "Demak", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 110.5280, "lat": -6.9280, "notes": "Tol Tanggul Laut Semarang-Demak", "operator": "Mitratel", "paas_status": "🟡 Testing & QA"},
    {"no": 175, "site_id": "MTL030", "site_name": "Mitratel Pekalongan Batik Pantura", "district": "Pekalongan", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 109.6750, "lat": -6.8890, "notes": "Tol Pemalang-Batang Exit", "operator": "Mitratel", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 176, "site_id": "MTL031", "site_name": "Mitratel Tegal Brebes Border", "district": "Tegal", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 109.1380, "lat": -6.8710, "notes": "Tol Pejagan-Pemalang Interlink", "operator": "Mitratel", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 177, "site_id": "MTL032", "site_name": "Mitratel Banyumas Purwokerto Slope", "district": "Banyumas", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 109.2410, "lat": -7.4250, "notes": "Gunung Slamet Foothills 650m", "operator": "Mitratel", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 178, "site_id": "MTL033", "site_name": "Mitratel Cilacap Teluk Penyu Coastal", "district": "Cilacap", "site_type": "Macro Tower", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Mitratel Tower PaaS", "lon": 109.0150, "lat": -7.7280, "notes": "South Coast Industrial Harbor", "operator": "Mitratel", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 179, "site_id": "MTL034", "site_name": "Mitratel Wonosobo Dieng Plateau 2000m", "district": "Wonosobo", "site_type": "Macro Tower", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q2-High", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 109.9180, "lat": -7.2150, "notes": "Dieng Volcanic Plateau 2,050m", "operator": "Mitratel", "paas_status": "Shipping & Customs"},
    {"no": 180, "site_id": "MTL035", "site_name": "Mitratel Kebumen Lintas Selatan", "district": "Kebumen", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Mitratel Tower PaaS", "lon": 109.6580, "lat": -7.6720, "notes": "Jalur Daendels Pansela Trans-Jawa", "operator": "Mitratel", "paas_status": "Shipping & Customs"},
]

GOOGLE_MAPS_ROUTING_PERAK: Dict[str, Dict[str, Any]] = {
    "MTL001": {"route_km": 3.5, "eta": "8 - 12 mins", "mode": "Jl. Perak Timur & Dermaga Madura Gate", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 1 | Surabaya Metropolitan Core", "wave": "Wave 1 | Surabaya Metropolitan Core"},
    "MTL002": {"route_km": 11.8, "eta": "20 - 30 mins", "mode": "Jl. Kusuma Bangsa ➔ CBD Gubeng Surabaya", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 1 | Surabaya Metropolitan Core", "wave": "Wave 1 | Surabaya Metropolitan Core"},
    "MTL003": {"route_km": 24.5, "eta": "25 - 35 mins", "mode": "Tol Surabaya-Gempol (GT Waru Utama)", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 1 | Surabaya Metropolitan Core", "wave": "Wave 1 | Surabaya Metropolitan Core"},
    "MTL004": {"route_km": 28.2, "eta": "30 - 40 mins", "mode": "Tol Surabaya-Manyar (Akses JIIPE Gresik)", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 1 | Surabaya Metropolitan Core", "wave": "Wave 1 | Surabaya Metropolitan Core"},
    "MTL005": {"route_km": 62.0, "eta": "50 - 65 mins", "mode": "Tol Surabaya-Mojokerto (Tol Sumo Seksi IV)", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 2 | Gerbangkertosusila & Tol Trans-Jawa", "wave": "Wave 1 | Gerbangkertosusila Corridor"},
    "MTL006": {"route_km": 68.5, "eta": "55 - 70 mins", "mode": "Tol Gempol-Pasuruan (GT Rembang Pier)", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 2 | Gerbangkertosusila & Tol Trans-Jawa", "wave": "Wave 2 | East Java Coastal Corridor"},
    "MTL007": {"route_km": 108.0, "eta": "1.4 - 1.8 hrs", "mode": "Tol Paspro (Pasuruan-Probolinggo Timur)", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 2 | Gerbangkertosusila & Tol Trans-Jawa", "wave": "Wave 2 | East Java Coastal Corridor"},
    "MTL008": {"route_km": 86.0, "eta": "1.1 - 1.4 hrs", "mode": "Tol Pandaan-Malang (GT Singosari)", "hub": "Malang Regional Hub", "zone": "Zone 3 | Malang Raya & Southern Mountain", "wave": "Wave 3 | Malang Raya & Southern Mountain"},
    "MTL009": {"route_km": 104.0, "eta": "1.8 - 2.3 hrs", "mode": "Tol Malang ➔ Karangploso ➔ Kota Wisata Batu (850m)", "hub": "Malang Regional Hub", "zone": "Zone 3 | Malang Raya & Southern Mountain", "wave": "Wave 3 | Malang Raya & Southern Mountain"},
    "MTL010": {"route_km": 128.0, "eta": "1.8 - 2.4 hrs", "mode": "Tol Jombang ➔ Kertosono ➔ Jalan Nasional Kediri", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 3 | Central East Java", "wave": "Wave 3 | Central East Java"},
    "MTL011": {"route_km": 155.0, "eta": "1.8 - 2.2 hrs", "mode": "Tol Kertosono-Ngawi (GT Caruban Madiun)", "hub": "Solo Regional Hub", "zone": "Zone 2 | Gerbangkertosusila & Tol Trans-Jawa", "wave": "Wave 2 | Trans-Jawa Backbone"},
    "MTL012": {"route_km": 84.0, "eta": "1.1 - 1.4 hrs", "mode": "Tol Sumo-Kertosono (GT Jombang Tembelang)", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 2 | Gerbangkertosusila & Tol Trans-Jawa", "wave": "Wave 2 | Trans-Jawa Backbone"},
    "MTL013": {"route_km": 102.0, "eta": "2.0 - 2.5 hrs", "mode": "Jalur Pantura Daendels Gresik-Tuban", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 2 | East Java Coastal Corridor", "wave": "Wave 2 | East Java Coastal Corridor"},
    "MTL014": {"route_km": 74.0, "eta": "1.4 - 1.8 hrs", "mode": "Jalur Arteri Surabaya-Lamongan-Babat", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 2 | East Java Coastal Corridor", "wave": "Wave 2 | East Java Coastal Corridor"},
    "MTL015": {"route_km": 295.0, "eta": "4.8 - 5.8 hrs", "mode": "Tol Paspro ➔ Jalur Pantura Situbondo-Ketapang", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 4 | Tapal Kuda & Bali Strait", "wave": "Wave 4 | Tapal Kuda & Bali Strait"},
    "MTL016": {"route_km": 205.0, "eta": "3.8 - 4.8 hrs", "mode": "Tol Probolinggo ➔ Klakah ➔ Jalan Nasional Jember", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 4 | Tapal Kuda & Bali Strait", "wave": "Wave 4 | Tapal Kuda & Bali Strait"},
    "MTL017": {"route_km": 118.0, "eta": "2.2 - 2.8 hrs", "mode": "Jalur Babat-Bojonegoro-Cepu Energy Basin", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 3 | Central East Java", "wave": "Wave 3 | Central East Java"},
    "MTL018": {"route_km": 18.5, "eta": "25 - 35 mins", "mode": "Jembatan Nasional Suramadu ➔ Akses Bangkalan", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 5 | Madura Island Enclave", "wave": "Wave 5 | Madura Island Enclave"},
    "MTL019": {"route_km": 86.0, "eta": "1.8 - 2.3 hrs", "mode": "Suramadu ➔ Jalur Lintas Selatan Madura Sampang", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 5 | Madura Island Enclave", "wave": "Wave 5 | Madura Island Enclave"},
    "MTL020": {"route_km": 156.0, "eta": "3.5 - 4.5 hrs", "mode": "Jalur Trans-Madura Timur ➔ Pelabuhan Kalianget", "hub": "Surabaya Central Logistics Hub", "zone": "Zone 5 | Madura Island Enclave", "wave": "Wave 5 | Madura Island Enclave"},
    "MTL021": {"route_km": 348.0, "eta": "3.8 - 4.5 hrs", "mode": "Tol Trans-Jawa (Surabaya-Solo-Semarang) ➔ Pelabuhan", "hub": "Semarang Forward Hub", "zone": "Zone 6 | Central Java Metropolitan Core", "wave": "Wave 2 | Central Java Corridors"},
    "MTL022": {"route_km": 352.0, "eta": "3.9 - 4.6 hrs", "mode": "Tol Trans-Jawa ➔ GT Gayamsari ➔ Simpang Lima", "hub": "Semarang Forward Hub", "zone": "Zone 6 | Central Java Metropolitan Core", "wave": "Wave 2 | Central Java Corridors"},
    "MTL023": {"route_km": 258.0, "eta": "2.8 - 3.4 hrs", "mode": "Tol Ngawi-Kertosono ➔ Tol Solo-Ngawi (GT Solo)", "hub": "Solo Regional Hub", "zone": "Zone 7 | Solo Raya & Yogyakarta Corridor", "wave": "Wave 2 | Central Java Corridors"},
    "MTL024": {"route_km": 282.0, "eta": "3.0 - 3.6 hrs", "mode": "Tol Solo-Semarang (GT Boyolali Rest Area)", "hub": "Solo Regional Hub", "zone": "Zone 7 | Solo Raya & Yogyakarta Corridor", "wave": "Wave 2 | Central Java Corridors"},
    "MTL025": {"route_km": 292.0, "eta": "3.5 - 4.2 hrs", "mode": "Tol Solo ➔ Jalur Arteri Solo-Klaten-Prambanan", "hub": "Solo Regional Hub", "zone": "Zone 7 | Solo Raya & Yogyakarta Corridor", "wave": "Wave 3 | Central Java Heritage Corridors"},
    "MTL026": {"route_km": 338.0, "eta": "4.2 - 5.0 hrs", "mode": "Tol Solo-Semarang ➔ Bawen ➔ Arteri Borobudur", "hub": "Solo Regional Hub", "zone": "Zone 7 | Solo Raya & Yogyakarta Corridor", "wave": "Wave 3 | Central Java Heritage Corridors"},
    "MTL027": {"route_km": 305.0, "eta": "3.2 - 3.8 hrs", "mode": "Tol Solo-Semarang (Panorama GT Salatiga)", "hub": "Semarang Forward Hub", "zone": "Zone 6 | Central Java Metropolitan Core", "wave": "Wave 2 | Central Java Corridors"},
    "MTL028": {"route_km": 328.0, "eta": "4.2 - 5.0 hrs", "mode": "Tol Trans-Jawa ➔ Grobogan / Jalur Pantura Kudus", "hub": "Semarang Forward Hub", "zone": "Zone 8 | Central Java Pantura Timur", "wave": "Wave 3 | Pantura Timur Corridor"},
    "MTL029": {"route_km": 335.0, "eta": "4.0 - 4.8 hrs", "mode": "Tol Tanggul Laut Semarang-Demak Sayung", "hub": "Semarang Forward Hub", "zone": "Zone 8 | Central Java Pantura Timur", "wave": "Wave 3 | Pantura Timur Corridor"},
    "MTL030": {"route_km": 442.0, "eta": "4.8 - 5.6 hrs", "mode": "Tol Batang-Semarang ➔ Tol Pemalang-Batang", "hub": "Semarang Forward Hub", "zone": "Zone 9 | Central Java Pantura Barat", "wave": "Wave 4 | Western Central Java Outliers"},
    "MTL031": {"route_km": 508.0, "eta": "5.5 - 6.4 hrs", "mode": "Tol Pejagan-Pemalang (GT Tegal Timur)", "hub": "Semarang Forward Hub", "zone": "Zone 9 | Central Java Pantura Barat", "wave": "Wave 4 | Western Central Java Outliers"},
    "MTL032": {"route_km": 425.0, "eta": "5.8 - 7.0 hrs", "mode": "Tol Pejagan ➔ Bumiayu ➔ Lereng Gunung Slamet 650m", "hub": "Semarang Forward Hub", "zone": "Zone 10 | Banyumas Highlands & Pansela", "wave": "Wave 4 | Western Central Java Outliers"},
    "MTL033": {"route_km": 455.0, "eta": "6.2 - 7.5 hrs", "mode": "Tol Solo ➔ Yogyakarta ➔ Daendels Pansela Cilacap", "hub": "Solo Regional Hub", "zone": "Zone 10 | Banyumas Highlands & Pansela", "wave": "Wave 4 | Western Central Java Outliers"},
    "MTL034": {"route_km": 385.0, "eta": "5.5 - 6.8 hrs", "mode": "Tol Bawen ➔ Secang ➔ Tanjakan Dieng Plateau 2,050m", "hub": "Semarang Forward Hub", "zone": "Zone 10 | Banyumas Highlands & Pansela", "wave": "Wave 4 | Western Central Java Outliers"},
    "MTL035": {"route_km": 375.0, "eta": "5.0 - 6.2 hrs", "mode": "Tol Solo ➔ Jalur Pansela Daendels Kebumen", "hub": "Solo Regional Hub", "zone": "Zone 10 | Banyumas Highlands & Pansela", "wave": "Wave 4 | Western Central Java Outliers"}
}


# ==========================================
# 3. IOH: KALIMANTAN & IKN CORRIDOR (20 SITES)
# ==========================================
IOH_SITES_RAW: List[Dict[str, Any]] = [
    # Kalimantan Timur & IKN Nusantara (9 Sites)
    {"no": 126, "site_id": "IOH001", "site_name": "IOH Balikpapan Semayang Gateway", "district": "Kota Balikpapan", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 116.8220, "lat": -1.2680, "notes": "Semayang Harbor Marine Gateway", "operator": "IOH", "paas_status": "🟢 Handover IOH"},
    {"no": 127, "site_id": "IOH002", "site_name": "IOH Balikpapan Sudirman Metro", "district": "Kota Balikpapan", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 116.8390, "lat": -1.2610, "notes": "Balikpapan Oil CBD Hub", "operator": "IOH", "paas_status": "🟢 Handover IOH"},
    {"no": 128, "site_id": "IOH003", "site_name": "IOH IKN Nusantara Core Sepaku", "district": "Penajam Paser Utara", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 5.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 116.7110, "lat": -0.9720, "notes": "IKN Central Government Core (KIPP)", "operator": "IOH", "paas_status": "🟢 Handover IOH"},
    {"no": 129, "site_id": "IOH004", "site_name": "IOH Samarinda Mahakam Gateway", "district": "Kota Samarinda", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 117.1350, "lat": -0.5120, "notes": "Jembatan Mahakam Trans-River", "operator": "IOH", "paas_status": "🟢 Handover IOH"},
    {"no": 130, "site_id": "IOH005", "site_name": "IOH Samarinda Kota Lembuswana", "district": "Kota Samarinda", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Gold", "quadrant": "Q2-High", "has_dg": "DG", "program": "IOH PaaS", "lon": 117.1480, "lat": -0.4850, "notes": "Samarinda Capital Commercial Center", "operator": "IOH", "paas_status": "🟣 Power I&C Active"},
    {"no": 131, "site_id": "IOH006", "site_name": "IOH IKN Glamping Western Ridge", "district": "Penajam Paser Utara", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 116.6950, "lat": -0.9550, "notes": "IKN Glamping & Eco-Tourism Node", "operator": "IOH", "paas_status": "🟣 Power I&C Active"},
    {"no": 132, "site_id": "IOH007", "site_name": "IOH Tenggarong Kutai Hub", "district": "Kutai Kartanegara", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "IOH PaaS", "lon": 116.9880, "lat": -0.4320, "notes": "Mahakam Royal Kingdom Corridor", "operator": "IOH", "paas_status": "🟣 Power I&C Active"},
    {"no": 133, "site_id": "IOH008", "site_name": "IOH Bontang PKT Petrochemical", "district": "Kota Bontang", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 117.4850, "lat": 0.1380, "notes": "Pupuk Kaltim Industrial Complex", "operator": "IOH", "paas_status": "🟣 Power I&C Active"},
    {"no": 134, "site_id": "IOH009", "site_name": "IOH Sangatta Kutai Timur", "district": "Kutai Timur", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "IOH PaaS", "lon": 117.5620, "lat": 0.4890, "notes": "KPC Coal Basin Energy Corridor", "operator": "IOH", "paas_status": "🟣 Power I&C Active"},

    # Kalimantan Selatan (4 Sites)
    {"no": 135, "site_id": "IOH010", "site_name": "IOH Banjarmasin Trisakti Port", "district": "Kota Banjarmasin", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "DG", "program": "IOH PaaS", "lon": 114.5680, "lat": -3.3280, "notes": "Barito River Maritime Gateway", "operator": "IOH", "paas_status": "🟡 Testing & QA"},
    {"no": 136, "site_id": "IOH011", "site_name": "IOH Banjarbaru Airport Hub", "district": "Kota Banjarbaru", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "IOH PaaS", "lon": 114.7450, "lat": -3.4420, "notes": "Bandara Syamsudin Noor Gateway", "operator": "IOH", "paas_status": "🟡 Testing & QA"},
    {"no": 137, "site_id": "IOH012", "site_name": "IOH Martapura Diamond Node", "district": "Banjar", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 114.8550, "lat": -3.4180, "notes": "Kota Intan Cultural Hub", "operator": "IOH", "paas_status": "🟡 Testing & QA"},
    {"no": 138, "site_id": "IOH013", "site_name": "IOH Batulicin Coastal Port", "district": "Tanah Bumbu", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "IOH PaaS", "lon": 115.9850, "lat": -3.4550, "notes": "Selat Sebuku Marine Crossing", "operator": "IOH", "paas_status": "⚪ Staged / Delivery Ready"},

    # Kalimantan Barat (3 Sites)
    {"no": 139, "site_id": "IOH014", "site_name": "IOH Pontianak Dwikora Port", "district": "Kota Pontianak", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 109.3380, "lat": -0.0240, "notes": "Sungai Kapuas Equator Center", "operator": "IOH", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 140, "site_id": "IOH015", "site_name": "IOH Singkawang Coastal Gate", "district": "Kota Singkawang", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "IOH PaaS", "lon": 108.9880, "lat": 0.9080, "notes": "Kota Amoy Coastal Corridor", "operator": "IOH", "paas_status": "⚪ Staged / Delivery Ready"},
    {"no": 141, "site_id": "IOH016", "site_name": "IOH Ketapang Sukabangun Port", "district": "Ketapang", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "DG", "program": "IOH PaaS", "lon": 109.9650, "lat": -1.8420, "notes": "Selat Karimata Maritime Relay", "operator": "IOH", "paas_status": "⚪ Staged / Regional Hub"},

    # Kalimantan Tengah (3 Sites)
    {"no": 142, "site_id": "IOH017", "site_name": "IOH Palangka Raya Bundaran", "district": "Kota Palangka Raya", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "IOH PaaS", "lon": 113.9180, "lat": -2.2150, "notes": "Bundaran Besar Central Park", "operator": "IOH", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 143, "site_id": "IOH018", "site_name": "IOH Sampit Kotawaringin", "district": "Kotawaringin Timur", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "IOH PaaS", "lon": 112.9550, "lat": -2.5350, "notes": "Sungai Mentaya Trade Hub", "operator": "IOH", "paas_status": "⚪ Staged / Regional Hub"},
    {"no": 144, "site_id": "IOH019", "site_name": "IOH Pangkalan Bun Port Kumai", "district": "Kotawaringin Barat", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q2-High", "has_dg": "DG", "program": "IOH PaaS", "lon": 111.7350, "lat": -2.6850, "notes": "Tanjung Puting National Park Hub", "operator": "IOH", "paas_status": "Shipping & Customs"},

    # Kalimantan Utara (1 Site)
    {"no": 145, "site_id": "IOH020", "site_name": "IOH Tarakan Juwata Terminal", "district": "Kota Tarakan", "site_type": "Backbone", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "IOH PaaS", "lon": 117.5850, "lat": 3.3280, "notes": "Pulau Tarakan Border Marine Hub", "operator": "IOH", "paas_status": "Shipping & Customs"},
]

GOOGLE_MAPS_ROUTING_SEMAYANG: Dict[str, Dict[str, Any]] = {
    "IOH001": {"route_km": 1.8, "eta": "5 - 8 mins", "mode": "Jl. Yos Sudarso & Pelabuhan Semayang Gate", "hub": "Balikpapan Central Logistics Hub", "zone": "Zone 1 | Balikpapan Coastal Core", "wave": "Wave 1 | Balikpapan & IKN Core"},
    "IOH002": {"route_km": 5.2, "eta": "12 - 18 mins", "mode": "Jl. Jenderal Sudirman Balikpapan CBD", "hub": "Balikpapan Central Logistics Hub", "zone": "Zone 1 | Balikpapan Coastal Core", "wave": "Wave 1 | Balikpapan & IKN Core"},
    "IOH003": {"route_km": 58.0, "eta": "55 - 70 mins", "mode": "Tol IKN (Seksi 3A/3B) & Jembatan Pulau Balang", "hub": "IKN Nusantara Central Hub", "zone": "Zone 2 | IKN Nusantara Government Core", "wave": "Wave 1 | Balikpapan & IKN Core"},
    "IOH004": {"route_km": 112.0, "eta": "1.4 - 1.8 hrs", "mode": "Jalan Tol Balsam (Balikpapan-Samarinda)", "hub": "Samarinda Forward Hub", "zone": "Zone 3 | Mahakam River & East Coast", "wave": "Wave 2 | Samarinda & Mahakam Basin"},
    "IOH005": {"route_km": 124.0, "eta": "1.6 - 2.0 hrs", "mode": "Tol Balsam ➔ Palaran ➔ Samarinda Kota Lembuswana", "hub": "Samarinda Forward Hub", "zone": "Zone 3 | Mahakam River & East Coast", "wave": "Wave 2 | Samarinda & Mahakam Basin"},
    "IOH006": {"route_km": 65.0, "eta": "1.1 - 1.4 hrs", "mode": "Tol IKN ➔ Samboja Barat ➔ Glamping Sepaku 4x4", "hub": "IKN Nusantara Central Hub", "zone": "Zone 2 | IKN Nusantara Government Core", "wave": "Wave 1 | Balikpapan & IKN Core"},
    "IOH007": {"route_km": 142.0, "eta": "2.0 - 2.5 hrs", "mode": "Tol Balsam ➔ Jembatan Kutai Kartanegara Tenggarong", "hub": "Samarinda Forward Hub", "zone": "Zone 3 | Mahakam River & East Coast", "wave": "Wave 2 | Samarinda & Mahakam Basin"},
    "IOH008": {"route_km": 235.0, "eta": "4.2 - 5.0 hrs", "mode": "Tol Balsam ➔ Jl. Poros Samarinda-Bontang (Petrochemical)", "hub": "Samarinda Forward Hub", "zone": "Zone 3 | Mahakam River & East Coast", "wave": "Wave 2 | Samarinda & Mahakam Basin"},
    "IOH009": {"route_km": 298.0, "eta": "5.8 - 6.8 hrs", "mode": "Jalan Poros Bontang-Sangatta KPC Coal Basin", "hub": "Samarinda Forward Hub", "zone": "Zone 3 | Mahakam River & East Coast", "wave": "Wave 3 | Northern Resource Corridors"},
    "IOH010": {"route_km": 492.0, "eta": "11 - 13 hrs", "mode": "Trans-Kalimantan Lintas Selatan (Kuaro-Batu Licin)", "hub": "Banjarmasin Regional Hub", "zone": "Zone 4 | South Kalimantan Industrial Basin", "wave": "Wave 3 | South Kalimantan Industrial Basin"},
    "IOH011": {"route_km": 475.0, "eta": "10.5 - 12.5 hrs", "mode": "Trans-Kalimantan ➔ Syamsudin Noor Banjarbaru", "hub": "Banjarmasin Regional Hub", "zone": "Zone 4 | South Kalimantan Industrial Basin", "wave": "Wave 3 | South Kalimantan Industrial Basin"},
    "IOH012": {"route_km": 468.0, "eta": "10 - 12 hrs", "mode": "Trans-Kalimantan ➔ Martapura Diamond Center", "hub": "Banjarmasin Regional Hub", "zone": "Zone 4 | South Kalimantan Industrial Basin", "wave": "Wave 3 | South Kalimantan Industrial Basin"},
    "IOH013": {"route_km": 320.0, "eta": "7.5 - 9.0 hrs", "mode": "Trans-Kalimantan Lintas Timur Tanah Bumbu", "hub": "Banjarmasin Regional Hub", "zone": "Zone 4 | South Kalimantan Industrial Basin", "wave": "Wave 3 | South Kalimantan Industrial Basin"},
    "IOH014": {"route_km": 1180.0, "eta": "24 - 28 hrs (Overland / Air Cargo)", "mode": "Trans-Kalimantan Poros Tengah (Sungai Kapuas)", "hub": "Pontianak Regional Hub", "zone": "Zone 5 | West Kalimantan Trans-Corridor", "wave": "Wave 4 | West Kalimantan & Border"},
    "IOH015": {"route_km": 1325.0, "eta": "27 - 31 hrs", "mode": "Trans-Kalimantan Lintas Barat Pontianak-Singkawang", "hub": "Pontianak Regional Hub", "zone": "Zone 5 | West Kalimantan Trans-Corridor", "wave": "Wave 4 | West Kalimantan & Border"},
    "IOH016": {"route_km": 960.0, "eta": "20 - 23 hrs", "mode": "Trans-Kalimantan Poros Selatan Ketapang Port", "hub": "Pontianak Regional Hub", "zone": "Zone 5 | West Kalimantan Trans-Corridor", "wave": "Wave 4 | West Kalimantan & Border"},
    "IOH017": {"route_km": 685.0, "eta": "14 - 16 hrs", "mode": "Trans-Kalimantan Poros Tengah Palangka Raya", "hub": "Banjarmasin Regional Hub", "zone": "Zone 6 | Central Kalimantan River Basin", "wave": "Wave 4 | Central & West Expansion"},
    "IOH018": {"route_km": 895.0, "eta": "18 - 21 hrs", "mode": "Jalan Trans-Kalteng Sampit Kotawaringin", "hub": "Banjarmasin Regional Hub", "zone": "Zone 6 | Central Kalimantan River Basin", "wave": "Wave 4 | Central & West Expansion"},
    "IOH019": {"route_km": 1045.0, "eta": "21 - 24 hrs", "mode": "Jalan Trans-Kalteng Barat Pangkalan Bun Kumai", "hub": "Banjarmasin Regional Hub", "zone": "Zone 6 | Central Kalimantan River Basin", "wave": "Wave 4 | Central & West Expansion"},
    "IOH020": {"route_km": 710.0, "eta": "16 - 19 hrs (Overland + Ro-Ro Ferry)", "mode": "Overland ke Tanjung Selor (590 km) + Feri Ro-Ro Tarakan (120 km)", "hub": "Samarinda Forward Hub", "zone": "Zone 7 | North Kalimantan Frontier", "wave": "Wave 5 | Frontier Enclave Island"}
}


# ==========================================
# ROUTING COMPUTATION ENGINES
# ==========================================
def compute_xlsmart_sumatra_routing(site: Dict[str, Any]) -> Dict[str, Any]:
    """Computes routing from Pelabuhan Belawan (Medan) for XLSmart Sumut & Aceh."""
    lat, lon, site_id = site["lat"], site["lon"], site["site_id"]
    h_dist = calculate_haversine_km(BELAWAN_PORT_COORDS[0], BELAWAN_PORT_COORDS[1], lat, lon)
    info = GOOGLE_MAPS_ROUTING_BELAWAN.get(site_id, {})
    return _enrich_site(site, h_dist, info, "Belawan")

def compute_mitratel_java_routing(site: Dict[str, Any]) -> Dict[str, Any]:
    """Computes routing from Pelabuhan Tanjung Perak (Surabaya) for Mitratel Jatim & Jateng."""
    lat, lon, site_id = site["lat"], site["lon"], site["site_id"]
    h_dist = calculate_haversine_km(TANJUNG_PERAK_COORDS[0], TANJUNG_PERAK_COORDS[1], lat, lon)
    info = GOOGLE_MAPS_ROUTING_PERAK.get(site_id, {})
    return _enrich_site(site, h_dist, info, "Tanjung Perak")

def compute_ioh_kalimantan_routing(site: Dict[str, Any]) -> Dict[str, Any]:
    """Computes routing from Pelabuhan Semayang (Balikpapan) for IOH Kalimantan & IKN."""
    lat, lon, site_id = site["lat"], site["lon"], site["site_id"]
    h_dist = calculate_haversine_km(BALIKPAPAN_PORT_COORDS[0], BALIKPAPAN_PORT_COORDS[1], lat, lon)
    info = GOOGLE_MAPS_ROUTING_SEMAYANG.get(site_id, {})
    return _enrich_site(site, h_dist, info, "Semayang")

def _enrich_site(site: Dict[str, Any], h_dist: float, info: Dict[str, Any], origin_name: str) -> Dict[str, Any]:
    route_dist = info.get("route_km", round(h_dist * 1.35, 1))
    mode = info.get("mode", f"Jalan Nasional dari Pelabuhan {origin_name}")
    est_time = info.get("eta", f"{round(route_dist / 45.0, 1)} hrs")
    hub = info.get("hub", f"Central Hub {origin_name}")
    zone = info.get("zone", "Regional Corridor")
    wave = info.get("wave", "Wave 2 | Regional Rollout")

    q_map = {"Q1-Critical": 4.0, "Q2-High": 3.0, "Q3-Modernized-Monitor": 2.0, "Q4-LowPriority": 1.0}
    c_score = q_map.get(site["quadrant"], 2.0)
    rev_map = {"Diamond": 4.0, "Platinum": 3.0, "Gold": 2.0, "Silver": 1.5, "Bronze": 1.0}
    r_score = rev_map.get(site["revenue_tier"], 2.0)
    bk = site["backup_hours"]
    b_score = 4.0 if bk == 0.0 else (3.0 if bk <= 1.0 else (2.0 if bk <= 3.0 else 1.0))
    dg_score = 3.0 if site["has_dg"] == "No DG" else 1.0

    is_ext = 1 if (
        site["district"] in ["Sabang", "Nias", "Karo", "Aceh Tengah", "Wonosobo", "Batu", "Kota Tarakan"]
        or "Mountain" in site["site_name"]
        or "Ferry" in site["site_name"]
        or "Plateau" in site["site_name"]
    ) else 0
    ext_bonus = 0.5 if is_ext else 0.0

    p_idx = round(0.45 * c_score + 0.20 * r_score + 0.20 * b_score + 0.15 * dg_score + ext_bonus, 2)
    tier = "Tier 1 - Immediate Modernization" if p_idx >= 3.0 else ("Tier 2 - Planned Upgrade" if p_idx >= 2.3 else "Tier 3 - Standard Cycle")

    status = site["paas_status"]
    if "Handover" in status:
        gate = "G5 - Handover [GO]"
    elif "Testing" in status:
        gate = "G4 - Acceptance Testing [GO]"
    elif "Power" in status:
        gate = "G3 - Power I&C [GO]"
    elif "Staged" in status:
        gate = "G1 - Material Staged [GO]"
    else:
        gate = "G0 - Port Berth & Inbound [HOLD]"

    enriched = dict(site)
    enriched.update({
        "haversine_distance_km": h_dist,
        "accessible_route_km": route_dist,
        "transport_mode": mode,
        "est_travel_time": est_time,
        "assigned_forward_hub": hub,
        "deployment_zone": zone,
        "delivery_wave": wave,
        "priority_index": p_idx,
        "priority_tier": tier,
        "readiness_gate": gate,
        "is_extreme": is_ext
    })
    return enriched


def seed_multi_tenant_sites(db_path: str = None) -> None:
    """
    Seeds sites for all tenant operators:
    - Telkomcel (100) strictly in Timor-Leste
    - XLSmart (25) in Sumatera Utara & Aceh
    - Mitratel (35) in Jawa Timur & Jawa Tengah
    - IOH (20) in Kalimantan & IKN
    Total = 180 nationwide sites.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # 1. Ensure Telkomcel 100 baseline sites are present
    cursor.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE operator = 'Telkomcel'")
    t_count = cursor.fetchone()[0]
    if t_count == 0:
        seed_timor_100_sites(db_path)
        
    # 2. Check if Mitratel is in Jatim/Jateng and IOH in Kalimantan
    cursor.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE operator = 'Mitratel' AND district IN ('Surabaya', 'Semarang')")
    mtl_java = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE operator = 'IOH' AND district IN ('Kota Balikpapan', 'Kota Samarinda')")
    ioh_kal = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE operator != 'Telkomcel'")
    other_count = cursor.fetchone()[0]

    if other_count >= 80:
        conn.close()
        return # Already fully seeded with correct regional multi-tenant distribution — NEVER delete user data!
    
    # 4. Enrich and insert all other tenant sites
    processed_xl = [compute_xlsmart_sumatra_routing(s) for s in XLSMART_SITES_RAW]
    processed_mtl = [compute_mitratel_java_routing(s) for s in MITRATEL_SITES_RAW]
    processed_ioh = [compute_ioh_kalimantan_routing(s) for s in IOH_SITES_RAW]
    
    df_other = pd.DataFrame(processed_xl + processed_mtl + processed_ioh)
    
    cols = [
        "no", "site_id", "site_name", "district", "site_type", "rectifier", "backup_hours",
        "revenue_tier", "quadrant", "has_dg", "program", "lon", "lat", "notes",
        "haversine_distance_km", "accessible_route_km", "transport_mode", "est_travel_time",
        "assigned_forward_hub", "deployment_zone", "delivery_wave", "priority_index",
        "priority_tier", "readiness_gate", "paas_status", "operator", "is_extreme"
    ]
    
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO timor_sites_100 ({', '.join(cols)}) VALUES ({placeholders})"
    
    rows = []
    for _, r in df_other.iterrows():
        rows.append(tuple(r[c] for c in cols))
        
    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()


def get_all_tenant_sites_dataframe() -> pd.DataFrame:
    """Returns combined dataframe of all 180 multi-tenant sites."""
    from database.timor_sites_data import get_timor_100_sites_dataframe
    df_telkomcel = get_timor_100_sites_dataframe()
    processed_xl = [compute_xlsmart_sumatra_routing(s) for s in XLSMART_SITES_RAW]
    processed_mtl = [compute_mitratel_java_routing(s) for s in MITRATEL_SITES_RAW]
    processed_ioh = [compute_ioh_kalimantan_routing(s) for s in IOH_SITES_RAW]
    df_other = pd.DataFrame(processed_xl + processed_mtl + processed_ioh)
    return pd.concat([df_telkomcel, df_other], ignore_index=True)
