from database.model import db, Volunteer, Attendance
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import json
import pytz
import os
import pandas as pd
from flask import send_file
import io

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
    search_query = request.args.get('search')

    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        selected_date = date.today()

    query = Attendance.query.join(Volunteer).order_by(Attendance.check_in)

    if search_query:
        query = query.filter(
            (Volunteer.name.ilike(f'%{search_query}%')) |
            (Volunteer.team.ilike(f'%{search_query}%'))
        )

    attendances = query.all()

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
        today = datetime.now(local_tz).date()
        existing_attendance = Attendance.query.filter(
            Attendance.volunteer_id == volunteer.id,
            db.func.date(Attendance.check_in) == today
        ).first()

        if existing_attendance:
            if existing_attendance.check_out is None:
                return jsonify({
                    'success': True,
                    'message': f'{volunteer.name} is currently checked in. Please confirm check-out.',
                    'volunteer': {
                        'name': volunteer.name,
                        'team': volunteer.team,
                        'check_in_time': existing_attendance.check_in.astimezone(local_tz).strftime('%H:%M:%S'),
                        'check_out_time': None
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'{volunteer.name} has already checked out today',
                    'volunteer': {
                        'name': volunteer.name,
                        'team': volunteer.team,
                        'check_in_time': existing_attendance.check_in.astimezone(local_tz).strftime('%H:%M:%S'),
                        'check_out_time': existing_attendance.check_out.astimezone(local_tz).strftime('%H:%M:%S')
                    }
                })

        # Prepare for new check-in
        return jsonify({
            'success': True,
            'message': f'{volunteer.name} is ready to check in. Please confirm.',
            'volunteer': {
                'name': volunteer.name,
                'team': volunteer.team,
                'check_in_time': None,
                'check_out_time': None
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing scan: {str(e)}'
        })
        

@app.route('/api/confirm', methods=['POST'])
def confirm_scan():
    try:
        data = request.json
        volunteer_name = data['name']
        volunteer_team = data['team']

        # Find volunteer in database
        volunteer = Volunteer.query.filter_by(
            name=volunteer_name, team=volunteer_team).first()

        if not volunteer:
            return jsonify({
                'success': False,
                'message': 'Volunteer not found'
            })

        # Check if already checked in today
        today = datetime.now(local_tz).date()
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
            'message': f'Error confirming scan: {str(e)}'
        })
        
@app.route('/download-attendance', methods=['GET'])
def download_attendance():
    selected_date_str = request.args.get('date')
    if not selected_date_str:
        return jsonify({'success': False, 'message': 'No date provided'})

    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

    query = Attendance.query.join(Volunteer).filter(
        db.func.date(Attendance.check_in) == selected_date
    ).order_by(Attendance.check_in)

    attendances = query.all()

    # Convert check_in and check_out times to UTC+7
    for attendance in attendances:
        if attendance.check_in:
            attendance.check_in = attendance.check_in.astimezone(local_tz)
        if attendance.check_out:
            attendance.check_out = attendance.check_out.astimezone(local_tz)

    # Create a DataFrame
    data = [{
        'ID': attendance.volunteer.id,
        'Name': attendance.volunteer.name,
        'Team': attendance.volunteer.team,
        'Check-in Time': attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else 'N/A',
        'Check-out Time': attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else 'N/A'
    } for attendance in attendances]

    df = pd.DataFrame(data)

    # Create an Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')
    output.seek(0)

    return send_file(output, download_name=f'attendance_{selected_date_str}.xlsx', as_attachment=True)


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
            # Check if a volunteer with the same name already exists
            existing_volunteer = Volunteer.query.filter_by(
                name=row['name']).first()
            if existing_volunteer:
                print(
                    f"Volunteer with name {row['name']} already exists. Skipping...")
                continue

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
