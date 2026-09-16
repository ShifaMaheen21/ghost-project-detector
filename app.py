from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)
