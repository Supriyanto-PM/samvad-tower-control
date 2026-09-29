"""
Timor-Leste 100-Site National Rollout Dataset & Operational Routing Engine.
Accurately encodes all 100 telecom tower sites from the Samvad Delivery Blueprint.
Computes accessible route distance from Port Dili (Lat: -8.5520, Long: 125.5711),
travel time, transport mode, deployment zones, forward hubs, delivery waves, and P0-P3 Priority Index.
"""
import math
from typing import List, Dict, Any, Tuple
import pandas as pd
from database.connection import get_connection, execute_write

PORT_DILI_COORDS = (-8.5520, 125.5711) # VCU004 Dili Port Terminal

# 100-Site Baseline Data from the Blueprint
TIMOR_100_SITES_RAW: List[Dict[str, Any]] = [
    {"no": 1, "site_id": "DAX001", "site_name": "Fomento 1", "district": "Dili", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5382, "lat": -8.5621, "notes": None},
    {"no": 2, "site_id": "DAX003", "site_name": "Timor Lodge", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5275, "lat": -8.55678, "notes": None},
    {"no": 3, "site_id": "DAX027", "site_name": "Aimutin 2", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5455, "lat": -8.5555, "notes": None},
    {"no": 4, "site_id": "CRE009", "site_name": "Kuluhun de Baixo", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5895, "lat": -8.5551, "notes": None},
    {"no": 5, "site_id": "DAX033", "site_name": "Mercado Comoro", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5486, "lat": -8.55023, "notes": None},
    {"no": 6, "site_id": "DAX024", "site_name": "Kampung Baru Dili", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5270, "lat": -8.56499, "notes": None},
    {"no": 7, "site_id": "DAX004", "site_name": "Bebonuk", "district": "Dili", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5416, "lat": -8.54704, "notes": None},
    {"no": 8, "site_id": "DAX014", "site_name": "Kampung Alor", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5593, "lat": -8.55058, "notes": None},
    {"no": 9, "site_id": "DAX025", "site_name": "Markoni", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Diamond", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5543, "lat": -8.5526, "notes": None},
    {"no": 10, "site_id": "DAX008", "site_name": "Aimutin Santos", "district": "Dili", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 0.5, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5511, "lat": -8.5591, "notes": None},
    {"no": 11, "site_id": "VCU004", "site_name": "Dili Port", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5711, "lat": -8.5520, "notes": "Port Dili Staging Origin"},
    {"no": 12, "site_id": "CRE018", "site_name": "Tubarai", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 5.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5919, "lat": -8.56857, "notes": None},
    {"no": 13, "site_id": "DAX005", "site_name": "Lurumata", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5501, "lat": -8.5534, "notes": None},
    {"no": 14, "site_id": "DAX007", "site_name": "Fatuhada", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5534, "lat": -8.54756, "notes": None},
    {"no": 15, "site_id": "DAX032", "site_name": "Malinamoc", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5261, "lat": -8.55745, "notes": None},
    {"no": 16, "site_id": "DAX035", "site_name": "Ailok Laran", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5650, "lat": -8.57249, "notes": None},
    {"no": 17, "site_id": "DAX038", "site_name": "Pantai Kelapa 2", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5452, "lat": -8.5464, "notes": None},
    {"no": 18, "site_id": "CRE020", "site_name": "Becusi Kraik", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5983, "lat": -8.5686, "notes": None},
    {"no": 19, "site_id": "DAX042", "site_name": "Perumnas", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5609, "lat": -8.5651, "notes": None},
    {"no": 20, "site_id": "CRE024", "site_name": "HERA_II", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.6538, "lat": -8.55689, "notes": None},
    {"no": 21, "site_id": "NFE007", "site_name": "Quintal Boot", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5839, "lat": -8.5637, "notes": None},
    {"no": 22, "site_id": "DAX040", "site_name": "Bebonuk 3", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5375, "lat": -8.5446, "notes": None},
    {"no": 23, "site_id": "DAX018", "site_name": "Beto", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Platinum", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5343, "lat": -8.54883, "notes": None},
    {"no": 24, "site_id": "VCU007", "site_name": "Vila Verde", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Platinum", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5678, "lat": -8.56258, "notes": None},
    {"no": 25, "site_id": "NFE008", "site_name": "Audian", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5856, "lat": -8.55817, "notes": None},
    {"no": 26, "site_id": "DAX021", "site_name": "Delta 2", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5377, "lat": -8.55679, "notes": None},
    {"no": 27, "site_id": "DAX026", "site_name": "Hudilaran", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5589, "lat": -8.55603, "notes": None},
    {"no": 28, "site_id": "CRE004", "site_name": "Bedois", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.6180, "lat": -8.56449, "notes": None},
    {"no": 29, "site_id": "VCU001", "site_name": "Palpaco", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5658, "lat": -8.55335, "notes": None},
    {"no": 30, "site_id": "VCU002", "site_name": "Untl", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.5, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5785, "lat": -8.5557, "notes": None},
    {"no": 31, "site_id": "BAZ004", "site_name": "Fatunia", "district": "Liquisa", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.4879, "lat": -8.56012, "notes": None},
    {"no": 32, "site_id": "CRE014", "site_name": "Aituri Laran", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5950, "lat": -8.57868, "notes": None},
    {"no": 33, "site_id": "NFE010", "site_name": "Lahane Ocidental", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5865, "lat": -8.5769, "notes": None},
    {"no": 34, "site_id": "NFE005", "site_name": "FFTL", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5829, "lat": -8.55436, "notes": None},
    {"no": 35, "site_id": "DAX019", "site_name": "BETO PNTL", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Platinum", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.5326, "lat": -8.55338, "notes": None},
    {"no": 36, "site_id": "DAX039", "site_name": "DIT Baya Leste", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5417, "lat": -8.56795, "notes": None},
    {"no": 37, "site_id": "CRE019", "site_name": "Bedois TT", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.6172, "lat": -8.56757, "notes": None},
    {"no": 38, "site_id": "CRE006", "site_name": "Hera", "district": "Dili", "site_type": "Hub Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Gold", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.6650, "lat": -8.53015, "notes": None},
    {"no": 39, "site_id": "DAX046", "site_name": "UNPAZ", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5466, "lat": -8.56471, "notes": None},
    {"no": 40, "site_id": "CRE021", "site_name": "Becora Camea", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.6093, "lat": -8.5619, "notes": None},
    {"no": 41, "site_id": "VCU010", "site_name": "UNDIL", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5806, "lat": -8.56251, "notes": None},
    {"no": 42, "site_id": "DAX043", "site_name": "DELTA 3", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5419, "lat": -8.55757, "notes": None},
    {"no": 43, "site_id": "NFE004", "site_name": "Marabia", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5751, "lat": -8.57971, "notes": None},
    {"no": 44, "site_id": "DAX041", "site_name": "Hudilaran 2", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Gold", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5570, "lat": -8.55934, "notes": None},
    {"no": 45, "site_id": "VEN003", "site_name": "ARIANA", "district": "Baucau", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 126.4173, "lat": -8.6335, "notes": None},
    {"no": 46, "site_id": "CRE022", "site_name": "Rooftop Unital", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.6065, "lat": -8.56345, "notes": None},
    {"no": 47, "site_id": "DAX015", "site_name": "TP Indoor", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5413, "lat": -8.55368, "notes": None},
    {"no": 48, "site_id": "CRE007", "site_name": "Balibar", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 5.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.6035, "lat": -8.59804, "notes": None},
    {"no": 49, "site_id": "VCU008", "site_name": "EWSD", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5791, "lat": -8.55892, "notes": None},
    {"no": 50, "site_id": "CRE011", "site_name": "Taibesi 2", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5976, "lat": -8.56429, "notes": None},
    {"no": 51, "site_id": "PAN004", "site_name": "Lifau City", "district": "Oecusse", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 124.3691, "lat": -9.20373, "notes": "Ferry Nakroma Access"},
    {"no": 52, "site_id": "DAX028", "site_name": "Casnavar", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5310, "lat": -8.60022, "notes": None},
    {"no": 53, "site_id": "DAX022", "site_name": "Kampung Merdeka", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5326, "lat": -8.5582, "notes": None},
    {"no": 54, "site_id": "MET003", "site_name": "Metinaro", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.7560, "lat": -8.53119, "notes": None},
    {"no": 55, "site_id": "DAX051", "site_name": "BETO ROOFTOP", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5317, "lat": -8.54806, "notes": None},
    {"no": 56, "site_id": "DAX045", "site_name": "Canossa", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.5354, "lat": -8.57032, "notes": None},
    {"no": 57, "site_id": "BAU008", "site_name": "Gariuri", "district": "Baucau", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 5.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 126.4073, "lat": -8.54706, "notes": None},
    {"no": 58, "site_id": "DAX047", "site_name": "Lidun 2", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5439, "lat": -8.58439, "notes": None},
    {"no": 59, "site_id": "LAG001", "site_name": "Saelari", "district": "Baucau", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 126.6785, "lat": -8.4993, "notes": None},
    {"no": 60, "site_id": "SUA006", "site_name": "Suai Airport", "district": "Cova Lima", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.2835, "lat": -9.31851, "notes": "Forward Hub Suai"},
    {"no": 61, "site_id": "VCU012", "site_name": "ROOFTOP_COLMERA", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5723, "lat": -8.55616, "notes": None},
    {"no": 62, "site_id": "MET001", "site_name": "Duyung", "district": "Dili", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.7669, "lat": -8.52144, "notes": None},
    {"no": 63, "site_id": "SUA013", "site_name": "Ouges", "district": "Cova Lima", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.2304, "lat": -9.29588, "notes": None},
    {"no": 64, "site_id": "WAT002", "site_name": "Uatulari", "district": "Viqueque", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 126.5317, "lat": -8.82022, "notes": None},
    {"no": 65, "site_id": "VEM002", "site_name": "Vemasse", "district": "Baucau", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Silver", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 126.2105, "lat": -8.51545, "notes": None},
    {"no": 66, "site_id": "DAX049", "site_name": "MASLIDUN", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.5046, "lat": -8.5666, "notes": None},
    {"no": 67, "site_id": "PAN006", "site_name": "PADIAE", "district": "Oecusse", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.5, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 124.3521, "lat": -9.2550, "notes": "Enclave Ferry Access"},
    {"no": 68, "site_id": "CRE017", "site_name": "Hera Akanunu", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.6731, "lat": -8.54523, "notes": None},
    {"no": 69, "site_id": "PAN005", "site_name": "Masin", "district": "Oecusse", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Silver", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 124.3401, "lat": -9.21305, "notes": "Enclave Ferry Access"},
    {"no": 70, "site_id": "BAL001", "site_name": "Fatuklulik", "district": "Bobonaro", "site_type": "Backbone", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.0437, "lat": -8.97317, "notes": None},
    {"no": 71, "site_id": "DAX020", "site_name": "DIT Manleuana", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.5447, "lat": -8.56404, "notes": None},
    {"no": 72, "site_id": "LOS009", "site_name": "SORO NAIRETE", "district": "Lautem", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 2.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 126.9659, "lat": -8.51241, "notes": None},
    {"no": 73, "site_id": "BAZ008", "site_name": "LAUHATA", "district": "Liquisa", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.3562, "lat": -8.58462, "notes": None},
    {"no": 74, "site_id": "VIQ009", "site_name": "Carabalun", "district": "Viqueque", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 126.3564, "lat": -8.85172, "notes": None},
    {"no": 75, "site_id": "DAX034", "site_name": "Arbiruh Beach", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.5383, "lat": -8.54028, "notes": None},
    {"no": 76, "site_id": "DAX010", "site_name": "TP Outdoor", "district": "Dili", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.5413, "lat": -8.55379, "notes": None},
    {"no": 77, "site_id": "RAI001", "site_name": "Tokoluli", "district": "Ermera", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Bronze", "quadrant": "Q4-LowPriority", "has_dg": "DG", "program": "Samvad", "lon": 125.4378, "lat": -8.70246, "notes": None},
    {"no": 78, "site_id": "MET002", "site_name": "Heineken Sabuli", "district": "Dili", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Bronze", "quadrant": "Q4-LowPriority", "has_dg": "DG", "program": "Samvad", "lon": 125.6955, "lat": -8.53801, "notes": None},
    {"no": 79, "site_id": "BAZ005", "site_name": "Terlau", "district": "Liquisa", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.4539, "lat": -8.63018, "notes": None},
    {"no": 80, "site_id": "BAZ003", "site_name": "Leovenia", "district": "Liquisa", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.3807, "lat": -8.68415, "notes": None},
    {"no": 81, "site_id": "NAT002", "site_name": "NATARBORA 2", "district": "Manatuto", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 4.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 126.0543, "lat": -8.98082, "notes": None},
    {"no": 82, "site_id": "MAN002", "site_name": "Kampung Baru", "district": "Manatuto", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 0.2, "revenue_tier": "Bronze", "quadrant": "Q4-LowPriority", "has_dg": "DG", "program": "Samvad", "lon": 126.0075, "lat": -8.53111, "notes": None},
    {"no": 83, "site_id": "SUA003", "site_name": "SUAI LORO", "district": "Cova Lima", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.2789, "lat": -9.3468, "notes": None},
    {"no": 84, "site_id": "LOS007", "site_name": "PUIHORO", "district": "Lautem", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 3.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 126.9932, "lat": -8.50923, "notes": None},
    {"no": 85, "site_id": "MAN006", "site_name": "Iliheu", "district": "Manatuto", "site_type": "Hub Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.9531, "lat": -8.53905, "notes": None},
    {"no": 86, "site_id": "SAM005", "site_name": "Same Postu", "district": "Manufahi", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.6530, "lat": -9.0010, "notes": None},
    {"no": 87, "site_id": "MAB001", "site_name": "Vatunau", "district": "Liquisa", "site_type": "Hub Site", "rectifier": "ELTEK", "backup_hours": 0.5, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.2769, "lat": -8.60885, "notes": None},
    {"no": 88, "site_id": "SUA012", "site_name": "Suai Talioan", "district": "Cova Lima", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q4-LowPriority", "has_dg": "DG", "program": "Samvad", "lon": 125.2413, "lat": -9.32303, "notes": None},
    {"no": 89, "site_id": "OSS003", "site_name": "LIARUKA", "district": "Viqueque", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 3.0, "revenue_tier": "Bronze", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 126.2786, "lat": -8.73561, "notes": "Extreme Mountain Access"},
    {"no": 90, "site_id": "OSS001", "site_name": "Asalaitula", "district": "Viqueque", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 126.3680, "lat": -8.69832, "notes": None},
    {"no": 91, "site_id": "BAG001", "site_name": "Baugia", "district": "Baucau", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 1.0, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 126.6535, "lat": -8.62838, "notes": None},
    {"no": 92, "site_id": "ERM002", "site_name": "Ermera Old Town", "district": "Ermera", "site_type": "End Site", "rectifier": "ELTEK", "backup_hours": 4.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.4007, "lat": -8.75003, "notes": None},
    {"no": 93, "site_id": "LET002", "site_name": "Lauana", "district": "Ermera", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 0.5, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.4251, "lat": -8.88938, "notes": "Extreme Mountain Access"},
    {"no": 94, "site_id": "BAG002", "site_name": "Defause", "district": "Baucau", "site_type": "Sub Site", "rectifier": "HARIF", "backup_hours": 1.0, "revenue_tier": "Bronze", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 126.6990, "lat": -8.59689, "notes": "Extreme Coastal/Elevation"},
    {"no": 95, "site_id": "LET003", "site_name": "Ducurai", "district": "Ermera", "site_type": "Hub Site", "rectifier": "HARIF", "backup_hours": 0.5, "revenue_tier": "Bronze", "quadrant": "Q1-Critical", "has_dg": "No DG", "program": "Samvad", "lon": 125.4642, "lat": -8.82378, "notes": "Extreme Mountain Spine"},
    {"no": 96, "site_id": "SAM006", "site_name": "Manico", "district": "Manufahi", "site_type": "End Site", "rectifier": "HARIF", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q2-High", "has_dg": "No DG", "program": "Samvad", "lon": 125.6418, "lat": -8.99928, "notes": None},
    {"no": 97, "site_id": "BAR001", "site_name": "Manehat", "district": "Manatuto", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 0.5, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.9721, "lat": -8.9137, "notes": None},
    {"no": 98, "site_id": "SUA002", "site_name": "Haemanu", "district": "Cova Lima", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.3428, "lat": -9.2559, "notes": None},
    {"no": 99, "site_id": "LET001", "site_name": "Lete foho", "district": "Ermera", "site_type": "Sub Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Bronze", "quadrant": "Q3-Modernized-Monitor", "has_dg": "DG", "program": "Samvad", "lon": 125.4131, "lat": -8.83195, "notes": None},
    {"no": 100, "site_id": "ATU002", "site_name": "Atauro", "district": "Dili", "site_type": "Hub Site", "rectifier": "ELTEK", "backup_hours": 0.0, "revenue_tier": "Diamond", "quadrant": "Q3-Modernized-Monitor", "has_dg": "No DG", "program": "Samvad", "lon": 125.5992, "lat": -8.27299, "notes": "Atauro Island Ferry Access"},
]

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
    if site_id == "ATU002":
        # Atauro Island: Sea Ferry / Speedboat from Port Dili
        route_dist = 36.5
        mode = "Maritime Ferry / Speedboat (Port Dili Direct)"
        est_time = "1.5 - 2.0 hrs (Sea)"
        hub = "Port Dili Sea Terminal"
        zone = "Zone 1 | Dili Metropolitan (Island Hub)"
        wave = "Wave 1 | Dili Metropolitan"
    elif dist == "Oecusse":
        # Oecusse Enclave: Berlin Nakroma Ferry from Port Dili + local transit
        # Base sea route to Pante Macassar is ~142 km, plus local road
        local_offset = 6.0 if site_id == "PAN004" else (14.0 if site_id == "PAN006" else 9.0)
        route_dist = round(142.0 + local_offset, 1)
        mode = "Maritime Ferry (Nakroma) + Paved Road"
        est_time = "8.5 - 10 hrs (Scheduled Ferry)"
        hub = "Forward Hub Oecusse"
        zone = "Zone 5 | Oecusse Enclave"
        wave = "Wave 2 | Oecusse + Central Mountain"
    elif dist == "Dili":
        # Dili Metropolitan: Urban network
        # Urban circuity 1.25x or minimum 2.5 km
        route_dist = round(max(2.5, h_dist * 1.25), 1)
        mode = "Paved Urban Road Network"
        est_time = f"{int(max(15, route_dist * 2.5))} mins"
        hub = "Central Staging Dili"
        zone = "Zone 1 | Dili Metropolitan"
        wave = "Wave 1 | Dili Metropolitan"
    elif dist in ["Baucau", "Lautem"]:
        # Northern Coastal Corridor via Estrada Nacional 1 (A01)
        # Baucau straight-line ~95-120 km -> Road distance ~125 - 155 km
        # Lautem straight-line ~155-165 km -> Road distance ~215 - 235 km
        if dist == "Lautem":
            route_dist = round(175.0 + (h_dist - 150) * 1.4, 1)
            est_time = "5.5 - 6.5 hrs"
        else:
            route_dist = round(h_dist * 1.34, 1)
            est_time = "3.5 - 4.5 hrs"
        mode = "North Coast Highway (Estrada Nacional 1)"
        hub = "Forward Hub Baucau"
        zone = "Zone 2 | Northern Coastal"
        wave = "Wave 4 | Northern Coastal"
    elif dist == "Ermera":
        # Central Mountain Spine (via Tibar -> Gleno -> Letefoho switchbacks)
        # Mountain elevation climb up to 1,500m
        route_dist = round(h_dist * 1.68, 1)
        mode = "Mountain Spine Switchbacks (High Elevation 4x4)"
        est_time = "2.5 - 4.0 hrs"
        hub = "Central Staging Dili / Gleno"
        zone = "Zone 4 | Central Mountain Spine"
        wave = "Wave 2 | Oecusse + Central Mountain"
    elif dist in ["Cova Lima", "Manufahi", "Viqueque"]:
        # Southern Lowlands & Trans-Timor Corridor
        # Suai (Cova Lima) ~155 - 175 km via Ainaro/Cassa or Maliana
        # Same (Manufahi) ~115 - 130 km via Aileu/Maubisse
        # Viqueque ~180 - 200 km
        if dist == "Cova Lima":
            route_dist = round(140.0 + (h_dist - 80) * 1.3, 1)
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
            route_dist = round(max(25.0, h_dist * 1.28), 1)
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

    # Compute Priority Index from Blueprint Formula (Page 6)
    # Priority Index = 0.45*Criticality + 0.20*Revenue + 0.20*Backup + 0.15*DG + Extreme_overlay
    # Criticality score: Q1 = 4, Q2 = 3, Q3 = 2, Q4 = 1
    q_map = {"Q1-Critical": 4.0, "Q2-High": 3.0, "Q3-Modernized-Monitor": 2.0, "Q4-LowPriority": 1.0}
    c_score = q_map.get(site["quadrant"], 2.0)

    # Revenue score: Diamond = 5, Platinum = 4, Gold = 3, Silver = 2, Bronze = 1
    rev_map = {"Diamond": 5.0, "Platinum": 4.0, "Gold": 3.0, "Silver": 2.0, "Bronze": 1.0}
    r_score = rev_map.get(site["revenue_tier"], 2.0)

    # Backup resilience score: 0h = 4 (high risk/urgency), <=1h = 3, 2-3h = 2, >3h = 1
    bk = site["backup_hours"]
    b_score = 4.0 if bk == 0.0 else (3.0 if bk <= 1.0 else (2.0 if bk <= 3.0 else 1.0))

    # DG readiness score: No DG = 4 (fragile/needs priority), DG = 1
    dg_score = 4.0 if site["has_dg"] == "No DG" else 1.0

    # Extreme overlay: +0.5 bonus if extreme
    is_extreme = "Extreme" in (notes or "")
    ext_score = 0.5 if is_extreme else 0.0

    priority_idx = round(
        (0.45 * c_score) + (0.20 * r_score) + (0.20 * b_score) + (0.15 * dg_score) + ext_score,
        2
    )

    # Classification
    if priority_idx >= 3.5:
        p_tier = "P0 | Immediate"
    elif priority_idx >= 3.0:
        p_tier = "P1 | Early wave"
    elif priority_idx >= 2.0:
        p_tier = "P2 | Planned"
    else:
        p_tier = "P3 | Monitor"

    # Readiness Gate decision (Page 13)
    if is_extreme or site["quadrant"] == "Q1-Critical" and site["has_dg"] == "No DG" and bk == 0.0:
        readiness = "ESCALATE (High Risk)"
    elif site["has_dg"] == "No DG" and bk == 0.0:
        readiness = "HOLD (Dependency)"
    else:
        readiness = "GO (Dispatch Ready)"

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
        "is_extreme": 1 if is_extreme else 0
    }

def get_timor_100_sites_dataframe() -> pd.DataFrame:
    """Returns all 100 Timor-Leste sites enriched with operational routing attributes."""
    processed = [compute_operational_routing(s) for s in TIMOR_100_SITES_RAW]
    return pd.DataFrame(processed)

def seed_timor_100_sites(db_path: str = None) -> None:
    """Seeds the 100 Timor-Leste sites table into SQLite."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
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
        is_extreme INTEGER DEFAULT 0
    )
    """)

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM timor_sites_100")
    if cursor.fetchone()[0] == 100:
        conn.close()
        return # Already loaded

    # Clear and insert all 100
    cursor.execute("DELETE FROM timor_sites_100")
    df = get_timor_100_sites_dataframe()
    
    cols = [
        "no", "site_id", "site_name", "district", "site_type", "rectifier", "backup_hours",
        "revenue_tier", "quadrant", "has_dg", "program", "lon", "lat", "notes",
        "haversine_distance_km", "accessible_route_km", "transport_mode", "est_travel_time",
        "assigned_forward_hub", "deployment_zone", "delivery_wave", "priority_index",
        "priority_tier", "readiness_gate", "is_extreme"
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
    print(df_test[["site_id", "site_name", "district", "accessible_route_km", "est_travel_time", "transport_mode", "priority_tier"]].head(10))
