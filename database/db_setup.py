import sqlite3
import os

DB_PATH = 'database/ghost_project.db'

def create_database():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT NOT NULL,
        project_type TEXT,
        state TEXT,
        district TEXT,
        village TEXT,
        latitude REAL,
        longitude REAL,
        boundary TEXT,
        budget REAL,
        contractor_id INTEGER,
        start_date TEXT,
        expected_end_date TEXT,
        actual_end_date TEXT,
        status TEXT DEFAULT 'On Track',
        progress_percent INTEGER DEFAULT 0,
        claimed_completion REAL DEFAULT 0,
        observed_completion REAL DEFAULT 0,
        financial_paid REAL DEFAULT 0,
        emb_completion REAL DEFAULT 0,
        risk_score INTEGER DEFAULT 0,
        risk_level TEXT DEFAULT 'Low'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contractors (
        contractor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        contractor_name TEXT NOT NULL,
        registration_number TEXT,
        total_projects INTEGER DEFAULT 0,
        completed_on_time INTEGER DEFAULT 0,
        completed_late INTEGER DEFAULT 0,
        projects_failed INTEGER DEFAULT 0,
        legal_cases INTEGER DEFAULT 0,
        score INTEGER DEFAULT 50
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS milestones (
        milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        milestone_name TEXT,
        expected_date TEXT,
        actual_date TEXT,
        status TEXT DEFAULT 'Pending'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS citizen_reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        citizen_name TEXT,
        report_type TEXT,
        description TEXT,
        latitude REAL,
        longitude REAL,
        photo_path TEXT,
        photo_hash TEXT,
        gps_valid INTEGER DEFAULT 0,
        report_date TEXT,
        status TEXT DEFAULT 'Pending'
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_rates (
        rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_name TEXT,
        unit TEXT,
        market_rate REAL,
        last_updated TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tenders (
        tender_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        tender_title TEXT,
        tender_amount REAL,
        publish_date TEXT,
        deadline_date TEXT,
        status TEXT DEFAULT 'Open'
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS escrow_accounts (
        escrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        total_amount REAL,
        released_amount REAL DEFAULT 0,
        balance_amount REAL,
        last_release_date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS whistleblower_reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        description TEXT,
        evidence_path TEXT,
        report_date TEXT,
        status TEXT DEFAULT 'New'
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_evidence (
        evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        evidence_type TEXT,
        observed_value REAL,
        score REAL,
        source TEXT,
        captured_date TEXT,
        notes TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quality_parameters (
        param_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_type TEXT,
        component TEXT,
        parameter_name TEXT,
        unit TEXT,
        expected_value REAL,
        min_value REAL,
        max_value REAL,
        criticality TEXT,
        weight REAL,
        measurement_method TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_quality_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        param_id INTEGER,
        observed_value REAL,
        status TEXT,
        confidence REAL,
        evidence_id INTEGER,
        notes TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_actions (
        action_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        action_type TEXT,
        notes TEXT,
        action_date TEXT,
        auditor_name TEXT
    )
    ''')

	    # ============ 13. BOQ ITEMS ============
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS boq_items (
        boq_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        material_name TEXT,
        unit TEXT,
        boq_quantity REAL,
        emb_quantity REAL,
        observed_quantity REAL,
        discrepancy_percent REAL DEFAULT 0,
        status TEXT DEFAULT 'Pending'
    )
    ''')


    conn.commit()
    conn.close()
    print("[OK] Database created with 12 tables at", DB_PATH)

if __name__ == "__main__":
    create_database()
