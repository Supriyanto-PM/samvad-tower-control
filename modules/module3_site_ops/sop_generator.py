"""
Module 3: SOP Document Generator for Installation & Commissioning (I&C).
Provides step-by-step interactive digital checklist and compiles client-ready I&C PDF.
"""
import json
from typing import Dict, Any, List
from datetime import datetime, date
from database.connection import query_df, execute_write
from services.export_service import ExportService

STANDARD_IC_CHECKLIST_ITEMS = [
    {"id": 1, "title": "Civil & Mechanical Rigging", "spec": "Tower mount torque specs & safety cable clamp", "result": "PASS", "remarks": "Visual inspection OK; torque verified with calibrated tool"},
    {"id": 2, "title": "Power Plant & DC Rectifier", "spec": "-48V DC nominal output +/- 0.5V", "result": "PASS", "remarks": "Voltage stable at -48.2V DC; battery float verified"},
    {"id": 3, "title": "RF & Antenna Alignment", "spec": "VSWR <= 1.35 across carrier band", "result": "PASS", "remarks": "Anritsu SiteMaster test VSWR measured at 1.18"},
    {"id": 4, "title": "Fiber Optic Backbone", "spec": "Total insertion loss < 0.35 dB/km", "result": "PASS", "remarks": "OTDR bi-directional trace completed, no microbends"},
    {"id": 5, "title": "Grounding & Surge Protection", "spec": "Earthing resistance < 5.0 Ohms", "result": "PASS", "remarks": "Earth tester reading 1.84 Ohms (Within standard)"},
    {"id": 6, "title": "NOC Ping & Traffic Call Test", "spec": "Zero packet loss & latency < 15ms", "result": "PASS", "remarks": "1000 ICMP packets transmitted; 0% loss, 8.4ms average"},
    {"id": 7, "title": "Environmental & Housekeeping", "spec": "Cabinet sealed, cable entry weather-proofed", "result": "PASS", "remarks": "Roxtec seal installed, shelter clean"}
]

class SOPGenerator:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def get_standard_template(self) -> List[Dict[str, Any]]:
        """Returns the default comprehensive I&C checklist."""
        return [item.copy() for item in STANDARD_IC_CHECKLIST_ITEMS]

    def compile_ic_document(self, site_id: str, client_name: str, lead_technician: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Saves completed checklist to database and compiles standardized client-ready PDF.
        """
        checklist_code = f"IC-SVD-{site_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
        pdf_path = ExportService.generate_sop_ic_pdf(
            checklist_code=checklist_code,
            site_id=site_id,
            client_name=client_name,
            tech_name=lead_technician,
            items=items
        )

        sql = """
            INSERT INTO sop_ic_checklists 
            (checklist_code, site_id, client_name, lead_technician, inspection_date, checklist_data_json, overall_status, pdf_report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_write(
            sql,
            (checklist_code, site_id, client_name, lead_technician, date.today().isoformat(), json.dumps(items), "Approved & Signed", pdf_path),
            db_path=self.db_path
        )

        return {
            "checklist_code": checklist_code,
            "site_id": site_id,
            "pdf_path": pdf_path,
            "status": "Approved & Signed"
        }

    def get_all_generated_sops(self):
        """Retrieves history of generated I&C SOP certificates."""
        sql = "SELECT * FROM sop_ic_checklists ORDER BY created_at DESC"
        return query_df(sql, db_path=self.db_path)
