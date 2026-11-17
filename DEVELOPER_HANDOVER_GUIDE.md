# SAMVAD PMO COMMAND CENTER (PMO-CC)
## Panduan Lengkap Serah Terima Teknis & Instruksi Pengembangan (Developer Handover Guide)
**PT Samvad Technology Services | Timor-Leste 100 Sites National Rollout Project**  
*Document Owner: PMO Lead | Version: 2.0 (November 2026)*

---

## 1. Ringkasan Eksekutif & Tujuan Dokumen

Dokumen ini disusun sebagai panduan resmi serah terima teknis (*technical handover*) dari purwarupa fungsional (*functional working prototype*) yang dikembangkan pada lingkungan Google Antigravity menuju implementasi produksi tingkat korporat (*production enterprise deployment*) oleh tim software engineering / IT perusahaan.

Sistem **SAMVAD PMO Command Center** mengonsolidasikan seluruh tata kelola operasional proyek percepatan infrastruktur telekomunikasi di Timor-Leste (100 tower sites Telkomcel), mencakup:
1. **Pemetaan & Rute Jalan Riil 100 Site**: Analisis jaringan jalan darat nasional Google Maps dari Central Staging / Port Dili ke seluruh 11 distrik di 5 zona operasional (bukan jarak lurus/udara).
2. **Model Bahan Bakar Armada Lapangan**: Kalkulasi konsumsi solar untuk armada Mitsubishi Triton 4x4 Double Cabin (atau Toyota Hilux 4WD) pada kondisi beban kerja maksimal (*worst-case payload* ~2,8 ton) dan konversi biaya resmi USD ($).
3. **Pusat Radar GPS & Telemetri Tim**: Pelacakan posisi tim teknisi, verifikasi radius geofencing site, dan log check-in kedatangan.
4. **Digitalisasi SOP IC Handover**: Formulir berita acara komisioning rectifier, bank baterai LiFePO4, genset, dan penerbitan berkas BAST PDF otomatis.
5. **Kontrol Finansial & SLA Presales**: Disiplin anggaran SG&A (< 12%), optimasi manpower harian ke retainer bulanan, dan audit kepatuhan ketersediaan daya menara (SLA >= 95.0%).

---

## 2. Struktur Direktori Proyek

```text
Samvad Tower Control/
├── app.py                      # Core Streamlit Web Application & PMO Command Center Entrypoint
├── DEVELOPER_HANDOVER_GUIDE.md # Dokumen panduan serah terima ini
├── requirements.txt            # Daftar dependensi Python resmi
├── README.md                   # Dokumen spesifikasi arsitektur awal
├── start_samvad.command        # Skrip otomatis 1-klik untuk menjalankan server di macOS
├── stop_samvad.command         # Skrip otomatis untuk menghentikan server di macOS
├── start_tunnel.sh             # Skrip automasi Cloudflare tunnel
├── tunnel_url.txt              # Cache alamat domain aktif Cloudflare
│
├── database/                   # Modul Basis Data & Seed Engine
│   ├── connection.py           # Database connection manager (SQLite / Extensible to Postgres)
│   ├── schema.sql              # Definisi DDL 25 tabel database relasional
│   ├── timor_sites_data.py     # Master dataset 100 site Telkomcel & algoritma rute darat
│   ├── multi_tenant_data.py    # Skema multi-tenant operator (IOH, Mitratel, Telkomcel, XL)
│   ├── pmo_command_center.db   # Database master SQLite aktif
│   └── seed_data.py            # Generator data awal untuk simulasi
│
├── services/                   # Business Logic & Service Engine (Modular Tier)
│   ├── fleet_tracking_service.py     # Pelacakan GPS radar, geofencing, penugasan tim
│   ├── excel_sync_service.py         # Generator & parser Excel Master Tracker, Google Sheets sync
│   ├── rollout_operations_service.py # Tata kelola gelombang peluncuran (Waves) & Readiness Gate
│   ├── kpi_engine.py                 # Multi-category weighted KPI engine (Target 120% Tier)
│   ├── data_management_service.py    # CRUD tabel teknis & audit ledger
│   ├── noc_integration_service.py    # Sinkronisasi alarm eksternal & snapshot KPI
│   ├── mobile_checkin_handler.py     # Parser koordinat GPS dari mobile browser teknisi
│   ├── export_service.py             # Generator laporan BAST PDF (ReportLab), Word, Excel
│   └── notification_service.py       # Dispatcher notifikasi WhatsApp & Telegram
│
├── modules/                    # Modul Fungsional Antarmuka
│   ├── module1_customs/        # Tracker rantai pasok kepabeanan (Customs SLA Buffer)
│   ├── module2_sga/            # Kalkulator disiplin SG&A & manpower optimizer
│   ├── module3_site_ops/       # Monitor ketersediaan daya menara & generator SOP IC
│   └── module4_reporting/      # Pelapor otomatis SLA mingguan & pelacak POC presales
│
├── reports/                    # Berkas Acuan Spreadsheet & Output Audit Resmi
│   ├── Timor_Leste_100_Sites_Zone_Distance_Fuel_Analysis.xlsx # Master Acuan 100 Site & BBM
│   ├── Samvad_Master_Tracker.xlsx                             # Master Spreadsheet Multi-Tenant
│   ├── Samvad_PMO_Audit_W36_2026.xlsx                        # Berkas audit SLA ketersediaan
│   ├── Samvad_PMO_Executive_Summary_W36_2026.docx             # Ringkasan eksekutif Word
│   ├── Samvad_PMO_Weekly_Report_W36_2026.pdf                 # Laporan audit PDF mingguan
│   └── SOP_IC_Handover_IC-SVD-SVD-JKT-001-202610201124.pdf   # Contoh BAST SOP komisioning
│
└── tests/                      # Rangkaian Uji Otomatis (Unit Test Suite - 63 Tests)
    ├── test_timor_100_sites.py      # Verifikasi rute, jarak darat, zona, dan prioritas P0-P3
    ├── test_fleet_tracking.py       # Uji telemetri GPS, radius geofence, assignment links
    ├── test_rollout_governance.py   # Uji kesiapan gerbang (GO/HOLD/ESCALATE) & wave sequencing
    ├── test_noc_integration.py      # Uji sinkronisasi alarm dan snapshot outage
    ├── test_data_management.py      # Uji integritas CRUD data teknis dan audit ledger
    └── test_navigation.py           # Uji routing URL portal mobile dan query parameters
```

---

## 3. Panduan Setup & Eksekusi Cepat (Quick Start Guide)

### A. Persyaratan Sistem (*Prerequisites*)
- Python versi 3.9, 3.10, atau 3.11.
- Sistem Operasi: macOS, Linux (Ubuntu/Debian), atau Windows 10/11.
- Git & Git Bash (untuk Windows).

### B. Langkah Instalasi

#### Di macOS / Linux:
```bash
# 1. Buka terminal pada folder proyek
cd "Samvad Tower Control"

# 2. Buat virtual environment mandiri
python3 -m venv .venv

# 3. Aktifkan virtual environment
source .venv/bin/activate

# 4. Pasang seluruh pustaka dependensi
pip install --upgrade pip
pip install -r requirements.txt
```

#### Di Windows:
```cmd
# 1. Buka Command Prompt / PowerShell pada folder proyek
cd "Samvad Tower Control"

# 2. Buat virtual environment
python -m venv .venv

# 3. Aktifkan virtual environment
.venv\Scripts\activate

# 4. Pasang pustaka dependensi
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Verifikasi Mutu Kode (Menjalankan Unit Test)

Sebelum melakukan perubahan kode apa pun, tim developer wajib menjalankan unit test untuk memastikan integritas logika bisnis:

```bash
python -m unittest discover tests
```

**Target Kelulusan:**
```text
Ran 63 tests in 0.620s
OK
```
Semua 63 skenario uji mencakup validasi jarak darat Google Maps, model konsumsi solar, perhitungan SLA, dan verifikasi geofencing GPS lapangan.

---

## 5. Menjalankan Server Aplikasi

Jalankan perintah berikut:

```bash
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

### Akses Aplikasi Melalui Browser:
1. **Dasbor PMO Command Center Utama**:
   - URL: `http://localhost:8502` atau `http://127.0.0.1:8502`
2. **Simulasi Portal Ponsel Teknisi Lapangan (*Mobile Dispatch View*)**:
   - URL: `http://localhost:8502/?page=field_portal&team=SVD-TL-ALPHA&site=DAX001`

---

## 6. Spesifikasi Logika Bisnis & Rumus Operasional Kunci

Developer yang melanjutkan sistem ini wajib memahami 3 formula operasional utama yang telah ditanamkan ke dalam kode:

### A. Formula Jarak Rute Darat vs Udara (*Circuity Factor*)
- Jarak lurus (*Haversine*) terbukti menyesatkan di Timor-Leste karena terhalang jalur pegunungan terjal dan lembah sungai.
- Pada berkas `database/timor_sites_data.py`, jarak darat dihitung dengan koefisien kelokan nyata:
  - **Zona 1 (Dili & Liquica)**: Circuity factor **1.25x - 1.28x** dari jarak udara (minimum 2.5 km).
  - **Zona 2 (Pantai Utara)**: Circuity factor **1.34x - 1.40x** via Estrada Nacional 1 (A01).
  - **Zona 3 (Pesisir Selatan)**: Circuity factor **1.52x - 1.68x** menembus perlintasan pegunungan Maubisse/Ainaro.
  - **Zona 4 (Pegunungan Ermera & Bobonaro)**: Circuity factor **1.68x** mendaki lereng >1.500m dpl dengan gigi rendah 4WD.
  - **Zona 5 (Enklave Oecusse)**: Transit ferri maritim Berlin Nakroma (142 km) + rute darat lingkar enklave (6–14 km).

### B. Model Konsumsi Bahan Bakar (Worst-Case Maximum Payload)
- Platform: **Mitsubishi Triton 4x4 Double Cabin 2.4L/2.5L Diesel** (atau Toyota Hilux 4WD).
- Bobot kerja maksimal: ~2.800 kg GVW (kabin penuh, AC dingin 100%, peralatan hidrolik, tangga teleskopik 8m, modul rectifier, baterai darurat).
- Efisiensi per zona:
  - Zona 1: **6.5 km/L** (15.4 L/100km - macet kota).
  - Zona 2: **6.0 km/L** (16.7 L/100km - tanjakan pesisir & angin laut).
  - Zona 3: **5.0 km/L** (20.0 L/100km - jalan berbatu & lumpur sungai).
  - Zona 4: **4.5 km/L** (22.2 L/100km - tanjakan ekstrem, 4WD low range gigi 1–2).
  - Zona 5: **5.5 km/L** (18.2 L/100km - jalan berbatu pedalaman enklave).
- Alokasi idle di lokasi site: **2.5 Liter per kunjungan** (mesin menyala untuk menyuplai inverter 240V pengujian rectifier/genset).
- Harga acuan solar Timor-Leste: **$1.25/L (Dili)** dan **$1.30–$1.35/L (Distrik Luar)**.

### C. Formula Prioritas Peluncuran (P0–P3 Priority Index)
- Dihitung di `database/timor_sites_data.py`:
  $$\text{Priority Index} = (0.45 \times \text{Criticality}) + (0.20 \times \text{Revenue}) + (0.20 \times \text{Resilience}) + (0.15 \times \text{DG Status}) + \text{Extreme Bonus}$$

---

## 7. Rencana Peningkatan untuk Tim Developer Perusahaan (Roadmap)

Untuk mengubah prototipe ini menjadi produk korporat mandiri (*production-grade software*):

1. **Deploy ke Server Cloud Mandiri (VPS Linux)**:
   - Pasang aplikasi di VPS (DigitalOcean / AWS / GCP) menggunakan Docker atau Systemd Daemon agar berjalan 24/7 tanpa laptop.
   - Sambungkan domain permanen perusahaan (misal: `https://pmo.samvad.com`) dengan sertifikat SSL gratis dari Let's Encrypt / Cloudflare.
2. **Migrasi Database ke PostgreSQL**:
   - Skema DDL pada `database/schema.sql` telah dirancang kompatibel dengan PostgreSQL. Developer cukup mengganti *connection string* di `database/connection.py`.
3. **Peningkatan Aplikasi Teknisi Lapangan (PWA / Flutter)**:
   - Buat aplikasi Android mandiri atau Progressive Web App (PWA) agar pelacakan GPS dapat terus berjalan di latar belakang (*native background location service*) saat layar ponsel teknisi mati atau berada di dalam saku.
4. **Otentikasi & Manajemen Pengguna (RBAC)**:
   - Tambahkan sistem login berbasis JWT token untuk membedakan hak akses: Admin PMO, Koordinator Lapangan, Teknisi, dan Eksekutif Klien.

---
*Dokumen ini diterbitkan oleh PMO Lead PT Samvad Technology Services sebagai aset serah terima resmi proyek Rollout 100 Sites Timor-Leste.*
