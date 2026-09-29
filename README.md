# Samvad PMO Command Center (PMO-CC)
### Operational Automation & KPI Alignment Platform
**PT Samvad Technology Services**  
*Document Owner: Supriyanto (PMO Lead) | Version: 1.0 (September 7, 2026)*

---

## 📌 Executive Summary

**Samvad PMO Command Center (PMO-CC)** adalah platform otomasi operasional terpadu yang dirancang khusus untuk memfasilitasi tugas multidisiplin PMO Lead PT Samvad Technology Services. Sistem ini mengonsolidasikan rantai pasok (*Supply Chain*), kontrol finansial (*SG&A Financial Discipline*), operasi jaringan menara (*Site Availability & SLA*), serta pelaporan presales (*SLA Auto-Reporter*) ke dalam satu dashboard terintegrasi guna mengamankan target kinerja **Maximum 120% Performance Tier** (sesuai Annex B Employment Agreement).

---

## 🎯 KPI Alignment Matrix (PRD Section 4)

| Contract KPI Category | Weight | Application Module | Target Automation Goal |
| :--- | :---: | :--- | :--- |
| **A. Supply Chain & Partners** | **25%** | **Module 1: Customs Guardian** | 0% logistics delays, visual SLA buffer alerts (Green/Yellow/Red), and competitor intelligence pricing database for cost pushback. |
| **B. Financial Control** | **25%** | **Module 2: SG&A Sentinel** | Enforce project SG&A < 12% in Year 1, optimize manpower structures (convert high-frequency daily engineers to monthly retainers), and track client gross margin improvements. |
| **C. Operations & Uptime** | **25%** | **Module 3: Site SLA Dashboard** | Maintain site availability $\ge$ 95.0% contract threshold, trigger instant emergency alerts for outages > 15 mins, and generate standardized client-ready I&C SOP PDFs. |
| **D. Presales & SLA Reporting** | **25%** | **Module 4: SLA Auto-Reporter** | Auto-extract and compile weekly reports every Friday at 14:00 WIB (100% compliance before 17:00 WIB deadline), and track POC milestones against 5-days ahead stretch targets. |

---

## 🏗️ Architecture & Project Structure

```
Samvad Tower Control/
├── app.py                      # Main Streamlit web application & Executive Command Center
├── config/                     # Settings, KPI specifications, and operational thresholds
│   ├── __init__.py
│   └── settings.py
├── database/                   # SQLite database schema, persistence layer, & seed data
│   ├── __init__.py
│   ├── connection.py
│   ├── schema.sql
│   └── seed_data.py
├── modules/                    # 4 Core PRD Operational Modules
│   ├── module1_customs/        # Customs Milestone Tracker, SLA Buffer Alerts & Competitor Hub
│   │   ├── tracker.py
│   │   ├── competitor_hub.py
│   │   └── ui.py
│   ├── module2_sga/            # SG&A Ratio Calculator, Manpower Optimizer & Margin Tracker
│   │   ├── sga_calculator.py
│   │   ├── manpower_optimizer.py
│   │   ├── margin_optimizer.py
│   │   └── ui.py
│   ├── module3_site_ops/       # Uptime Monitor, Emergency Outage Dispatch & SOP Generator
│   │   ├── uptime_monitor.py
│   │   ├── sop_generator.py
│   │   └── ui.py
│   └── module4_reporting/      # Friday 14:00 Auto-Reporter & POC Gantt Stretch Tracker
│       ├── auto_reporter.py
│       ├── poc_tracker.py
│       └── ui.py
├── services/                   # Shared Platform Services
│   ├── kpi_engine.py           # Multi-category weighted calculation engine (120% Tier)
│   ├── notification_service.py # Telegram Bot & WhatsApp Webhook dispatcher
│   └── export_service.py       # Client-ready PDF (ReportLab), Excel (OpenPyXL), & Word (Docx)
├── reports/                    # Auto-generated weekly and SOP reports (.pdf, .docx, .xlsx)
├── tests/                      # Automated unit test suite
│   ├── test_kpi_engine.py
│   ├── test_sga_calculator.py
│   ├── test_uptime_sla.py
│   └── test_export_service.py
├── requirements.txt            # Python dependencies
└── README.md                   # System documentation
```

---

## 🚀 Quickstart & Installation

### 1. Prasyarat Sistem
- Python 3.9+ (Python 3.12 direkomendasikan sesuai PRD)
- Lingkungan virtual environment

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Buat virtual environment
python3 -m venv .venv

# Aktifkan virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Menjalankan Aplikasi Streamlit
```bash
# Jalankan aplikasi Command Center
streamlit run app.py
```
Aplikasi akan otomatis terbuka di browser pada `http://localhost:8501`.

---

## ⚙️ Menjalankan Automated Unit Tests
```bash
.venv/bin/python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📦 Fitur-Fitur Utama Setiap Modul

### 1. Module 1: Supply Chain & Customs Guardian
- **Customs Milestone Tracker**: Pelacakan nomor B/L terhadap milestone pelabuhan (Port of Origin, Ocean Transit, Port Arrival, Red/Yellow Channel Customs Inspection, Delivered to Warehouse).
- **SLA Buffer Alerts**: Sistem visualisasi status (Green/Yellow/Red) berdasarkan sisa hari buffer antara ETA dan tanggal deadline *commissioning* proyek.
- **Competitor Intelligence Hub**: Database harga vendor kompetitor dan kalkulator *Supplier Cost Pushback* dengan rekomendasi taktik negosiasi.

### 2. Module 2: SG&A & Manpower Financial Sentinel
- **SG&A Ratio Calculator**: Pemantauan pengeluaran perjalanan site, logistik lokal, dan admin secara dinamis terhadap batas ketat **12.0% Year 1** dilengkapi *gauge chart*.
- **Manpower Cost Optimizer**: Audit otomatis utilisasi kunjungan harian teknisi/engineer. Rekomendasi otomatis konversi ke paket *fixed monthly retainer* untuk teknisi frekuensi tinggi (menghemat jutaan rupiah per bulan).
- **Client-Side Margin Optimizer**: Tracking implementasi efisiensi energi (*Solar Hybrid*, DC Aircon VSD, *Passive Sharing*) dan dampaknya terhadap kenaikan *gross margin*.

### 3. Module 3: Site Availability & SLA Operations
- **Real-time Uptime Dashboard**: Monitoring ketersediaan seluruh site aktif dan POC telekomunikasi terhadap standar kontrak $\ge 95.0\%$.
- **Emergency Outage Sentinel**: Deteksi insiden down $> 15$ menit dan pemicu notifikasi darurat instan via **Telegram Bot** atau **Twilio WhatsApp API**.
- **Digital I&C SOP Generator**: Checklist digital interaktif dari pemasangan mekanikal, RF/antena, fiber optik, hingga pentanahan yang langsung mengompilasi berkas PDF standar serah terima klien (*Client-Ready I&C Certificate*).

### 4. Module 4: SLA Reporting & Presales Engine
- **Friday 14:00 Auto-Reporter**: Mengambil performa aktual dari Modul 1, 2, dan 3 setiap Jumat pukul 14:00 WIB dan mengompilasi berkas PDF, Word (.docx), dan Excel (.xlsx) sebelum batas akhir 17:00 WIB (100% kepatuhan kontrak).
- **POC Gantt & Milestone Tracker**: Timeline interaktif presentasi teknis dan pilot deployment dengan highlight penanda *'5-days ahead' stretch target*.

---

## 🔒 Konfigurasi Notifikasi (Opsional)
Untuk mengaktifkan pengiriman notifikasi nyata ke Telegram atau WhatsApp, atur variabel lingkungan berikut di sistem Anda atau melalui tab **System Settings** di aplikasi:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_or_channel_id"
export WHATSAPP_API_URL="https://your-whatsapp-gateway.com/send"
export WHATSAPP_TOKEN="your_token"
```
Jika tidak dikonfigurasi, sistem akan otomatis berjalan dalam mode **Simulasi & Audit Trail Log**, sehingga seluruh aktivitas tercatat aman di database tanpa menyebabkan galat.
