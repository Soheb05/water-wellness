from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta, datetime
from models import db, User, WaterIntake, Reminder, Progress, Setting  # use models here
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Bind db to app
db.init_app(app)
migrate = Migrate(app, db)

DAILY_GOAL = 2.5  # fallback daily goal

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
        new_user = User(username=username, password=password, daily_goal=DAILY_GOAL)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    # Today’s intake
    today = date.today()
    entries = WaterIntake.query.filter_by(user_id=user_id, date=today).all()
    today_amount = sum(e.amount for e in entries)

    # Last 7 days chart (daily)
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    chart_labels = [d.strftime("%d-%b") for d in last_7_days]
    chart_data = [
        sum(e.amount for e in WaterIntake.query.filter_by(user_id=user_id, date=d).all())
        for d in last_7_days
    ]

    # ✅ Weekly total (last 7 days combined per day)
    weekly_data = [
        {
            "date": d.strftime("%d-%b"),
            "total": sum(e.amount for e in WaterIntake.query.filter_by(user_id=user_id, date=d).all())
        }
        for d in last_7_days
    ]
    weekly_labels = [d["date"] for d in weekly_data]
    weekly_totals = [d["total"] for d in weekly_data]

    # Reminders (serialize into JSON-safe dicts)
    reminders = Reminder.query.filter_by(user_id=user_id).all()
    reminders_json = [
        {
            "id": r.id,
            "name": r.name,
            "message": r.message,
            "time": r.time,   # "HH:MM"
            "active": r.active
        }
        for r in reminders
    ]

    # Progress (already stored per week in DB)
    progress_entries = Progress.query.filter_by(user_id=user_id).all()
    progress_labels = [p.week for p in progress_entries]
    progress_data = [p.total_amount for p in progress_entries]

    return render_template(
        'dashboard.html',
        username=user.username,
        water_entries=entries,
        today_amount=today_amount,
        daily_goal=user.daily_goal or DAILY_GOAL,
        chart_labels=chart_labels,   # for daily chart
        chart_data=chart_data,
        weekly_labels=weekly_labels, # ✅ for weekly chart
        weekly_totals=weekly_totals, # ✅ for weekly chart
        reminders=reminders,
        reminders_json=reminders_json,
        progress_labels=progress_labels,
        progress_data=progress_data
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


@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    message = request.form['message']
    name = request.form['name']
    time_str = request.form['time']   # <--- This is already a string like "22:57"

    # Ensure it's stored as "HH:MM"
    time_str = time_str[:5]

    reminder = Reminder(user_id=user_id, name=name, message=message, time=time_str)
    db.session.add(reminder)
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/toggle_reminder/<int:reminder_id>', methods=['POST'])
def toggle_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    reminder.active = not reminder.active  # Flip ON/OFF
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_reminder/<int:reminder_id>', methods=['POST'])
def delete_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)

    # Ensure reminder belongs to logged-in user
    if reminder.user_id != session['user_id']:
        flash("You are not allowed to delete this reminder.", "danger")
        return redirect(url_for('dashboard'))

    db.session.delete(reminder)
    db.session.commit()
    flash("Reminder deleted successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user.daily_goal = float(request.form['daily_goal'])
    db.session.commit()

    flash('Settings updated!')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
