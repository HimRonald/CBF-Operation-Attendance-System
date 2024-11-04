from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Volunteer(db.Model):
    __tablename__ = 'volunteer'
    # Changed to String to match the actual data type
    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100))
    team = db.Column(db.String(100))
    attendances = db.relationship('Attendance', backref='volunteer', lazy=True)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.String(100), db.ForeignKey('volunteer.id'))
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
