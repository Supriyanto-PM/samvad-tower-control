"""
Database connection and session handling for Samvad PMO-CC.
"""
import sqlite3
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from config.settings import DATABASE_PATH

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection object with row factory enabled."""
    path = db_path or DATABASE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
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
