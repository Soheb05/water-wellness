from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    water_entries = db.relationship('WaterIntake', backref='user', lazy=True)

class WaterIntake(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Liters

DAILY_GOAL = 2.5  # Example daily water goal in liters

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    entries = WaterIntake.query.filter_by(user_id=user_id).order_by(WaterIntake.date.desc()).all()

    # Today's intake
    today = date.today()
    today_entry = WaterIntake.query.filter_by(user_id=user_id, date=today).first()
    today_amount = today_entry.amount if today_entry else 0

    # Prepare chart data for last 7 days
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime("%d-%b"))
        entry = WaterIntake.query.filter_by(user_id=user_id, date=day).first()
        chart_data.append(entry.amount if entry else 0)

    return render_template(
        'dashboard.html',
        username=session['user'],
        water_entries=entries,
        today_amount=today_amount,
        daily_goal=DAILY_GOAL,
        chart_labels=chart_labels,
        chart_data=chart_data
    )

@app.route('/add_water', methods=['POST'])
def add_water():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    amount = float(request.form['amount'])
    today = date.today()

    existing_entry = WaterIntake.query.filter_by(user_id=user_id, date=today).first()
    if existing_entry:
        existing_entry.amount += amount
    else:
        new_entry = WaterIntake(user_id=user_id, date=today, amount=amount)
        db.session.add(new_entry)

    db.session.commit()
    flash(f"Added {amount} liters for {today}")
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():  # <-- Add this
        db.create_all()
    app.run(debug=True)