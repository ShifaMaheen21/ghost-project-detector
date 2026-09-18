from flask import Blueprint, render_template
import sqlite3

contractors_bp = Blueprint('contractors', __name__)

DB_PATH = 'database/ghost_project.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def compute_score(contractor):
    """Weighted score 0-100.
       Starts at 100, penalized for late/failed/legal.
       Bonuses for on-time completions."""
    total = contractor['total_projects'] or 0
    if total == 0:
        return 50  # unproven

    on_time = contractor['completed_on_time'] or 0
    late = contractor['completed_late'] or 0
    failed = contractor['projects_failed'] or 0
    legal = contractor['legal_cases'] or 0

    on_time_rate = (on_time / total) * 100
    late_penalty = (late / total) * 30
    failed_penalty = (failed / total) * 60
    legal_penalty = min(legal * 8, 30)

    score = on_time_rate + (100 - on_time_rate) * 0.3 - late_penalty - failed_penalty - legal_penalty
    score = max(0, min(100, round(score)))
    return score

def risk_bucket(score):
    if score >= 70:
        return 'GOOD'
    if score >= 40:
        return 'AVERAGE'
    return 'BAD'

@contractors_bp.route('/contractors')
def contractors():
    conn = get_db()

    rows = conn.execute('SELECT * FROM contractors ORDER BY contractor_id').fetchall()

    contractors_list = []
    for c in rows:
        score = compute_score(c)
        contractors_list.append({
            'contractor_id': c['contractor_id'],
            'contractor_name': c['contractor_name'],
            'registration_number': c['registration_number'],
            'total_projects': c['total_projects'],
            'completed_on_time': c['completed_on_time'],
            'completed_late': c['completed_late'],
            'projects_failed': c['projects_failed'],
            'legal_cases': c['legal_cases'],
            'score': score,
            'bucket': risk_bucket(score)
        })

    # Sort worst first (so blacklist candidates appear at top)
    contractors_list.sort(key=lambda x: x['score'])

    blacklist = [c for c in contractors_list if c['score'] < 40]

    conn.close()
    return render_template('contractor_scoring.html',
                           contractors=contractors_list,
                           blacklist=blacklist)

@contractors_bp.route('/fraud-network')
def fraud_network():
    conn = get_db()

    # 1. Duplicate photo hashes across reports
    duplicate_photos = conn.execute('''
        SELECT
            r.photo_hash,
            COUNT(*) AS occurrences,
            GROUP_CONCAT(r.report_id) AS report_ids,
            GROUP_CONCAT(p.project_name) AS project_names
        FROM citizen_reports r
        LEFT JOIN projects p ON r.project_id = p.project_id
        WHERE r.photo_hash IS NOT NULL AND r.photo_hash != ''
        GROUP BY r.photo_hash
        HAVING COUNT(*) > 1
        ORDER BY occurrences DESC
    ''').fetchall()

    # 2. Contractors on multiple high-risk projects
    risky_contractors = conn.execute('''
        SELECT
            c.contractor_id,
            c.contractor_name,
            c.registration_number,
            COUNT(p.project_id) AS risky_project_count,
            GROUP_CONCAT(p.project_name) AS project_names
        FROM contractors c
        JOIN projects p ON p.contractor_id = c.contractor_id
        WHERE p.risk_level = 'High'
        GROUP BY c.contractor_id
        HAVING COUNT(p.project_id) > 1
        ORDER BY risky_project_count DESC
    ''').fetchall()

    # 3. Same-amount tenders by same project cluster (basic pattern)
    suspicious_tenders = conn.execute('''
        SELECT
            t1.tender_id AS tender_a,
            t2.tender_id AS tender_b,
            t1.tender_amount,
            t1.tender_title AS title_a,
            t2.tender_title AS title_b
        FROM tenders t1
        JOIN tenders t2
          ON t1.tender_amount = t2.tender_amount
         AND t1.tender_id < t2.tender_id
        ORDER BY t1.tender_amount DESC
        LIMIT 10
    ''').fetchall()

    conn.close()

    return render_template('fraud_network.html',
                           duplicate_photos=duplicate_photos,
                           risky_contractors=risky_contractors,
                           suspicious_tenders=suspicious_tenders)
