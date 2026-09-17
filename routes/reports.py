from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import os
import hashlib

reports_bp = Blueprint('reports', __name__)

DB_PATH = 'database/ghost_project.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@reports_bp.route('/citizen-report', methods=['GET', 'POST'])
def citizen_report():
    conn = get_db()

    if request.method == 'POST':
        project_id = request.form['project_id']
        report_type = request.form['report_type']
        description = request.form['description']
        latitude = request.form.get('latitude') or None
        longitude = request.form.get('longitude') or None
        citizen_name = request.form.get('citizen_name') or 'Anonymous'

        photo_path = ''
        photo_hash = ''
        gps_valid = 0

        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename:
                os.makedirs('static/uploads', exist_ok=True)
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                photo_path = f"uploads/{filename}"
                full_path = f"static/{photo_path}"
                file.save(full_path)

                # SHA-256 hash for duplicate detection (Day 4 adds EXIF + GPS)
                with open(full_path, 'rb') as f:
                    photo_hash = hashlib.sha256(f.read()).hexdigest()

        conn.execute('''
            INSERT INTO citizen_reports
            (project_id, citizen_name, report_type, description, latitude, longitude,
             photo_path, photo_hash, gps_valid, report_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        ''', (project_id, citizen_name, report_type, description,
              latitude, longitude, photo_path, photo_hash, gps_valid,
              datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

        flash('Report submitted successfully!', 'success')
        return redirect(url_for('reports.citizen_report'))

    projects = conn.execute(
        'SELECT project_id, project_name, village FROM projects ORDER BY project_name'
    ).fetchall()

    reports = conn.execute('''
        SELECT r.*, p.project_name
        FROM citizen_reports r
        LEFT JOIN projects p ON r.project_id = p.project_id
        ORDER BY r.report_id DESC
        LIMIT 20
    ''').fetchall()

    conn.close()
    return render_template('citizen_report.html', projects=projects, reports=reports)
