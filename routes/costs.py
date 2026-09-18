from flask import Blueprint, render_template, request, jsonify
import sqlite3

costs_bp = Blueprint('costs', __name__)

DB_PATH = 'database/ghost_project.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@costs_bp.route('/cost-tracking')
def cost_tracking():
    conn = get_db()
    projects = conn.execute('SELECT project_id, project_name, village, budget FROM projects ORDER BY project_name').fetchall()
    rates = conn.execute('SELECT * FROM market_rates ORDER BY material_name').fetchall()
    conn.close()
    return render_template('cost_tracking.html', projects=projects, rates=rates)

@costs_bp.route('/api/check-cost', methods=['POST'])
def check_cost():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body'}), 400

    material = data.get('material')
    quantity = data.get('quantity')
    claimed = data.get('claimed')

    if material is None or quantity is None or claimed is None:
        return jsonify({'error': 'Missing material, quantity, or claimed'}), 400

    try:
        quantity = float(quantity)
        claimed = float(claimed)
    except (TypeError, ValueError):
        return jsonify({'error': 'quantity and claimed must be numbers'}), 400

    conn = get_db()
    rate = conn.execute(
        'SELECT material_name, unit, market_rate FROM market_rates WHERE material_name = ?',
        (material,)
    ).fetchone()
    conn.close()

    if not rate:
        return jsonify({'error': f'No market rate found for {material}'}), 404

    actual = rate['market_rate'] * quantity
    overcharge = claimed - actual
    overcharge_percent = (overcharge / actual * 100) if actual > 0 else 0

    if overcharge_percent > 20:
        verdict = 'FRAUD'
        message = 'Overcharge exceeds 20% — flag for investigation.'
    elif overcharge_percent > 10:
        verdict = 'SUSPICIOUS'
        message = 'Overcharge is 10–20% — needs review.'
    elif overcharge_percent >= 0:
        verdict = 'ACCEPTABLE'
        message = 'Within acceptable range (under 10%).'
    else:
        verdict = 'UNDER'
        message = 'Claimed cost is below market rate — possible quality concern.'

    return jsonify({
        'material': rate['material_name'],
        'unit': rate['unit'],
        'market_rate': rate['market_rate'],
        'quantity': quantity,
        'actual_cost': round(actual, 2),
        'claimed_cost': claimed,
        'overcharge': round(overcharge, 2),
        'overcharge_percent': round(overcharge_percent, 2),
        'verdict': verdict,
        'message': message
    })
