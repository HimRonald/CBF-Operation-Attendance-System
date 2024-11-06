import json
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_migrate import Migrate
from datetime import datetime, date, time
import pytz
import os
import pandas as pd
import io
from flask import send_file
from flask_login import login_user, login_required, logout_user, current_user
from login.extensions import db, login_manager
from login.login import login_bp
from database.config import Config
from database.model import Volunteer, Attendance, User

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
login_manager.init_app(app)
login_manager.login_view = 'login_bp.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(login_bp)

local_tz = pytz.timezone('Asia/Phnom_Penh')

# Routes for web pages
# Meal times configuration
BREAKFAST_TIME = (time(7, 0), time(9, 0))
LUNCH_TIME = (time(11, 0), time(13, 0))
DINNER_TIME = (time(17, 0), time(19, 0))

# Helper function to determine if the current time is within meal times


def get_meal_column():
    current_time = datetime.now().time()
    if BREAKFAST_TIME[0] <= current_time <= BREAKFAST_TIME[1]:
        return 'breakfast'
    elif LUNCH_TIME[0] <= current_time <= LUNCH_TIME[1]:
        return 'lunch'
    elif DINNER_TIME[0] <= current_time <= DINNER_TIME[1]:
        return 'dinner'
    return None


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/scanner.html')
@login_required
def scanner():
    return render_template('scanner.html')


@app.route('/dashboard.html')
@login_required
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
        today = datetime.now().date()
        existing_attendance = Attendance.query.filter(
            Attendance.volunteer_id == volunteer.id,
            db.func.date(Attendance.check_in) == today
        ).first()

        if existing_attendance:
            if existing_attendance.check_out is None:
                meal_column = get_meal_column()
                if meal_column and not getattr(existing_attendance, meal_column):
                    return jsonify({
                        'success': True,
                        'message': f'{volunteer.name} is currently checked in. Confirm meal: {meal_column.capitalize()}.',
                        'volunteer': {
                            'name': volunteer.name,
                            'team': volunteer.team,
                            'check_in_time': existing_attendance.check_in.strftime('%H:%M:%S'),
                            'check_out_time': None,
                            'meal_type': meal_column.capitalize()
                        }
                    })
                else:
                    return jsonify({
                        'success': True,
                        'message': f'{volunteer.name} is currently checked in. Please confirm check-out.',
                        'volunteer': {
                            'name': volunteer.name,
                            'team': volunteer.team,
                            'check_in_time': existing_attendance.check_in.strftime('%H:%M:%S'),
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
                        'check_in_time': existing_attendance.check_in.strftime('%H:%M:%S'),
                        'check_out_time': existing_attendance.check_out.strftime('%H:%M:%S')
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
        meal_type = data.get('meal_type')

        # Find volunteer in database
        volunteer = Volunteer.query.filter_by(
            name=volunteer_name, team=volunteer_team).first()

        if not volunteer:
            return jsonify({
                'success': False,
                'message': 'Volunteer not found'
            })

        # Check if already checked in today
        today = datetime.now().date()
        existing_attendance = Attendance.query.filter(
            Attendance.volunteer_id == volunteer.id,
            db.func.date(Attendance.check_in) == today
        ).first()

        if existing_attendance:
            if existing_attendance.check_out is None:
                if meal_type:
                    meal_column = meal_type.lower()
                    if meal_column in ['breakfast', 'lunch', 'dinner']:
                        setattr(existing_attendance, meal_column, True)
                        db.session.commit()
                        return jsonify({
                            'success': True,
                            'message': f'{meal_type} recorded for {volunteer.name}',
                            'volunteer': {
                                'name': volunteer.name,
                                'team': volunteer.team,
                                'meal_type': meal_type
                            }
                        })
                else:
                    # Check out the volunteer
                    existing_attendance.check_out = datetime.now()
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
                                check_in=datetime.now())
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

    # Create a DataFrame with breakfast, lunch, and dinner columns
    data = [{
        'ID': attendance.volunteer.id,
        'Name': attendance.volunteer.name,
        'Team': attendance.volunteer.team,
        'Check-in Time': attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else 'N/A',
        'Check-out Time': attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else 'N/A',
        'Breakfast': 'Yes' if attendance.breakfast else 'No',
        'Lunch': 'Yes' if attendance.lunch else 'No',
        'Dinner': 'Yes' if attendance.dinner else 'No'
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
