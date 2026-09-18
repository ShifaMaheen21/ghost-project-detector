from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

app.secret_key = 'ghost-project-detector-dev-key-change-in-production'


from routes.reports import reports_bp

app.register_blueprint(reports_bp)

from routes.costs import costs_bp
app.register_blueprint(costs_bp)

DB_PATH = 'database/ghost_project.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    conn = get_db()
    projects = conn.execute('''
        SELECT p.*, c.contractor_name
        FROM projects p
        LEFT JOIN contractors c ON p.contractor_id = c.contractor_id
        ORDER BY p.risk_score DESC
    ''').fetchall()

    total = len(projects)
    on_track = len([p for p in projects if p['status'] == 'On Track'])
    delayed = len([p for p in projects if p['status'] == 'Delayed'])
    completed = len([p for p in projects if p['status'] == 'Completed'])
    suspicious = len([p for p in projects if p['status'] == 'Suspicious'])
    high_risk = len([p for p in projects if p['risk_level'] == 'High'])

    conn.close()
    return render_template('dashboard.html',
                           projects=projects,
                           total=total,
                           on_track=on_track,
                           delayed=delayed,
                           completed=completed,
                           suspicious=suspicious,
                           high_risk=high_risk)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    conn = get_db()

    # 1. Project + contractor
    project = conn.execute('''
        SELECT p.*, c.contractor_name, c.registration_number, c.score AS contractor_score
        FROM projects p
        LEFT JOIN contractors c ON p.contractor_id = c.contractor_id
        WHERE p.project_id = ?
    ''', (project_id,)).fetchone()

    if not project:
        conn.close()
        return "Project not found", 404

    # 2. Evidence
    evidence = conn.execute('''
        SELECT * FROM project_evidence
        WHERE project_id = ?
        ORDER BY captured_date DESC
    ''', (project_id,)).fetchall()

    # 3. Milestones
    milestones = conn.execute('''
        SELECT * FROM milestones
        WHERE project_id = ?
        ORDER BY expected_date ASC
    ''', (project_id,)).fetchall()

    # 4. Quality results (joined with parameters)
    quality_results = conn.execute('''
        SELECT qr.*, qp.parameter_name, qp.component, qp.unit,
               qp.expected_value, qp.criticality
        FROM project_quality_results qr
        JOIN quality_parameters qp ON qr.param_id = qp.param_id
        WHERE qr.project_id = ?
    ''', (project_id,)).fetchall()

    # 5. Citizen reports
    citizen_reports = conn.execute('''
        SELECT * FROM citizen_reports
        WHERE project_id = ?
        ORDER BY report_date DESC
    ''', (project_id,)).fetchall()

    # 6. Audit actions
    audit_actions = conn.execute('''
        SELECT * FROM audit_actions
        WHERE project_id = ?
        ORDER BY action_date DESC
    ''', (project_id,)).fetchall()

    conn.close()

    return render_template('project_detail.html',
                           project=project,
                           evidence=evidence,
                           milestones=milestones,
                           quality_results=quality_results,
                           citizen_reports=citizen_reports,
                           audit_actions=audit_actions)


if __name__ == '__main__':
    app.run(debug=True)
