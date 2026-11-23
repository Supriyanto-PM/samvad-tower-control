"""
Timor-Leste 101-Site National Rollout Dataset & Operational Routing Engine.
Accurately encodes all 101 telecom tower sites from Samvad_101_Site_Load_Final.xlsx.
Computes accessible route distance from Port Dili (Lat: -8.5520, Long: 125.5711),
travel time, transport mode, deployment zones, forward hubs, delivery waves, P0-P3 Priority Index,
and full DC/AC electrical load profile (343.41 kW DC, 392.23 kW AC, 412.82 kVA, 8,241.2 kWh/day).
"""
import math
from typing import List, Dict, Any, Tuple
import pandas as pd
from database.connection import get_connection, execute_write

PORT_DILI_COORDS = (-8.5520, 125.5711) # VCU004 Dili Port Terminal

# 101-Site Baseline Data from Samvad_101_Site_Load_Final.xlsx
TIMOR_100_SITES_RAW: List[Dict[str, Any]] = [
    {'no': 1, 'site_id': 'DAX001', 'site_name': 'Fomento 1', 'district': 'Dili', 'site_type': 'Sub Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 85.6, 'load_dc_kw': 4.58, 'energy_kwh_day': 109.9, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.09, 'load_ac_total_kw': 5.09, 'load_ac_kva': 5.36, 'backup_hours': 1.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5382, 'lat': -8.5621, 'notes': None},
    {'no': 2, 'site_id': 'CRE009', 'site_name': 'Kuluhun de Baixo', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 92.2, 'load_dc_kw': 4.93, 'energy_kwh_day': 118.3, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.48, 'load_ac_total_kw': 5.48, 'load_ac_kva': 5.77, 'backup_hours': 0.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5895, 'lat': -8.5551, 'notes': None},
    {'no': 3, 'site_id': 'DAX024', 'site_name': 'Kampung Baru Dili', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 69.3, 'load_dc_kw': 3.71, 'energy_kwh_day': 89.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.12, 'load_ac_total_kw': 4.12, 'load_ac_kva': 4.34, 'backup_hours': 0.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.527, 'lat': -8.56499, 'notes': None},
    {'no': 4, 'site_id': 'DAX016', 'site_name': 'Delta', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 93.7, 'load_dc_kw': 5.01, 'energy_kwh_day': 120.2, 'position': 'INDOOR', 'load_ac_recti_kw': 5.57, 'load_ac_total_kw': 7.07, 'load_ac_kva': 7.44, 'backup_hours': 2.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5395, 'lat': -8.5562, 'notes': None},
    {'no': 5, 'site_id': 'CRE008', 'site_name': 'Becusi Centru', 'district': 'Dili', 'site_type': 'Sub Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 67.4, 'load_dc_kw': 3.61, 'energy_kwh_day': 86.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.01, 'load_ac_total_kw': 4.01, 'load_ac_kva': 4.22, 'backup_hours': 2.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.596, 'lat': -8.5665, 'notes': None},
    {'no': 6, 'site_id': 'DAX004', 'site_name': 'Bebonuk', 'district': 'Dili', 'site_type': 'Sub Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 85.8, 'load_dc_kw': 4.59, 'energy_kwh_day': 110.2, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.1, 'load_ac_total_kw': 5.1, 'load_ac_kva': 5.37, 'backup_hours': 1.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5416, 'lat': -8.54704, 'notes': None},
    {'no': 7, 'site_id': 'DAX014', 'site_name': 'Kampung Alor', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 93.1, 'load_dc_kw': 4.98, 'energy_kwh_day': 119.5, 'position': 'INDOOR', 'load_ac_recti_kw': 5.53, 'load_ac_total_kw': 7.03, 'load_ac_kva': 7.4, 'backup_hours': 1.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5593, 'lat': -8.55058, 'notes': None},
    {'no': 8, 'site_id': 'NFE001', 'site_name': 'Lahane Oriental', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 93.2, 'load_dc_kw': 4.99, 'energy_kwh_day': 119.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.54, 'load_ac_total_kw': 5.54, 'load_ac_kva': 5.83, 'backup_hours': 2.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.584, 'lat': -8.5715, 'notes': None},
    {'no': 9, 'site_id': 'VCU004', 'site_name': 'Dili Port', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 82.5, 'load_dc_kw': 4.41, 'energy_kwh_day': 105.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.9, 'load_ac_total_kw': 4.9, 'load_ac_kva': 5.16, 'backup_hours': 0.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5711, 'lat': -8.552, 'notes': 'Port Dili Staging Origin'},
    {'no': 10, 'site_id': 'CRE018', 'site_name': 'Tubarai', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 91.6, 'load_dc_kw': 4.9, 'energy_kwh_day': 117.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.44, 'load_ac_total_kw': 5.44, 'load_ac_kva': 5.73, 'backup_hours': 5.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5919, 'lat': -8.56857, 'notes': None},
    {'no': 11, 'site_id': 'DAX005', 'site_name': 'Lurumata', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 86.7, 'load_dc_kw': 4.64, 'energy_kwh_day': 111.4, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.16, 'load_ac_total_kw': 5.16, 'load_ac_kva': 5.43, 'backup_hours': 1.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5501, 'lat': -8.5534, 'notes': None},
    {'no': 12, 'site_id': 'DAX007', 'site_name': 'Fatuhada', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 74.4, 'load_dc_kw': 3.98, 'energy_kwh_day': 95.5, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.42, 'load_ac_total_kw': 4.42, 'load_ac_kva': 4.65, 'backup_hours': 1.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5534, 'lat': -8.54756, 'notes': None},
    {'no': 13, 'site_id': 'DAX035', 'site_name': 'Ailok Laran', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 92.0, 'load_dc_kw': 4.92, 'energy_kwh_day': 118.1, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.47, 'load_ac_total_kw': 5.47, 'load_ac_kva': 5.76, 'backup_hours': 1.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.565, 'lat': -8.57249, 'notes': None},
    {'no': 14, 'site_id': 'DAX038', 'site_name': 'Pantai Kelapa 2', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 76.7, 'load_dc_kw': 4.1, 'energy_kwh_day': 98.4, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.56, 'load_ac_total_kw': 4.56, 'load_ac_kva': 4.8, 'backup_hours': 0.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5452, 'lat': -8.5464, 'notes': None},
    {'no': 15, 'site_id': 'NFE007', 'site_name': 'Quintal Boot', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 87.7, 'load_dc_kw': 4.69, 'energy_kwh_day': 112.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.21, 'load_ac_total_kw': 5.21, 'load_ac_kva': 5.48, 'backup_hours': 0.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5839, 'lat': -8.5637, 'notes': None},
    {'no': 16, 'site_id': 'DAX018', 'site_name': 'Beto', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 88.0, 'load_dc_kw': 4.71, 'energy_kwh_day': 113.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.23, 'load_ac_total_kw': 5.23, 'load_ac_kva': 5.51, 'backup_hours': 0.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5343, 'lat': -8.54883, 'notes': None},
    {'no': 17, 'site_id': 'VCU007', 'site_name': 'Vila Verde', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 86.3, 'load_dc_kw': 4.62, 'energy_kwh_day': 110.9, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.13, 'load_ac_total_kw': 5.13, 'load_ac_kva': 5.4, 'backup_hours': 1.0, 'revenue_tier': 'Platinum', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5678, 'lat': -8.56258, 'notes': None},
    {'no': 18, 'site_id': 'NFE008', 'site_name': 'Audian', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 90.6, 'load_dc_kw': 4.85, 'energy_kwh_day': 116.4, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.39, 'load_ac_total_kw': 5.39, 'load_ac_kva': 5.67, 'backup_hours': 0.0, 'revenue_tier': 'Gold', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5856, 'lat': -8.55817, 'notes': None},
    {'no': 19, 'site_id': 'DAX021', 'site_name': 'Delta 2', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 89.4, 'load_dc_kw': 4.78, 'energy_kwh_day': 114.7, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.31, 'load_ac_total_kw': 5.31, 'load_ac_kva': 5.59, 'backup_hours': 1.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5377, 'lat': -8.55679, 'notes': None},
    {'no': 20, 'site_id': 'DAX026', 'site_name': 'Hudilaran', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 85.8, 'load_dc_kw': 4.59, 'energy_kwh_day': 110.2, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.1, 'load_ac_total_kw': 5.1, 'load_ac_kva': 5.37, 'backup_hours': 1.0, 'revenue_tier': 'Gold', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5589, 'lat': -8.55603, 'notes': None},
    {'no': 21, 'site_id': 'CRE004', 'site_name': 'Bedois', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 82.5, 'load_dc_kw': 4.41, 'energy_kwh_day': 105.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.9, 'load_ac_total_kw': 4.9, 'load_ac_kva': 5.16, 'backup_hours': 0.0, 'revenue_tier': 'Gold', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.618, 'lat': -8.56449, 'notes': None},
    {'no': 22, 'site_id': 'VCU001', 'site_name': 'Palpaco', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 85.6, 'load_dc_kw': 4.58, 'energy_kwh_day': 109.9, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.09, 'load_ac_total_kw': 5.09, 'load_ac_kva': 5.36, 'backup_hours': 0.0, 'revenue_tier': 'Gold', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5658, 'lat': -8.55335, 'notes': None},
    {'no': 23, 'site_id': 'VCU002', 'site_name': 'Untl', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 79.8, 'load_dc_kw': 4.27, 'energy_kwh_day': 102.5, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.74, 'load_ac_total_kw': 4.74, 'load_ac_kva': 4.99, 'backup_hours': 0.5, 'revenue_tier': 'Gold', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5785, 'lat': -8.5557, 'notes': None},
    {'no': 24, 'site_id': 'CRE014', 'site_name': 'Aituri Laran', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.2, 'load_dc_kw': 2.95, 'energy_kwh_day': 70.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.28, 'load_ac_total_kw': 3.28, 'load_ac_kva': 3.45, 'backup_hours': 4.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.595, 'lat': -8.57868, 'notes': None},
    {'no': 25, 'site_id': 'NFE010', 'site_name': 'Lahane Ocidental', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 52.2, 'load_dc_kw': 2.79, 'energy_kwh_day': 67.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.1, 'load_ac_total_kw': 3.1, 'load_ac_kva': 3.26, 'backup_hours': 2.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5865, 'lat': -8.5769, 'notes': None},
    {'no': 26, 'site_id': 'DAX039', 'site_name': 'DIT Baya Leste', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 88.5, 'load_dc_kw': 4.73, 'energy_kwh_day': 113.5, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.26, 'load_ac_total_kw': 5.26, 'load_ac_kva': 5.54, 'backup_hours': 2.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5417, 'lat': -8.56795, 'notes': None},
    {'no': 27, 'site_id': 'CRE019', 'site_name': 'Bedois TT', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 88.5, 'load_dc_kw': 4.73, 'energy_kwh_day': 113.5, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.26, 'load_ac_total_kw': 5.26, 'load_ac_kva': 5.54, 'backup_hours': 2.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.6172, 'lat': -8.56757, 'notes': None},
    {'no': 28, 'site_id': 'CRE006', 'site_name': 'Hera', 'district': 'Dili', 'site_type': 'Hub Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 56.5, 'load_dc_kw': 3.02, 'energy_kwh_day': 72.5, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.36, 'load_ac_total_kw': 3.36, 'load_ac_kva': 3.54, 'backup_hours': 0.0, 'revenue_tier': 'Gold', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.665, 'lat': -8.53015, 'notes': None},
    {'no': 29, 'site_id': 'DAX046', 'site_name': 'UNPAZ', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 88.2, 'load_dc_kw': 4.72, 'energy_kwh_day': 113.3, 'position': 'ROOFTOP', 'load_ac_recti_kw': 5.24, 'load_ac_total_kw': 5.24, 'load_ac_kva': 5.52, 'backup_hours': 0.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5466, 'lat': -8.56471, 'notes': None},
    {'no': 30, 'site_id': 'CRE021', 'site_name': 'Becora Camea', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 71.5, 'load_dc_kw': 3.83, 'energy_kwh_day': 91.9, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.26, 'load_ac_total_kw': 4.26, 'load_ac_kva': 4.48, 'backup_hours': 2.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.6093, 'lat': -8.5619, 'notes': None},
    {'no': 31, 'site_id': 'VCU010', 'site_name': 'UNDIL', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 80.7, 'load_dc_kw': 4.32, 'energy_kwh_day': 103.7, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.8, 'load_ac_total_kw': 4.8, 'load_ac_kva': 5.05, 'backup_hours': 1.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5806, 'lat': -8.56251, 'notes': None},
    {'no': 32, 'site_id': 'DAX043', 'site_name': 'DELTA 3', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 85.0, 'load_dc_kw': 4.55, 'energy_kwh_day': 109.2, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.06, 'load_ac_total_kw': 5.06, 'load_ac_kva': 5.33, 'backup_hours': 2.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5419, 'lat': -8.55757, 'notes': None},
    {'no': 33, 'site_id': 'NFE004', 'site_name': 'Marabia', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 73.5, 'load_dc_kw': 3.93, 'energy_kwh_day': 94.3, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.37, 'load_ac_total_kw': 4.37, 'load_ac_kva': 4.6, 'backup_hours': 1.0, 'revenue_tier': 'Gold', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5751, 'lat': -8.57971, 'notes': None},
    {'no': 34, 'site_id': 'CRE022', 'site_name': 'Rooftop Unital', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 63.1, 'load_dc_kw': 3.38, 'energy_kwh_day': 81.1, 'position': 'ROOFTOP', 'load_ac_recti_kw': 3.76, 'load_ac_total_kw': 3.76, 'load_ac_kva': 3.96, 'backup_hours': 1.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.6065, 'lat': -8.56345, 'notes': None},
    {'no': 35, 'site_id': 'DAX015', 'site_name': 'TP Indoor', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 14.4, 'load_dc_kw': 0.77, 'energy_kwh_day': 18.5, 'position': 'INDOOR', 'load_ac_recti_kw': 0.86, 'load_ac_total_kw': 2.36, 'load_ac_kva': 2.48, 'backup_hours': 0.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5413, 'lat': -8.55368, 'notes': None},
    {'no': 36, 'site_id': 'CRE007', 'site_name': 'Balibar', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 57.0, 'load_dc_kw': 3.05, 'energy_kwh_day': 73.2, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.39, 'load_ac_total_kw': 3.39, 'load_ac_kva': 3.57, 'backup_hours': 5.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.6035, 'lat': -8.59804, 'notes': None},
    {'no': 37, 'site_id': 'VCU008', 'site_name': 'EWSD', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 91.2, 'load_dc_kw': 4.88, 'energy_kwh_day': 117.1, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.42, 'load_ac_total_kw': 5.42, 'load_ac_kva': 5.71, 'backup_hours': 1.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5791, 'lat': -8.55892, 'notes': None},
    {'no': 38, 'site_id': 'CRE011', 'site_name': 'Taibesi 2', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 86.2, 'load_dc_kw': 4.61, 'energy_kwh_day': 110.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.12, 'load_ac_total_kw': 5.12, 'load_ac_kva': 5.39, 'backup_hours': 1.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5976, 'lat': -8.56429, 'notes': None},
    {'no': 39, 'site_id': 'DAX022', 'site_name': 'Kampung Merdeka', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 96.1, 'load_dc_kw': 5.14, 'energy_kwh_day': 123.4, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.71, 'load_ac_total_kw': 5.71, 'load_ac_kva': 6.01, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5326, 'lat': -8.5582, 'notes': None},
    {'no': 40, 'site_id': 'MET003', 'site_name': 'Metinaro', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.756, 'lat': -8.53119, 'notes': None},
    {'no': 41, 'site_id': 'DAX051', 'site_name': 'BETO ROOFTOP', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 80.2, 'load_dc_kw': 4.29, 'energy_kwh_day': 103.0, 'position': 'ROOFTOP', 'load_ac_recti_kw': 4.77, 'load_ac_total_kw': 4.77, 'load_ac_kva': 5.02, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5317, 'lat': -8.54806, 'notes': None},
    {'no': 42, 'site_id': 'DAX045', 'site_name': 'Canossa', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 89.5, 'load_dc_kw': 4.79, 'energy_kwh_day': 115.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 5.32, 'load_ac_total_kw': 5.32, 'load_ac_kva': 5.6, 'backup_hours': 0.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.5354, 'lat': -8.57032, 'notes': None},
    {'no': 43, 'site_id': 'DAX047', 'site_name': 'Lidun 2', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 82.2, 'load_dc_kw': 4.4, 'energy_kwh_day': 105.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.89, 'load_ac_total_kw': 4.89, 'load_ac_kva': 5.15, 'backup_hours': 0.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5439, 'lat': -8.58439, 'notes': None},
    {'no': 44, 'site_id': 'VCU012', 'site_name': 'ROOFTOP_COLMERA', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 83.0, 'load_dc_kw': 4.44, 'energy_kwh_day': 106.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.93, 'load_ac_total_kw': 4.93, 'load_ac_kva': 5.19, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5723, 'lat': -8.55616, 'notes': None},
    {'no': 45, 'site_id': 'WAT002', 'site_name': 'Uatulari', 'district': 'Viqueque', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.5317, 'lat': -8.82022, 'notes': None},
    {'no': 46, 'site_id': 'DAX049', 'site_name': 'MASLIDUN', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 68.5, 'load_dc_kw': 3.66, 'energy_kwh_day': 87.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.07, 'load_ac_total_kw': 4.07, 'load_ac_kva': 4.28, 'backup_hours': 1.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5046, 'lat': -8.5666, 'notes': None},
    {'no': 47, 'site_id': 'PAN006', 'site_name': 'PADIAE', 'district': 'Oecusse', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 0.5, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 124.3521, 'lat': -9.255, 'notes': 'Enclave Ferry Access'},
    {'no': 48, 'site_id': 'CRE017', 'site_name': 'Hera Akanunu', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 60.7, 'load_dc_kw': 3.25, 'energy_kwh_day': 78.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.61, 'load_ac_total_kw': 3.61, 'load_ac_kva': 3.8, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.6731, 'lat': -8.54523, 'notes': None},
    {'no': 49, 'site_id': 'BAL001', 'site_name': 'Fatuklulik', 'district': 'Bobonaro', 'site_type': 'Backbone', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset+PV)', 'genset_avail': 'With Genset', 'load_dc_a': 70.0, 'load_dc_kw': 3.75, 'energy_kwh_day': 90.0, 'position': 'INDOOR', 'load_ac_recti_kw': 4.17, 'load_ac_total_kw': 5.67, 'load_ac_kva': 5.97, 'backup_hours': 1.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.0437, 'lat': -8.97317, 'notes': None},
    {'no': 50, 'site_id': 'DAX020', 'site_name': 'DIT Manleuana', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 64.7, 'load_dc_kw': 3.46, 'energy_kwh_day': 83.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.84, 'load_ac_total_kw': 3.84, 'load_ac_kva': 4.04, 'backup_hours': 0.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q2-High', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5447, 'lat': -8.56404, 'notes': None},
    {'no': 51, 'site_id': 'LOS009', 'site_name': 'SORO NAIRETE', 'district': 'Lautem', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q2-High', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.9659, 'lat': -8.51241, 'notes': None},
    {'no': 52, 'site_id': 'DAX034', 'site_name': 'Arbiruh Beach', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 42.9, 'load_dc_kw': 2.3, 'energy_kwh_day': 55.2, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.56, 'load_ac_total_kw': 2.56, 'load_ac_kva': 2.69, 'backup_hours': 0.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q2-High', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5383, 'lat': -8.54028, 'notes': None},
    {'no': 53, 'site_id': 'DAX010', 'site_name': 'TP Outdoor', 'district': 'Dili', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 98.7, 'load_dc_kw': 5.28, 'energy_kwh_day': 126.7, 'position': 'INDOOR', 'load_ac_recti_kw': 5.87, 'load_ac_total_kw': 7.37, 'load_ac_kva': 7.76, 'backup_hours': 0.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q2-High', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5413, 'lat': -8.55379, 'notes': None},
    {'no': 54, 'site_id': 'RAI001', 'site_name': 'Tokoluli', 'district': 'Ermera', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 70.0, 'load_dc_kw': 3.75, 'energy_kwh_day': 90.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.17, 'load_ac_total_kw': 4.17, 'load_ac_kva': 4.39, 'backup_hours': 3.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q4-LowPriority', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.4378, 'lat': -8.70246, 'notes': None},
    {'no': 55, 'site_id': 'BAZ005', 'site_name': 'Terlau', 'district': 'Liquisa', 'site_type': 'Sub Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 0.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.4539, 'lat': -8.63018, 'notes': None},
    {'no': 56, 'site_id': 'BAZ003', 'site_name': 'Leovenia', 'district': 'Liquisa', 'site_type': 'Sub Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset+PV)', 'genset_avail': 'With Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 0.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.3807, 'lat': -8.68415, 'notes': None},
    {'no': 57, 'site_id': 'VEM001', 'site_name': 'Naulale', 'district': 'Baucau', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.205, 'lat': -8.518, 'notes': None},
    {'no': 58, 'site_id': 'BAL003', 'site_name': 'Palaka', 'district': 'Bobonaro', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.061, 'lat': -8.932, 'notes': None},
    {'no': 59, 'site_id': 'BAZ007', 'site_name': 'Motaulun', 'district': 'Liquisa', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.412, 'lat': -8.582, 'notes': None},
    {'no': 60, 'site_id': 'NAT002', 'site_name': 'NATARBORA 2', 'district': 'Manatuto', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 4.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q2-High', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.0543, 'lat': -8.98082, 'notes': None},
    {'no': 61, 'site_id': 'SAM008', 'site_name': 'HOLARUA', 'district': 'Manufahi', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.642, 'lat': -8.968, 'notes': None},
    {'no': 62, 'site_id': 'MAN006', 'site_name': 'Iliheu', 'district': 'Manatuto', 'site_type': 'Hub Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 0.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.9531, 'lat': -8.53905, 'notes': None},
    {'no': 63, 'site_id': 'LAG002', 'site_name': 'Teki NauMata', 'district': 'Baucau', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 126.589, 'lat': -8.474, 'notes': None},
    {'no': 64, 'site_id': 'PAN003', 'site_name': 'Pantai Macassar', 'district': 'Oecusse', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'INDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 4.77, 'load_ac_kva': 5.02, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 124.3835, 'lat': -9.2015, 'notes': 'Enclave Ferry Access'},
    {'no': 65, 'site_id': 'LAG004', 'site_name': 'Quelicai', 'district': 'Baucau', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.559, 'lat': -8.601, 'notes': None},
    {'no': 66, 'site_id': 'LOS004', 'site_name': 'Kartini', 'district': 'Lautem', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.995, 'lat': -8.522, 'notes': None},
    {'no': 67, 'site_id': 'BAU005', 'site_name': 'Baucau Coast', 'district': 'Baucau', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.462, 'lat': -8.445, 'notes': None},
    {'no': 68, 'site_id': 'LAL002', 'site_name': 'Cairui', 'district': 'Manatuto', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.145, 'lat': -8.569, 'notes': None},
    {'no': 69, 'site_id': 'VIQ010', 'site_name': 'BIBLEO', 'district': 'Viqueque', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.378, 'lat': -8.875, 'notes': None},
    {'no': 70, 'site_id': 'BAU010', 'site_name': 'CAIBADA MAKASAE', 'district': 'Baucau', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Silver', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.445, 'lat': -8.463, 'notes': None},
    {'no': 71, 'site_id': 'SUA003', 'site_name': 'Suai Loro', 'district': 'Cova Lima', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 70.0, 'load_dc_kw': 3.75, 'energy_kwh_day': 90.0, 'position': 'OUTDOOR', 'load_ac_recti_kw': 4.17, 'load_ac_total_kw': 4.17, 'load_ac_kva': 4.39, 'backup_hours': 1.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q2-High', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.2789, 'lat': -9.3468, 'notes': None},
    {'no': 72, 'site_id': 'MAN005', 'site_name': 'Laclo Manatuto', 'district': 'Manatuto', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.912, 'lat': -8.554, 'notes': None},
    {'no': 73, 'site_id': 'ERM004', 'site_name': 'TALIMORO', 'district': 'Ermera', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.439, 'lat': -8.728, 'notes': None},
    {'no': 74, 'site_id': 'ERM002', 'site_name': 'Ermera Old Town', 'district': 'Ermera', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'INDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 4.77, 'load_ac_kva': 5.02, 'backup_hours': 4.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q2-High', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.4007, 'lat': -8.75003, 'notes': None},
    {'no': 75, 'site_id': 'BOB004', 'site_name': 'TAIMEA', 'district': 'Bobonaro', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.218, 'lat': -8.985, 'notes': 'Extreme Mountain Access'},
    {'no': 76, 'site_id': 'CAI001', 'site_name': 'Cailaco', 'district': 'Bobonaro', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.278, 'lat': -8.895, 'notes': 'Extreme Mountain Access'},
    {'no': 77, 'site_id': 'BOB002', 'site_name': 'Bobonaro', 'district': 'Bobonaro', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.325, 'lat': -9.032, 'notes': 'Extreme Mountain Access'},
    {'no': 78, 'site_id': 'NAT001', 'site_name': 'Natarbora', 'district': 'Manatuto', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.048, 'lat': -8.972, 'notes': None},
    {'no': 79, 'site_id': 'AIL004', 'site_name': 'Liurai', 'district': 'Aileu', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (Genset)', 'genset_avail': 'With Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.558, 'lat': -8.742, 'notes': 'Extreme Mountain Access'},
    {'no': 80, 'site_id': 'BAG002', 'site_name': 'Defause', 'district': 'Baucau', 'site_type': 'Sub Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 1.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.699, 'lat': -8.59689, 'notes': 'Extreme Coastal/Elevation'},
    {'no': 81, 'site_id': 'VIQ003', 'site_name': 'Adarai', 'district': 'Viqueque', 'site_type': 'Sub Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.565, 'lat': -8.812, 'notes': None},
    {'no': 82, 'site_id': 'LET003', 'site_name': 'Ducurai', 'district': 'Ermera', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'Abnormal grid', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 0.5, 'revenue_tier': 'Bronze', 'quadrant': 'Q1-Critical', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.4642, 'lat': -8.82378, 'notes': 'OFF GRID SITE | Extreme Mountain Spine'},
    {'no': 83, 'site_id': 'SUA011', 'site_name': 'Holpilat', 'district': 'Cova Lima', 'site_type': 'Hub Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.215, 'lat': -9.235, 'notes': None},
    {'no': 84, 'site_id': 'REM004', 'site_name': 'FAHISOI', 'district': 'Aileu', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.635, 'lat': -8.638, 'notes': 'Extreme Mountain Access'},
    {'no': 85, 'site_id': 'ILI003', 'site_name': 'Iliomar', 'district': 'Lautem', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.828, 'lat': -8.709, 'notes': None},
    {'no': 86, 'site_id': 'CAI002', 'site_name': 'Cailaco Purugua', 'district': 'Bobonaro', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.246, 'lat': -8.854, 'notes': 'Extreme Mountain Access'},
    {'no': 87, 'site_id': 'REM002', 'site_name': 'Remexio', 'district': 'Aileu', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.665, 'lat': -8.618, 'notes': 'Extreme Mountain Access'},
    {'no': 88, 'site_id': 'MAN007', 'site_name': 'Cribas', 'district': 'Manatuto', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.986, 'lat': -8.675, 'notes': None},
    {'no': 89, 'site_id': 'HAO002', 'site_name': 'Fatubolu', 'district': 'Ermera', 'site_type': 'Sub Site', 'rectifier': 'ELTEK', 'power_status': 'Backup available (Genset+PV)', 'genset_avail': 'With Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'DG', 'program': 'Samvad', 'lon': 125.335, 'lat': -8.798, 'notes': 'Extreme Mountain Access'},
    {'no': 90, 'site_id': 'LEQ001', 'site_name': 'Lequidoe', 'district': 'Aileu', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.642, 'lat': -8.698, 'notes': 'Extreme Mountain Access'},
    {'no': 91, 'site_id': 'ZUM002', 'site_name': 'ZUMALAI_VILLA', 'district': 'Cova Lima', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.451, 'lat': -9.158, 'notes': None},
    {'no': 92, 'site_id': 'LAT004', 'site_name': 'Luro', 'district': 'Lautem', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.832, 'lat': -8.543, 'notes': None},
    {'no': 93, 'site_id': 'SAM003', 'site_name': 'Betano', 'district': 'Manufahi', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.718, 'lat': -9.162, 'notes': None},
    {'no': 94, 'site_id': 'OSS004', 'site_name': 'WAIMORITULA', 'district': 'Viqueque', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 126.382, 'lat': -8.745, 'notes': None},
    {'no': 95, 'site_id': 'ATS001', 'site_name': 'Laclo', 'district': 'Ermera', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.398, 'lat': -8.912, 'notes': 'Extreme Mountain Access'},
    {'no': 96, 'site_id': 'LAB001', 'site_name': 'Laclubar', 'district': 'Manatuto', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.912, 'lat': -8.748, 'notes': None},
    {'no': 97, 'site_id': 'ZUM001', 'site_name': 'Beilaco', 'district': 'Cova Lima', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.468, 'lat': -9.195, 'notes': None},
    {'no': 98, 'site_id': 'SUA010', 'site_name': 'SANFUK', 'district': 'Cova Lima', 'site_type': 'End Site', 'rectifier': 'HARIF', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.272, 'lat': -9.308, 'notes': None},
    {'no': 99, 'site_id': 'HAO001', 'site_name': 'Hatulia', 'district': 'Ermera', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.318, 'lat': -8.812, 'notes': 'Extreme Mountain Access'},
    {'no': 100, 'site_id': 'REM001', 'site_name': 'Fada Bloco', 'district': 'Aileu', 'site_type': 'End Site', 'rectifier': 'ELTEK', 'power_status': 'No backup (grid only)', 'genset_avail': 'No Genset', 'load_dc_a': 45.0, 'load_dc_kw': 2.41, 'energy_kwh_day': 57.8, 'position': 'OUTDOOR', 'load_ac_recti_kw': 2.68, 'load_ac_total_kw': 2.68, 'load_ac_kva': 2.82, 'backup_hours': 2.0, 'revenue_tier': 'Bronze', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.654, 'lat': -8.662, 'notes': 'Extreme Mountain Access'},
    {'no': 101, 'site_id': 'ATU002', 'site_name': 'Hahipaan', 'district': 'Atauro', 'site_type': 'Sub Site', 'rectifier': 'HARIF', 'power_status': 'Backup available (PV)', 'genset_avail': 'Backup available (PV)', 'load_dc_a': 55.0, 'load_dc_kw': 2.94, 'energy_kwh_day': 70.6, 'position': 'OUTDOOR', 'load_ac_recti_kw': 3.27, 'load_ac_total_kw': 3.27, 'load_ac_kva': 3.44, 'backup_hours': 0.0, 'revenue_tier': 'Diamond', 'quadrant': 'Q3-Modernized-Monitor', 'has_dg': 'No DG', 'program': 'Samvad', 'lon': 125.5992, 'lat': -8.27299, 'notes': 'Atauro Island Ferry Access | Backup available (PV)'},
]

TIMOR_101_SITES_RAW = TIMOR_100_SITES_RAW


def calculate_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates geodesic distance between two points in km."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def compute_operational_routing(site: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes road/maritime accessible route distance from Port Dili,
    travel duration, logistics corridor, zone, wave, and forward hub.
    """
    lat = site["lat"]
    lon = site["lon"]
    dist = site["district"]
    site_id = site["site_id"]
    notes = site.get("notes") or ""

    # Straight-line distance from Port Dili
    h_dist = calculate_haversine_km(PORT_DILI_COORDS[0], PORT_DILI_COORDS[1], lat, lon)

    # Specific routing rules by district & geography
    if site_id == "ATU002" or dist == "Atauro":
        route_dist = 36.5
        mode = "Maritime Ferry / Speedboat (Port Dili Direct)"
        est_time = "1.5 - 2.0 hrs (Sea)"
        hub = "Port Dili Sea Terminal"
        zone = "Zone 1 | Dili Metropolitan (Island Hub)"
        wave = "Wave 1 | Dili Metropolitan"
    elif dist == "Oecusse":
        local_offset = 2.4 if site_id == "PAN003" else (14.0 if site_id == "PAN006" else 9.0)
        route_dist = round(142.0 + local_offset, 1)
        mode = "Maritime Ferry (Nakroma) + Paved Road"
        est_time = "8.5 - 10 hrs (Scheduled Ferry)"
        hub = "Forward Hub Oecusse"
        zone = "Zone 5 | Oecusse Enclave"
        wave = "Wave 2 | Oecusse + Central Mountain"
    elif dist == "Dili":
        route_dist = round(max(2.5, h_dist * 1.25), 1)
        mode = "Paved Urban Road Network"
        est_time = f"{int(max(15, route_dist * 2.5))} mins"
        hub = "Central Staging Dili"
        zone = "Zone 1 | Dili Metropolitan"
        wave = "Wave 1 | Dili Metropolitan"
    elif dist in ["Baucau", "Lautem"]:
        if dist == "Lautem":
            route_dist = round(max(175.0, 175.0 + (h_dist - 140) * 1.4), 1)
            est_time = "5.5 - 6.5 hrs"
        else:
            route_dist = round(h_dist * 1.34, 1)
            est_time = "3.5 - 4.5 hrs"
        mode = "North Coast Highway (Estrada Nacional 1)"
        hub = "Forward Hub Baucau"
        zone = "Zone 2 | Northern Coastal"
        wave = "Wave 4 | Northern Coastal"
    elif dist in ["Ermera", "Aileu"]:
        route_dist = round(h_dist * 1.68, 1)
        mode = "Mountain Spine Switchbacks (High Elevation 4x4)"
        est_time = "1.5 - 2.5 hrs" if dist == "Aileu" else "2.5 - 4.0 hrs"
        hub = "Central Staging Dili / Gleno"
        zone = "Zone 4 | Central Mountain Spine"
        wave = "Wave 2 | Oecusse + Central Mountain"
    elif dist in ["Cova Lima", "Manufahi", "Viqueque"]:
        if dist == "Cova Lima":
            route_dist = round(140.0 + max(0.0, h_dist - 80) * 1.3, 1)
            hub = "Forward Hub Suai"
            est_time = "5.5 - 7.0 hrs"
        elif dist == "Manufahi":
            route_dist = round(h_dist * 1.55, 1)
            hub = "Forward Hub Suai / Same"
            est_time = "4.5 - 5.5 hrs"
        else: # Viqueque
            route_dist = round(h_dist * 1.52, 1)
            hub = "Forward Hub Baucau / Viqueque"
            est_time = "6.0 - 7.5 hrs"
        mode = "Southern Lowlands Corridor (Flood-Prone / Riverbeds)"
        zone = "Zone 3 | Southern Lowlands"
        wave = "Wave 3 | Southern Lowlands"
    else:
        # Transition Districts (Liquisa, Manatuto, Bobonaro)
        if dist == "Liquisa":
            route_dist = round(max(22.0, h_dist * 1.28), 1)
            mode = "West Coast Paved Highway"
            est_time = "45 - 75 mins"
        elif dist == "Manatuto":
            route_dist = round(h_dist * 1.35, 1)
            mode = "East Coastal / Cross-Island Road"
            est_time = "2.0 - 3.5 hrs"
        else: # Bobonaro
            route_dist = round(h_dist * 1.45, 1)
            mode = "Western Mountain Border Road"
            est_time = "4.0 - 5.0 hrs"
        hub = "Central Staging Dili"
        zone = "Transition Districts"
        wave = "Wave 5 | Transition Districts"

    q_map = {"Q1-Critical": 4.0, "Q2-High": 3.0, "Q3-Modernized-Monitor": 2.0, "Q4-LowPriority": 1.0}
    c_score = q_map.get(site["quadrant"], 2.0)

    rev_map = {"Diamond": 5.0, "Platinum": 4.0, "Gold": 3.0, "Silver": 2.0, "Bronze": 1.0}
    r_score = rev_map.get(site["revenue_tier"], 2.0)

    bk = site["backup_hours"]
    b_score = 4.0 if bk == 0.0 else (3.0 if bk <= 1.0 else (2.0 if bk <= 3.0 else 1.0))

    dg_score = 4.0 if site["has_dg"] == "No DG" else 1.0

    is_extreme = "Extreme" in (notes or "") or "OFF GRID" in (notes or "")
    ext_score = 0.5 if is_extreme else 0.0

    priority_idx = round(
        (0.45 * c_score) + (0.20 * r_score) + (0.20 * b_score) + (0.15 * dg_score) + ext_score,
        2
    )

    if priority_idx >= 3.5:
        p_tier = "P0 | Immediate"
    elif priority_idx >= 3.0:
        p_tier = "P1 | Early wave"
    elif priority_idx >= 2.0:
        p_tier = "P2 | Planned"
    else:
        p_tier = "P3 | Monitor"

    if is_extreme or (site["quadrant"] == "Q1-Critical" and site["has_dg"] == "No DG" and bk == 0.0):
        readiness = "ESCALATE (High Risk)"
    elif site["has_dg"] == "No DG" and bk == 0.0:
        readiness = "HOLD (Dependency)"
    else:
        readiness = "GO (Dispatch Ready)"

    site_no = site.get("no", 1)
    if site_no <= 28:
        paas_status = "🟢 Handover Telkomcel"
    elif site_no <= 44:
        paas_status = "🟡 Testing & QA"
    elif site_no <= 66:
        paas_status = "🟣 Power I&C Active"
    elif site_no <= 78:
        paas_status = "⚪ Staged / Delivery Ready"
        readiness = "HOLD (Civil Dependency)"
    elif site_no <= 92:
        paas_status = "⚪ Staged / Dili Hub"
    else:
        paas_status = "Shipping & Customs"

    return {
        **site,
        "haversine_distance_km": h_dist,
        "accessible_route_km": route_dist,
        "transport_mode": mode,
        "est_travel_time": est_time,
        "assigned_forward_hub": hub,
        "deployment_zone": zone,
        "delivery_wave": wave,
        "priority_index": priority_idx,
        "priority_tier": p_tier,
        "readiness_gate": readiness,
        "paas_status": paas_status,
        "operator": site.get("operator", "Telkomcel"),
        "is_extreme": 1 if is_extreme else 0
    }


def get_timor_100_sites_dataframe() -> pd.DataFrame:
    """Returns all 101 Timor-Leste sites enriched with operational routing and load attributes."""
    processed = [compute_operational_routing(s) for s in TIMOR_100_SITES_RAW]
    return pd.DataFrame(processed)


def seed_timor_100_sites(db_path: str = None) -> None:
    """Seeds the 101 Timor-Leste sites table into SQLite."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(timor_sites_100)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if existing_cols and ("paas_status" not in existing_cols or "operator" not in existing_cols):
        cursor.execute("DROP TABLE IF EXISTS timor_sites_100")
        existing_cols = []

    cursor.execute("""
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
        power_status TEXT DEFAULT 'No backup (grid only)',
        genset_avail TEXT DEFAULT 'No Genset',
        load_dc_a REAL DEFAULT 0.0,
        load_dc_kw REAL DEFAULT 0.0,
        energy_kwh_day REAL DEFAULT 0.0,
        position TEXT DEFAULT 'OUTDOOR',
        load_ac_recti_kw REAL DEFAULT 0.0,
        load_ac_total_kw REAL DEFAULT 0.0,
        load_ac_kva REAL DEFAULT 0.0
    )
    """)

    # Ensure electrical load columns exist if table was already created
    cursor.execute("PRAGMA table_info(timor_sites_100)")
    existing_cols_set = {row[1] for row in cursor.fetchall()}
    load_cols = [
        ("power_status", "TEXT DEFAULT 'No backup (grid only)'"),
        ("genset_avail", "TEXT DEFAULT 'No Genset'"),
        ("load_dc_a", "REAL DEFAULT 0.0"),
        ("load_dc_kw", "REAL DEFAULT 0.0"),
        ("energy_kwh_day", "REAL DEFAULT 0.0"),
        ("position", "TEXT DEFAULT 'OUTDOOR'"),
        ("load_ac_recti_kw", "REAL DEFAULT 0.0"),
        ("load_ac_total_kw", "REAL DEFAULT 0.0"),
        ("load_ac_kva", "REAL DEFAULT 0.0"),
    ]
    for col_name, col_def in load_cols:
        if col_name not in existing_cols_set:
            cursor.execute(f"ALTER TABLE timor_sites_100 ADD COLUMN {col_name} {col_def}")

    cursor.execute("SELECT COUNT(*) FROM timor_sites_100 WHERE operator = 'Telkomcel'")
    count_row = cursor.fetchone()
    if count_row and count_row[0] > 0:
        conn.close()
        return

    df = get_timor_100_sites_dataframe()

    cols = [
        "no", "site_id", "site_name", "district", "site_type", "rectifier", "backup_hours",
        "revenue_tier", "quadrant", "has_dg", "program", "lon", "lat", "notes",
        "haversine_distance_km", "accessible_route_km", "transport_mode", "est_travel_time",
        "assigned_forward_hub", "deployment_zone", "delivery_wave", "priority_index",
        "priority_tier", "readiness_gate", "paas_status", "operator", "is_extreme",
        "power_status", "genset_avail", "load_dc_a", "load_dc_kw", "energy_kwh_day",
        "position", "load_ac_recti_kw", "load_ac_total_kw", "load_ac_kva"
    ]

    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO timor_sites_100 ({', '.join(cols)}) VALUES ({placeholders})"

    rows = []
    for _, r in df.iterrows():
        rows.append(tuple(r[c] for c in cols))

    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    df_test = get_timor_100_sites_dataframe()
    print(f"Loaded {len(df_test)} sites.")
    print("Sample with distance from Port Dili:")
    print(df_test[["site_id", "site_name", "district", "accessible_route_km", "load_dc_kw", "load_ac_total_kw", "position"]].head(10))
