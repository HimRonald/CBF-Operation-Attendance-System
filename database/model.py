from flask_sqlalchemy import SQLAlchemy
from datetime import time

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
    # meal_type = db.Column(db.String(50))
    breakfast = db.Column(db.Boolean, default=False)
    lunch = db.Column(db.Boolean, default=False)
    dinner = db.Column(db.Boolean, default=False)


    # def is_meal_time(self, event='check_in'):
    #     """Check if the event time (check_in or check_out) falls within meal time slots."""
    #     if event == 'check_in' and self.check_in:
    #         event_time = self.check_in.time()
    #     elif event == 'check_out' and self.check_out:
    #         event_time = self.check_out.time()
    #     else:
    #         return False

    #     # Define meal time ranges
    #     breakfast_start = time(7, 0)
    #     breakfast_end = time(9, 0)
    #     lunch_start = time(11, 0)
    #     lunch_end = time(13, 0)
    #     dinner_start = time(17, 0)
    #     dinner_end = time(19, 0)

    #     # Check if event_time falls within any meal time slots
    #     if breakfast_start <= event_time <= breakfast_end:
    #         return "Breakfast"
    #     elif lunch_start <= event_time <= lunch_end:
    #         return "Lunch"
    #     elif dinner_start <= event_time <= dinner_end:
    #         return "Dinner"
    #     else:
    #         return False
