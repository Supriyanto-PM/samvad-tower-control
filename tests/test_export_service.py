"""
Unit tests for ReportLab PDF, OpenPyXL Excel, and python-docx generation.
"""
import unittest
import os
import pandas as pd
from database.seed_data import seed_all_data
from services.kpi_engine import KPICalculator
from services.export_service import ExportService
from modules.module3_site_ops.sop_generator import SOPGenerator

class TestExportService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "database/test_export.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
        seed_all_data(cls.test_db)
        cls.kpi = KPICalculator(db_path=cls.test_db)
        cls.sop = SOPGenerator(db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def test_generate_weekly_pdf_report(self):
        summary = self.kpi.get_overall_kpi_summary()
        pdf_path = ExportService.generate_weekly_pdf_report(summary, week_num=36, year=2026)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)

    def test_generate_sop_ic_pdf(self):
        items = self.sop.get_standard_template()
        pdf_path = ExportService.generate_sop_ic_pdf("TEST-001", "SVD-JKT-001", "Telkomsel", "Supriyanto", items)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)

    def test_generate_weekly_excel_report(self):
        dfs = {
            "Sheet1": pd.DataFrame([{"A": 1, "B": 2}]),
            "Sheet2": pd.DataFrame([{"Name": "Test Site", "Uptime": 99.8}])
        }
        xlsx_path = ExportService.generate_weekly_excel_report(dfs, week_num=36, year=2026)
        self.assertTrue(os.path.exists(xlsx_path))
        self.assertGreater(os.path.getsize(xlsx_path), 1000)

    def test_generate_weekly_word_report(self):
        summary = self.kpi.get_overall_kpi_summary()
        docx_path = ExportService.generate_weekly_word_report(summary, week_num=36, year=2026)
        self.assertTrue(os.path.exists(docx_path))
        self.assertGreater(os.path.getsize(docx_path), 1000)

if __name__ == '__main__':
    unittest.main()
