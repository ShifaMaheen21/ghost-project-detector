from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

emb_bp = Blueprint('emb', __name__)

DB_PATH = 'database/ghost_project.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def compute_status(emb_qty, observed_qty):
    """Return (discrepancy_percent, status_label).
       discrepancy = how much e-MB overclaims vs observed."""
    if not emb_qty or emb_qty == 0:
        return 0, 'GREEN'
    disc = ((emb_qty - observed_qty) / emb_qty) * 100 if observed_qty is not None else 0
    disc = round(disc, 2)

    if disc < 0:
        return disc, 'GREEN'   # observed exceeds e-MB → no overclaim
    if disc <= 5:
        return disc, 'GREEN'
    if disc <= 15:
        return disc, 'YELLOW'
    return disc, 'RED'

@emb_bp.route('/emb')
def emb_list():
    conn = get_db()

    # Aggregate per project
    projects = conn.execute('''
        SELECT
            p.project_id,
            p.project_name,
            p.village,
            COUNT(b.boq_item_id) AS item_count,
            SUM(b.boq_quantity) AS total_boq,
            SUM(b.emb_quantity) AS total_emb,
            SUM(b.observed_quantity) AS total_observed
        FROM projects p
        LEFT JOIN boq_items b ON p.project_id = b.project_id
        GROUP BY p.project_id
        ORDER BY p.project_id
    ''').fetchall()

    # Compute status per project
    result = []
    for p in projects:
        emb = p['total_emb'] or 0
        obs = p['total_observed'] or 0
        disc, status = compute_status(emb, obs)
        result.append({
            'project_id': p['project_id'],
            'project_name': p['project_name'],
            'village': p['village'],
            'item_count': p['item_count'],
            'total_boq': p['total_boq'] or 0,
            'total_emb': emb,
            'total_observed': obs,
            'discrepancy': disc,
            'status': status
        })

    conn.close()
    return render_template('emb_reconciliation.html', projects=result, project=None, items=None)

@emb_bp.route('/emb/<int:project_id>')
def emb_detail(project_id):
    conn = get_db()

    project = conn.execute(
        'SELECT project_id, project_name, village FROM projects WHERE project_id = ?',
        (project_id,)
    ).fetchone()

    if not project:
        conn.close()
        return "Project not found", 404

    items = conn.execute('''
        SELECT * FROM boq_items
        WHERE project_id = ?
        ORDER BY material_name
    ''', (project_id,)).fetchall()

    # Add per-item status
    enriched = []
    for it in items:
        disc, status = compute_status(it['emb_quantity'], it['observed_quantity'])
        enriched.append({
            'boq_item_id': it['boq_item_id'],
            'material_name': it['material_name'],
            'unit': it['unit'],
            'boq_quantity': it['boq_quantity'],
            'emb_quantity': it['emb_quantity'],
            'observed_quantity': it['observed_quantity'],
            'discrepancy': disc,
            'status': status
        })

    # Aggregate for the project
    total_emb = sum(i['emb_quantity'] or 0 for i in items)
    total_obs = sum(i['observed_quantity'] or 0 for i in items)
    total_disc, total_status = compute_status(total_emb, total_obs)

    # Load project list for the sidebar dropdown
    all_projects = conn.execute(
        'SELECT project_id, project_name FROM projects ORDER BY project_name'
    ).fetchall()

    conn.close()

    return render_template('emb_reconciliation.html',
                           projects=all_projects,
                           project=project,
                           items=enriched,
                           total_disc=total_disc,
                           total_status=total_status)

@emb_bp.route('/emb/update/<int:boq_item_id>', methods=['POST'])
def emb_update(boq_item_id):
    observed = request.form.get('observed_quantity')
    if observed is None or observed == '':
        flash('Observed quantity required.', 'warning')
        return redirect(request.referrer or url_for('emb.emb_list'))

    try:
        observed = float(observed)
    except ValueError:
        flash('Observed quantity must be a number.', 'warning')
        return redirect(request.referrer or url_for('emb.emb_list'))

    conn = get_db()
    item = conn.execute('SELECT * FROM boq_items WHERE boq_item_id = ?', (boq_item_id,)).fetchone()
    if not item:
        conn.close()
        return "Item not found", 404

    disc, status = compute_status(item['emb_quantity'], observed)

    conn.execute('''
        UPDATE boq_items
        SET observed_quantity = ?, discrepancy_percent = ?, status = ?
        WHERE boq_item_id = ?
    ''', (observed, disc, status, boq_item_id))
    conn.commit()
    project_id = item['project_id']
    conn.close()

    flash(f'Observed quantity updated — status: {status}', 'success')
    return redirect(url_for('emb.emb_detail', project_id=project_id))
