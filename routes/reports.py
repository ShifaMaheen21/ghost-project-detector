from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import os

from utils.photo_check import hash_image, read_exif, is_within_boundary, check_duplicate

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
        citizen_name = request.form.get('citizen_name') or 'Anonymous'

        user_lat = request.form.get('latitude') or None
        user_lng = request.form.get('longitude') or None

        photo_path = ''
        photo_hash = ''
        gps_valid = 0
        duplicate_flag = False
        duplicate_ref = None

        if 'photo' in request.files:
            file = request.files['photo']
            if file.filename:
                os.makedirs('static/uploads', exist_ok=True)
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                photo_path = f"uploads/{filename}"
                full_path = f"static/{photo_path}"
                file.save(full_path)

                # 1. Hash for duplicate detection
                photo_hash = hash_image(full_path)

                # 2. Read EXIF (date, GPS)
                exif = read_exif(full_path)

                # Prefer EXIF GPS over user-entered
                if exif.get('gps_lat') and exif.get('gps_lng'):
                    user_lat = exif['gps_lat']
                    user_lng = exif['gps_lng']

                # 3. Duplicate check
                duplicate_flag, duplicate_ref = check_duplicate(photo_hash, conn)

        # 4. Boundary / geofence check
        project = conn.execute(
            'SELECT latitude, longitude FROM projects WHERE project_id = ?',
            (project_id,)
        ).fetchone()

        if project and user_lat and user_lng:
            try:
                in_bounds = is_within_boundary(
                    float(user_lat), float(user_lng),
                    project['latitude'], project['longitude'],
                    radius_km=2.0
                )
                gps_valid = 1 if in_bounds else 0
            except (TypeError, ValueError):
                gps_valid = 0

        # 5. Insert
        conn.execute('''
            INSERT INTO citizen_reports
            (project_id, citizen_name, report_type, description, latitude, longitude,
             photo_path, photo_hash, gps_valid, report_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        ''', (project_id, citizen_name, report_type, description,
              user_lat, user_lng, photo_path, photo_hash, gps_valid,
              datetime.now().strftime("%Y-%m-%d")))
        conn.commit()

        flash('Report submitted successfully!', 'success')

        if duplicate_flag:
            flash(f'Duplicate photo detected — same image used in report #{duplicate_ref}', 'warning')

        if photo_hash and not gps_valid and user_lat and user_lng:
            flash('Photo location is outside the project boundary (2 km radius).', 'warning')

        return redirect(url_for('reports.citizen_report'))

    # GET
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
