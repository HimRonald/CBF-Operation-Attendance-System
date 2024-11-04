from database.model import db, Volunteer, Attendance
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import json
import pytz
import os
import pandas as pd

# Import the configuration
from database.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)  # Initialize the db instance with the Flask app

local_tz = pytz.timezone('Asia/Phnom_Penh')

# Import models

# Routes for web pages


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scanner.html')
def scanner():
    return render_template('scanner.html')


@app.route('/dashboard.html')
def dashboard():
    selected_date_str = request.args.get('date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        selected_date = date.today()

    attendances = Attendance.query.all()

    # Convert check_in and check_out times to UTC+7
    for attendance in attendances:
        if attendance.check_in:
            attendance.check_in = attendance.check_in.astimezone(local_tz)
        if attendance.check_out:
            attendance.check_out = attendance.check_out.astimezone(local_tz)

    return render_template('dashboard.html', attendances=attendances, selected_date=selected_date)

# API Routes


@app.route('/api/scan', methods=['POST'])
def process_scan():
    try:
        scan_data = request.json['code']
        volunteer_data = json.loads(scan_data)

        # Find volunteer in database
        volunteer = Volunteer.query.get(volunteer_data['id'])

        if not volunteer:
            return jsonify({
                'success': False,
                'message': 'Volunteer not found'
            })

        # Check if already checked in today
        today = datetime.utcnow().date()
        existing_attendance = Attendance.query.filter(
            Attendance.volunteer_id == volunteer.id,
            db.func.date(Attendance.check_in) == today
        ).first()

        if existing_attendance:
            if existing_attendance.check_out is None:
                existing_attendance.check_out = datetime.now(local_tz)
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'{volunteer.name} checked out successfully',
                    'volunteer': {
                        'name': volunteer.name,
                        'team': volunteer.team,
                        'check_out_time': existing_attendance.check_out.strftime('%H:%M:%S')
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'{volunteer.name} has already checked out today',
                    'volunteer': {
                        'name': volunteer.name,
                        'team': volunteer.team,
                        'check_in_time': existing_attendance.check_in.strftime('%H:%M:%S'),
                        'check_out_time': existing_attendance.check_out.strftime('%H:%M:%S')
                    }
                })

        # Create new attendance record
        attendance = Attendance(volunteer_id=volunteer.id,
                                check_in=datetime.now(local_tz))
        db.session.add(attendance)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Check-in recorded',
            'volunteer': {
                'name': volunteer.name,
                'team': volunteer.team,
                'check_in_time': attendance.check_in.strftime('%H:%M:%S')
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing scan: {str(e)}'
        })

# Import volunteers from CSV


@app.route('/api/import-volunteers', methods=['POST'])
def import_volunteers():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    try:
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            volunteer = Volunteer(
                id=row['id'],
                name=row['name'],
                team=row['team']
            )
            db.session.add(volunteer)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Volunteers imported successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error importing volunteers: {str(e)}'})


def init_db():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
