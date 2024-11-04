from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from datetime import date
import json
import pytz
import os
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

local_tz = pytz.timezone('Asia/Phnom_Penh')
# Database Models
class Volunteer(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(50), nullable=False)
    attendances = db.relationship('Attendance', backref='volunteer', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.String(10), db.ForeignKey('volunteer.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(local_tz))
    status = db.Column(db.String(20), nullable=False, default='present')  # present, late, etc.

# Routes for web pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scanner.html')
def scanner():
    return render_template('scanner.html')

@app.route('/dashboard.html')
def dashboard():
    today = date.today()
    # volunteers = Volunteer.query.all()
    attendances = Attendance.query.all()
    return render_template('dashboard.html', attendances=attendances, today=today)

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
            db.func.date(Attendance.timestamp) == today
        ).first()
        
        if existing_attendance:
            return jsonify({
            'success': False,
            'message': f'{volunteer.name} has already checked in today',
            'volunteer': {
                'name': volunteer.name,
                'team': volunteer.team,
                'check_in_time': existing_attendance.timestamp.strftime('%H:%M:%S')
            }
            })
        
        # Create new attendance record
        attendance = Attendance(volunteer_id=volunteer.id)
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Attendance recorded',
            'volunteer': {
                'name': volunteer.name,
                'team': volunteer.team,
                'check_in_time': attendance.timestamp.strftime('%H:%M:%S')
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

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)