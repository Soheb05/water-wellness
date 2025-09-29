from flask_sqlalchemy import SQLAlchemy
from datetime import time, datetime

db = SQLAlchemy()  # define here, app will bind later

# ------------------- User Model -------------------
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    daily_goal = db.Column(db.Float, default=2.5)

    # Relationships
    water_intakes = db.relationship("WaterIntake", backref="user", lazy=True)
    reminders = db.relationship("Reminder", backref="user", lazy=True)
    progresses = db.relationship("Progress", backref="user", lazy=True)
    settings = db.relationship("Setting", backref="user", lazy=True, uselist=False)


# ------------------- Water Intake -------------------
class WaterIntake(db.Model):
    __tablename__ = "water_intake"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    amount = db.Column(db.Float, nullable=False)


# ------------------- Reminder -------------------
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)     # Morning / Afternoon / Evening / Night
    message = db.Column(db.String(200), nullable=False) # Reminder message
    time = db.Column(db.String(5), nullable=False)      # Store as "HH:MM"
    active = db.Column(db.Boolean, default=True)        # New field (ON/OFF toggle)



# ------------------- Progress -------------------
class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    week = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)


# ------------------- Setting -------------------
class Setting(db.Model):
    __tablename__ = "setting"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    theme = db.Column(db.String(20), default="light")
