"""
Database connection and session handling for Samvad PMO-CC.
"""
import sqlite3
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from config.settings import DATABASE_PATH

_GOVERNANCE_SCHEMA_INITIALIZED = False

def ensure_governance_schema(conn: Optional[sqlite3.Connection] = None) -> None:
    """Ensures governance audit and team assignment columns exist on timor_sites_100."""
    global _GOVERNANCE_SCHEMA_INITIALIZED
    if _GOVERNANCE_SCHEMA_INITIALIZED:
        return
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(timor_sites_100)")
        existing_cols = {row[1] for row in cur.fetchall()}
        if existing_cols:
            columns_to_add = [
                ("assigned_team", "TEXT DEFAULT NULL"),
                ("updated_at", "TEXT DEFAULT NULL"),
                ("last_updated_by", "TEXT DEFAULT NULL"),
                ("blocker_reason", "TEXT DEFAULT NULL")
            ]
            for col_name, col_def in columns_to_add:
                if col_name not in existing_cols:
                    cur.execute(f"ALTER TABLE timor_sites_100 ADD COLUMN {col_name} {col_def}")
            
            # PaaS Rollout Scope Migration:
            # PaaS provider does not do civil construction. Civil status is removed.
            # Sites awaiting TowerCo civil readiness are flagged with Civil Dependency.
            cur.execute("""
                UPDATE timor_sites_100 
                SET paas_status = '🔴 Blocked / Dependency', 
                    readiness_gate = 'HOLD (Civil Dependency)',
                    blocker_reason = '[Civil Dependency] Tower foundation / plinth not ready by TowerCo'
                WHERE paas_status LIKE '%Civil%' AND (readiness_gate LIKE '%HOLD%' OR readiness_gate LIKE '%Civil%')
            """)
            cur.execute("""
                UPDATE timor_sites_100 
                SET paas_status = '🟣 Power I&C Active', 
                    readiness_gate = 'GO (Dispatch Ready)'
                WHERE paas_status LIKE '%Civil%'
            """)
            cur.execute("""
                UPDATE timor_sites_100
                SET readiness_gate = 'G4 - Acceptance Testing [GO]'
                WHERE readiness_gate LIKE '%Civil Readiness%'
            """)
            cur.execute("""
                UPDATE timor_sites_100
                SET readiness_gate = 'Passed - Site Ready for Installation'
                WHERE readiness_gate = 'Passed - Civil Construction'
            """)
            conn.commit()

        # Ensure paas_field_teams table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS paas_field_teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_code TEXT UNIQUE NOT NULL,
                team_name TEXT NOT NULL,
                lead_name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                crew_size INTEGER DEFAULT 4,
                contact_number TEXT DEFAULT NULL,
                status TEXT DEFAULT 'On-Site Active',
                created_at TEXT DEFAULT NULL,
                updated_at TEXT DEFAULT NULL,
                current_lat REAL DEFAULT NULL,
                current_lon REAL DEFAULT NULL,
                last_checkin_at TEXT DEFAULT NULL,
                last_checkin_site TEXT DEFAULT NULL,
                checkin_status TEXT DEFAULT 'Unconfirmed',
                battery_pct INTEGER DEFAULT 95
            )
        """)

        # Add tracking columns if table was created previously without them
        cur.execute("PRAGMA table_info(paas_field_teams)")
        team_cols = {row[1] for row in cur.fetchall()}
        team_cols_to_add = [
            ("current_lat", "REAL DEFAULT NULL"),
            ("current_lon", "REAL DEFAULT NULL"),
            ("current_address", "TEXT DEFAULT NULL"),
            ("last_checkin_at", "TEXT DEFAULT NULL"),
            ("last_checkin_site", "TEXT DEFAULT NULL"),
            ("checkin_status", "TEXT DEFAULT 'Unconfirmed'"),
            ("battery_pct", "INTEGER DEFAULT 95")
        ]
        for cname, cdef in team_cols_to_add:
            if cname not in team_cols:
                cur.execute(f"ALTER TABLE paas_field_teams ADD COLUMN {cname} {cdef}")

        # Ensure field_checkin_logs table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS field_checkin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_code TEXT NOT NULL,
                site_id TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                address TEXT DEFAULT NULL,
                accuracy_m REAL DEFAULT 10.0,
                checkin_status TEXT NOT NULL,
                checkin_time TEXT NOT NULL,
                user_agent TEXT,
                notes TEXT
            )
        """)

        # Add address to field_checkin_logs if table was created previously without it
        cur.execute("PRAGMA table_info(field_checkin_logs)")
        log_cols = {row[1] for row in cur.fetchall()}
        if "address" not in log_cols:
            cur.execute("ALTER TABLE field_checkin_logs ADD COLUMN address TEXT DEFAULT NULL")

        # Ensure geo_address_cache table exists for fast 0.1ms reverse geocode caching
        cur.execute("""
            CREATE TABLE IF NOT EXISTS geo_address_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lat_round REAL NOT NULL,
                lon_round REAL NOT NULL,
                address TEXT NOT NULL,
                details_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lat_round, lon_round)
            )
        """)

        # Ensure geo_route_cache table exists for 0.1ms road routing & ETA caching
        cur.execute("""
            CREATE TABLE IF NOT EXISTS geo_route_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_lat REAL NOT NULL,
                origin_lon REAL NOT NULL,
                dest_lat REAL NOT NULL,
                dest_lon REAL NOT NULL,
                road_dist_km REAL NOT NULL,
                duration_minutes REAL NOT NULL,
                duration_formatted TEXT NOT NULL,
                route_source TEXT DEFAULT 'OSRM_HIGHWAY',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(origin_lat, origin_lon, dest_lat, dest_lon)
            )
        """)
        
        # Track seeding status via system_metadata so that user can clear all teams to 0 without auto-reseeding
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # paas_field_teams table is kept empty by default for clean real WhatsApp testing.
        # Field teams can be registered dynamically by coordinators.
        _GOVERNANCE_SCHEMA_INITIALIZED = True

        _GOVERNANCE_SCHEMA_INITIALIZED = True
    except Exception:
        pass
    finally:
        if should_close:
            conn.close()

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection object with row factory enabled."""
    path = db_path or DATABASE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    ensure_governance_schema(conn)
    return conn

def init_db(db_path: Optional[str] = None, schema_file: str = "database/schema.sql") -> None:
    """Initializes the SQLite schema if tables do not exist."""
    path = db_path or DATABASE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Read schema
    if os.path.exists(schema_file):
        with open(schema_file, "r", encoding="utf-8") as f:
            sql_script = f.read()
    else:
        # Fallback if relative path differs
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        alt_path = os.path.join(base_dir, schema_file)
        with open(alt_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
            
    conn = get_connection(path)
    try:
        conn.executescript(sql_script)
        conn.commit()
    finally:
        conn.close()

def query_df(sql: str, params: tuple = (), db_path: Optional[str] = None) -> pd.DataFrame:
    """Executes a SQL query and returns results as a pandas DataFrame."""
    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()

def execute_write(sql: str, params: tuple = (), db_path: Optional[str] = None) -> int:
    """Executes an INSERT/UPDATE/DELETE query and returns the last row ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
