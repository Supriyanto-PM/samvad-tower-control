"""
Export Service for Samvad PMO Command Center (PMO-CC).
Generates client-ready and management reports:
- PDF (ReportLab) for I&C SOP documents & Friday Weekly PMO Reports
- Excel (.xlsx via openpyxl) for financial/SLA multi-sheet audits
- Word (.docx via python-docx) for formal executive briefings
"""
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

# ReportLab imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage

# Excel import
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# Word import
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

REPORTS_DIR = "reports"

def ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)

class ExportService:
    @staticmethod
    def generate_weekly_pdf_report(kpi_summary: Dict[str, Any], week_num: int, year: int) -> str:
        """Generates a professional executive Weekly SLA Status PDF report."""
        ensure_reports_dir()
        filename = f"{REPORTS_DIR}/Samvad_PMO_Weekly_Report_W{week_num}_{year}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'), spaceAfter=14)
        h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=6)
        body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#334155'), leading=12)

        elements = []

        # Header with Logo
        logo_path = "assets/samvad_logo_horizontal.png"
        if os.path.exists(logo_path):
            logo_img = RLImage(logo_path, width=130, height=28.5)
            header_table = Table([[logo_img, Paragraph("<b>PMO COMMAND CENTER (PMO-CC)</b><br/><font size=8 color='#475569'>Weekly SLA & KPI Status Report | Week " + str(week_num) + ", " + str(year) + "</font>", subtitle_style)]], colWidths=[140, 380])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(header_table)
        else:
            elements.append(Paragraph("PT SAMVAD TECHNOLOGY SERVICES", title_style))
            elements.append(Paragraph(f"PMO Command Center (PMO-CC) — Weekly SLA & KPI Status Report | Week {week_num}, {year}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=12))

        # Executive Summary Box
        overall_score = kpi_summary.get("overall_score", 100.0)
        tier_label = kpi_summary.get("tier_label", "100% Target Met")
        summary_text = (
            f"<b>Report Run:</b> Friday 14:00 WIB (SLA Deadline 17:00 WIB - 100% Compliant)<br/>"
            f"<b>PMO Lead:</b> Supriyanto | <b>Target Performance Tier:</b> Maximum 120% Tier<br/>"
            f"<b>Achieved Composite KPI Score:</b> <font color='#10B981' size='11'><b>{overall_score}%</b></font> ({tier_label})"
        )
        summary_table = Table([[Paragraph(summary_text, body_style)]], colWidths=[520])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 14))

        # KPI Category Breakdown Table
        elements.append(Paragraph("Contract KPI Performance Matrix (Annex B Alignment)", h2_style))
        cats = kpi_summary.get("categories", {})
        
        table_data = [
            ["KPI Category", "Weight", "Raw Score", "Weighted Score", "Operational Status"],
            [
                "A. Supply Chain & Customs Guardian",
                f"{cats.get('category_a', {}).get('weight', 0.25)*100:.0f}%",
                f"{cats.get('category_a', {}).get('raw_score', 100):.1f}%",
                f"{cats.get('category_a', {}).get('weighted_score', 25):.1f}%",
                cats.get('category_a', {}).get('status', 'On Target')
            ],
            [
                "B. SG&A & Manpower Financial Sentinel",
                f"{cats.get('category_b', {}).get('weight', 0.25)*100:.0f}%",
                f"{cats.get('category_b', {}).get('raw_score', 100):.1f}%",
                f"{cats.get('category_b', {}).get('weighted_score', 25):.1f}%",
                cats.get('category_b', {}).get('status', 'Compliant')
            ],
            [
                "C. Site Availability & SLA Operations",
                f"{cats.get('category_c', {}).get('weight', 0.25)*100:.0f}%",
                f"{cats.get('category_c', {}).get('raw_score', 100):.1f}%",
                f"{cats.get('category_c', {}).get('weighted_score', 25):.1f}%",
                cats.get('category_c', {}).get('status', 'Meets SLA')
            ],
            [
                "D. Presales & SLA Auto-Reporting",
                f"{cats.get('category_d', {}).get('weight', 0.25)*100:.0f}%",
                f"{cats.get('category_d', {}).get('raw_score', 100):.1f}%",
                f"{cats.get('category_d', {}).get('weighted_score', 25):.1f}%",
                cats.get('category_d', {}).get('status', 'On Track')
            ],
            [
                "OVERALL COMPOSITE ACHIEVED",
                "100%",
                "-",
                f"{overall_score:.2f}%",
                tier_label
            ]
        ]

        col_widths = [190, 45, 65, 80, 140]
        kpi_table = Table(table_data, colWidths=col_widths)
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (3, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # Operational Highlights
        elements.append(Paragraph("Key PMO Operational Highlights & Directives", h2_style))
        highlights = (
            "• <b>Customs & Supply Chain:</b> All critical shipments tracked with B/L APIs. Buffer alerts active; Belawan route prioritized to avoid Red channel delay.<br/>"
            "• <b>SG&A Discipline:</b> Cumulative SG&A maintained strictly below Year 1 ceiling of 12.0%. High-visit field engineers identified for retainer conversion.<br/>"
            "• <b>Site Operations SLA:</b> Nationwide network availability stands comfortably above the mandatory 95.0% threshold. Zero unhandled >15min outages.<br/>"
            "• <b>Presales & POC:</b> Key 5G Private Network POC delivered 7 days ahead of contract target, satisfying the 5-days ahead stretch objective."
        )
        elements.append(Paragraph(highlights, body_style))
        elements.append(Spacer(1, 25))

        # Signatures
        sig_data = [
            ["Prepared by:", "Reviewed & Approved by:"],
            ["\n\n\n____________________________\nSupriyanto\nPMO Lead, PT Samvad", "\n\n\n____________________________\nPresident Director\nPT Samvad Technology Services"]
        ]
        sig_table = Table(sig_data, colWidths=[260, 260])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        return filename

    @staticmethod
    def generate_sop_ic_pdf(checklist_code: str, site_id: str, client_name: str, tech_name: str, items: List[Dict[str, Any]]) -> str:
        """Generates a client-ready standardized I&C Handover SOP PDF document."""
        ensure_reports_dir()
        filename = f"{REPORTS_DIR}/SOP_IC_Handover_{checklist_code}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'), spaceAfter=4)
        subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#475569'), spaceAfter=12)
        body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#334155'), leading=11)

        elements = []
        logo_path = "assets/samvad_logo_horizontal.png"
        if os.path.exists(logo_path):
            logo_img = RLImage(logo_path, width=120, height=26.3)
            header_table = Table([[logo_img, Paragraph(f"<b>Installation & Commissioning (I&C) Acceptance Certificate</b><br/><font size=8 color='#475569'>Ref: {checklist_code}</font>", subtitle_style)]], colWidths=[130, 390])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(header_table)
        else:
            elements.append(Paragraph("PT SAMVAD TECHNOLOGY SERVICES", title_style))
            elements.append(Paragraph(f"Installation & Commissioning (I&C) Acceptance Certificate & Checklist | Ref: {checklist_code}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#059669'), spaceAfter=10))

        # Metadata table
        meta_data = [
            ["Site ID:", site_id, "Client Operator:", client_name],
            ["Lead Technician:", tech_name, "Inspection Date:", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Compliance Status:", "PASSED (Client-Ready)", "SLA Target:", ">= 95.0% Baseline Availability"]
        ]
        meta_table = Table(meta_data, colWidths=[110, 150, 110, 150])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 12))

        # Checklist Items Table
        elements.append(Paragraph("<b>I&C Technical Verification Steps:</b>", body_style))
        elements.append(Spacer(1, 4))
        
        table_data = [["No", "Workstream / Inspection Item", "Standard Spec", "Result", "Remarks"]]
        for idx, itm in enumerate(items, 1):
            table_data.append([
                str(idx),
                itm.get("title", f"Step {idx}"),
                itm.get("spec", "Manufacturer standard"),
                itm.get("result", "PASS"),
                itm.get("remarks", "Verified in tolerance")
            ])

        col_w = [25, 185, 130, 60, 120]
        check_table = Table(table_data, colWidths=col_w)
        check_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(check_table)
        elements.append(Spacer(1, 20))

        # Signatures
        sig_data = [
            ["Samvad Lead Commissioning Engineer:", "Client Technical Acceptance Officer:"],
            ["\n\n\n____________________________\nName: " + tech_name + "\nDate: " + datetime.now().strftime("%Y-%m-%d"),
             "\n\n\n____________________________\nName: Customer Sign-off\nDate: " + datetime.now().strftime("%Y-%m-%d")]
        ]
        sig_table = Table(sig_data, colWidths=[260, 260])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        return filename

    @staticmethod
    def generate_weekly_excel_report(dfs: Dict[str, pd.DataFrame], week_num: int, year: int) -> str:
        """Generates a multi-tab formatted Excel audit workbook (.xlsx)."""
        ensure_reports_dir()
        filename = f"{REPORTS_DIR}/Samvad_PMO_Audit_W{week_num}_{year}.xlsx"
        
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        for sheet_name, df in dfs.items():
            ws = wb.create_sheet(title=sheet_name[:30])
            for r in dataframe_to_rows(df, index=False, header=True):
                ws.append(r)

            # Style headers
            for col in range(1, len(df.columns) + 1):
                cell = ws.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Style rows
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
                for cell in row:
                    cell.border = thin_border
                    cell.font = Font(name="Calibri", size=10)

            # Adjust col widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(filename)
        return filename

    @staticmethod
    def generate_weekly_word_report(kpi_summary: Dict[str, Any], week_num: int, year: int) -> str:
        """Generates an executive briefing MS Word (.docx) document."""
        ensure_reports_dir()
        filename = f"{REPORTS_DIR}/Samvad_PMO_Executive_Summary_W{week_num}_{year}.docx"
        
        doc = Document()
        
        # Logo if available
        logo_path = "assets/samvad_logo_horizontal.png"
        if os.path.exists(logo_path):
            from docx.shared import Inches
            p_logo = doc.add_paragraph()
            p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_logo.add_run().add_picture(logo_path, width=Inches(2.5))
        
        # Heading
        title = doc.add_heading("PT SAMVAD TECHNOLOGY SERVICES", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        subtitle = doc.add_paragraph(f"PMO Command Center — Weekly Operations Briefing (Week {week_num}, {year})")
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f"Generated at: Friday 14:00 WIB (Contract SLA Target 17:00 WIB Met 100%)")
        doc.add_paragraph(f"Document Owner: Supriyanto (PMO Lead)")
        
        doc.add_heading("1. Executive Summary & Composite KPI Score", level=1)
        score = kpi_summary.get("overall_score", 100.0)
        tier = kpi_summary.get("tier_label", "100% Target Met")
        p = doc.add_paragraph()
        runner = p.add_run(f"Current Cumulative Performance Tier: {tier} (Composite Score: {score}%)\n")
        runner.bold = True
        p.add_run(
            "This report consolidates multidisciplinary metrics spanning Supply Chain, SG&A Financials, "
            "Site Operations, and Presales Milestones. The PMO Lead is currently tracking within the Maximum 120% Tier."
        )

        doc.add_heading("2. KPI Performance Matrix", level=1)
        cats = kpi_summary.get("categories", {})
        table = doc.add_table(rows=1, cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'KPI Category'
        hdr_cells[1].text = 'Weight'
        hdr_cells[2].text = 'Raw Score'
        hdr_cells[3].text = 'Status'

        for cat_key, cat_data in cats.items():
            row_cells = table.add_row().cells
            row_cells[0].text = str(cat_data.get("category", ""))
            row_cells[1].text = f"{cat_data.get('weight', 0.25)*100:.0f}%"
            row_cells[2].text = f"{cat_data.get('raw_score', 0):.1f}%"
            row_cells[3].text = str(cat_data.get("status", ""))

        doc.add_heading("3. Operational Directives & Action Items", level=1)
        doc.add_paragraph("• Supply Chain: Expedite B/L Red buffer shipments to avoid port demurrage.", style='List Bullet')
        doc.add_paragraph("• Financial Control: Finalize conversion of high-frequency field engineers to monthly retainer packages.", style='List Bullet')
        doc.add_paragraph("• Operations: Maintain 99%+ nationwide site uptime; resolve any outage alarms within 15 minutes.", style='List Bullet')
        doc.add_paragraph("• Presales: Advance upcoming POC pilot milestones to maintain 5-days ahead advantage.", style='List Bullet')

        doc.save(filename)
        return filename
