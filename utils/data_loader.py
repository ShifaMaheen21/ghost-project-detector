import pandas as pd
import sqlite3
import os

DB_PATH = 'database/ghost_project.db'

def load_all_data():
    conn = sqlite3.connect(DB_PATH)

    # Projects
    projects = pd.read_csv('data/sample_projects.csv')
    projects.to_sql('projects', conn, if_exists='append', index=False)
    print(f"[OK] Loaded {len(projects)} projects")

    # Contractors
    contractors = pd.read_csv('data/sample_contractors.csv')
    contractors.to_sql('contractors', conn, if_exists='append', index=False)
    print(f"[OK] Loaded {len(contractors)} contractors")

    # Market rates
    rates = pd.read_csv('data/market_rates.csv')
    rates.to_sql('market_rates', conn, if_exists='append', index=False)
    print(f"[OK] Loaded {len(rates)} market rates")

    # Quality parameters
    quality = pd.read_csv('data/quality_parameters.csv')
    quality.to_sql('quality_parameters', conn, if_exists='append', index=False)
    print(f"[OK] Loaded {len(quality)} quality parameters")

    # BOQ items
    boq = pd.read_csv('data/sample_boq.csv')
    boq.to_sql('boq_items', conn, if_exists='append', index=False)
    print(f"[OK] Loaded {len(boq)} BOQ items")

    conn.close()
    print("[OK] All sample data loaded successfully!")

if __name__ == "__main__":
    load_all_data()
