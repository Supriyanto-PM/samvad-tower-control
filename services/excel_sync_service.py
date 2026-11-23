"""
Excel Master Sync Service for Samvad PMO-CC.
Provides two-way Excel synchronization:
1. Exports current operational data into a user-friendly, color-coded 'Samvad_Master_Tracker.xlsx'.
2. Ingests uploaded Excel spreadsheets to update database records with full audit logging.
"""
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, Tuple
from database.connection import get_connection, query_df, execute_write

MASTER_EXCEL_PATH = "reports/Samvad_Master_Tracker.xlsx"

class ExcelSyncService:
    @staticmethod
    def generate_master_template(output_path: str = MASTER_EXCEL_PATH) -> str:
        """Generates a user-friendly, pre-filled Master Tracker Excel workbook."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wb = openpyxl.Workbook()
        wb.remove(wb.active) # Remove default sheet

        # Styles
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Navy Blue
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        guide_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        # 1. Quick Guide Sheet
        ws_guide = wb.create_sheet(title="Instructions & Guide")
        ws_guide.views.sheetView[0].showGridLines = True
        guide_lines = [
            ("SAMVAD PMO COMMAND CENTER — MASTER TRACKER TEMPLATE", Font(size=14, bold=True, color="1E3A8A")),
            ("PT Samvad Technology Services | PMO Lead: Supriyanto", Font(size=10, italic=True, color="475569")),
            ("", Font()),
            ("HOW TO USE THIS SPREADSHEET (FOR LOW-TECH CONVENIENCE):", Font(size=11, bold=True)),
            ("1. Open any of the sheets below: '1_Customs_Logistics', '2_SGA_Expenses', '3_Site_Status', or '4_POC_Presales'.", Font(size=10)),
            ("2. Update existing rows or add new rows directly in Excel.", Font(size=10)),
            ("3. Save this file, then upload it back to the PMO Command Center web app via 'Master Excel Sync'.", Font(size=10)),
            ("4. The system will automatically read your updates, calculate KPI scores, and update the dashboard!", Font(size=10, bold=True, color="059669")),
            ("", Font()),
            ("TRAFFIC LIGHT STATUS CONVENTIONS:", Font(size=11, bold=True)),
            ("GREEN = On Track / Safe / Normal", Font(size=10, color="059669")),
            ("YELLOW = Attention / Watch List / Buffer ≤ 5 Days", Font(size=10, color="D97706")),
            ("RED = Critical / Action Required / Buffer ≤ 2 Days", Font(size=10, color="DC2626")),
        ]
        for row_idx, (text, font_style) in enumerate(guide_lines, 1):
            ws_guide.cell(row=row_idx, column=1, value=text).font = font_style

        ws_guide.column_dimensions['A'].width = 85

        # 2. Sheet 1: Customs & Logistics
        df_shipments = query_df("SELECT bl_number, vendor_name, item_description, port_of_origin, etd, eta, project_commissioning_deadline, current_milestone, customs_channel, notes FROM customs_shipments")
        ExcelSyncService._add_data_sheet(wb, "1_Customs_Logistics", df_shipments, header_fill, header_font, thin_border)

        # 3. Sheet 2: SG&A Expenses
        df_sga = query_df("SELECT expense_date, category, description, amount_idr, site_id FROM sga_expenses")
        ExcelSyncService._add_data_sheet(wb, "2_SGA_Expenses", df_sga, header_fill, header_font, thin_border)

        # 4. Sheet 3: Tower Sites & Outages
        df_sites = query_df("SELECT site_id, site_name, region, current_status, uptime_percent, ip_address FROM tower_sites")
        ExcelSyncService._add_data_sheet(wb, "3_Site_Status", df_sites, header_fill, header_font, thin_border)

        # 5. Sheet 4: Presales & POC
        df_poc = query_df("SELECT poc_code, client_name, milestone_name, target_deadline, stretch_target_deadline, actual_completion_date, status, lead_presales_engineer FROM poc_milestones")
        ExcelSyncService._add_data_sheet(wb, "4_POC_Presales", df_poc, header_fill, header_font, thin_border)

        # 6. Sheet 5: Timor-Leste 101-Site National Rollout & Operational Routing from Port Dili
        df_timor = query_df("""
            SELECT site_id, site_name, district, site_type, rectifier, power_status, genset_avail,
                   load_dc_a, load_dc_kw, energy_kwh_day, position, load_ac_recti_kw, load_ac_total_kw, load_ac_kva,
                   paas_status, accessible_route_km, est_travel_time, transport_mode,
                   assigned_forward_hub, deployment_zone, delivery_wave, priority_tier, readiness_gate,
                   quadrant, revenue_tier, backup_hours, has_dg, lon, lat, notes
            FROM timor_sites_100 ORDER BY accessible_route_km ASC
        """)
        if not df_timor.empty:
            ExcelSyncService._add_data_sheet(wb, "5_Timor_100_Sites_Routing", df_timor, header_fill, header_font, thin_border)


        wb.save(output_path)
        return output_path

    @staticmethod
    def _add_data_sheet(wb, title, df, header_fill, header_font, border):
        ws = wb.create_sheet(title=title)
        ws.views.sheetView[0].showGridLines = True
        
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        # Header style
        for col_num in range(1, len(df.columns) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Row style
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = border
                cell.font = Font(name="Segoe UI", size=10)

        # Adjust widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    @staticmethod
    def sync_from_uploaded_excel(uploaded_file) -> Tuple[bool, str, Dict[str, int]]:
        """Reads uploaded Excel file, updates database records, and logs activity."""
        try:
            wb = openpyxl.load_workbook(uploaded_file, data_only=True)
            stats = {"shipments_updated": 0, "expenses_added": 0, "sites_updated": 0, "poc_updated": 0}

            # 1. Sync Customs
            if "1_Customs_Logistics" in wb.sheetnames:
                ws = wb["1_Customs_Logistics"]
                rows = list(ws.iter_rows(values_only=True))
                if len(rows) > 1:
                    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
                    for row_data in rows[1:]:
                        if not row_data[0]:
                            continue
                        row_dict = dict(zip(headers, row_data))
                        bl = str(row_dict.get("bl_number", "")).strip()
                        if bl:
                            # Update existing or insert
                            milestone = str(row_dict.get("current_milestone", "Ocean Freight Transit"))
                            channel = str(row_dict.get("customs_channel", "Green"))
                            eta = str(row_dict.get("eta", ""))[:10]
                            notes = str(row_dict.get("notes", ""))
                            
                            execute_write(
                                """
                                UPDATE customs_shipments 
                                SET current_milestone = ?, customs_channel = ?, eta = ?, notes = ?
                                WHERE bl_number = ?
                                """,
                                (milestone, channel, eta, notes, bl)
                            )
                            stats["shipments_updated"] += 1

            # 2. Sync Sites
            if "3_Site_Status" in wb.sheetnames:
                ws = wb["3_Site_Status"]
                rows = list(ws.iter_rows(values_only=True))
                if len(rows) > 1:
                    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
                    for row_data in rows[1:]:
                        if not row_data[0]:
                            continue
                        row_dict = dict(zip(headers, row_data))
                        site_id = str(row_dict.get("site_id", "")).strip()
                        status = str(row_dict.get("current_status", "ONLINE")).strip().upper()
                        try:
                            uptime = float(row_dict.get("uptime_percent", 99.0))
                        except Exception:
                            uptime = 99.0

                        if site_id:
                            execute_write(
                                "UPDATE tower_sites SET current_status = ?, uptime_percent = ? WHERE site_id = ?",
                                (status, uptime, site_id)
                            )
                            stats["sites_updated"] += 1

            # 3. Sync POC
            if "4_POC_Presales" in wb.sheetnames:
                ws = wb["4_POC_Presales"]
                rows = list(ws.iter_rows(values_only=True))
                if len(rows) > 1:
                    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
                    for row_data in rows[1:]:
                        if not row_data[0]:
                            continue
                        row_dict = dict(zip(headers, row_data))
                        poc_code = str(row_dict.get("poc_code", "")).strip()
                        status = str(row_dict.get("status", "On Track")).strip()
                        actual_dt = row_dict.get("actual_completion_date")
                        actual_str = str(actual_dt)[:10] if actual_dt else None

                        if poc_code:
                            execute_write(
                                "UPDATE poc_milestones SET status = ?, actual_completion_date = ? WHERE poc_code = ?",
                                (status, actual_str, poc_code)
                            )
                            stats["poc_updated"] += 1

            # 4. Sync Timor 100 Sites
            if "5_Timor_100_Sites_Routing" in wb.sheetnames:
                ws = wb["5_Timor_100_Sites_Routing"]
                rows = list(ws.iter_rows(values_only=True))
                if len(rows) > 1:
                    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
                    for row_data in rows[1:]:
                        if not row_data[0]:
                            continue
                        row_dict = dict(zip(headers, row_data))
                        site_id = str(row_dict.get("site_id", "")).strip()
                        readiness = str(row_dict.get("readiness_gate", "")).strip().upper()
                        notes = str(row_dict.get("notes", "")).strip()
                        paas_st = str(row_dict.get("paas_status", "")).strip()
                        if site_id:
                            if readiness in ["GO", "HOLD", "ESCALATE", "RESEQUENCE"]:
                                execute_write(
                                    "UPDATE timor_sites_100 SET readiness_gate = ?, notes = ? WHERE site_id = ?",
                                    (readiness, notes, site_id)
                                )
                            if paas_st and paas_st != "nan":
                                execute_write(
                                    "UPDATE timor_sites_100 SET paas_status = ? WHERE site_id = ?",
                                    (paas_st, site_id)
                                )
                            stats["timor_sites_updated"] = stats.get("timor_sites_updated", 0) + 1


            # Log audit
            execute_write(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("ExcelSync", "PMO-Lead", "EXCEL_SYNC_UPDATE", f"Synced: {stats}", "SUCCESS")
            )

            msg = f"Excel Master Tracker successfully synchronized! Updated {stats['shipments_updated']} shipments, {stats['sites_updated']} sites, {stats['poc_updated']} POC milestones, {stats.get('timor_sites_updated', 0)} Timor-100 sites."
            return True, msg, stats
        except Exception as e:
            return False, f"Failed to sync Excel file: {str(e)}", {}

    @staticmethod
    def sync_from_google_sheets(sheet_url: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Parses a public or shared Google Sheets link and syncs Timor-Leste 100 sites data.
        Supports standard Google Sheets URL format:
        https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit...
        """
        import re
        import io
        import requests

        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if not match:
            return False, "Invalid Google Sheets URL. Please copy the full link from your browser address bar.", {}

        sheet_id = match.group(1)
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"

        try:
            resp = requests.get(csv_url, timeout=12)
            if resp.status_code != 200:
                return False, f"Could not fetch Google Sheet (HTTP {resp.status_code}). Ensure link sharing is set to 'Anyone with the link can view'.", {}

            df = pd.read_csv(io.StringIO(resp.text))
            df.columns = [str(c).strip().lower() for c in df.columns]

            updated_count = 0
            for _, row in df.iterrows():
                site_id = str(row.get("site_id", "")).strip()
                readiness = str(row.get("readiness_gate", "")).strip().upper()
                notes = str(row.get("notes", "")).strip()

                if site_id and site_id != "nan":
                    if readiness in ["GO", "HOLD", "ESCALATE", "RESEQUENCE"]:
                        execute_write(
                            "UPDATE timor_sites_100 SET readiness_gate = ?, notes = ? WHERE site_id = ?",
                            (readiness, notes if notes != "nan" else "", site_id)
                        )
                        updated_count += 1

            # Audit log
            execute_write(
                """
                INSERT INTO notification_audit_logs (channel, recipient, message_type, payload, sent_status)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("GoogleSheetsSync", "PIC-Cloud", "GSHEETS_LIVE_SYNC", f"Updated {updated_count} sites from GSheets", "SUCCESS")
            )

            return True, f"Successfully synchronized {updated_count} sites directly from Google Sheets!", {"updated_sites": updated_count}
        except Exception as e:
            return False, f"Google Sheets sync failed: {str(e)}", {}

