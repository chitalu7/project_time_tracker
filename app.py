from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management (e.g., flashing messages)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set up the SQLite database URI
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'project_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Project model
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    status = db.Column(db.String(50), default='ongoing')
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Timesheet model
class TimeSheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_out = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.String(500), nullable=True)

# Archive model
class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    completed_date = db.Column(db.DateTime, nullable=False)

# Initialize the tables
with app.app_context():
    db.create_all()

# Register route
from flask import render_template, redirect, url_for, request, flash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))

        # Create a new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in!')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if user exists and password is correct
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))  # Redirect to a protected page
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch projects only for the logged-in user
    user_projects = Project.query.filter_by(user_id=current_user.id).all()
    
    # Fetch timesheets for the user's projects
    user_timesheets = TimeSheet.query.filter(TimeSheet.user_id == current_user.id).all()

    return render_template('dashboard.html', projects=user_projects, timesheets=user_timesheets)

# Create a new project
from datetime import datetime

@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form.get('name')
        start_date = datetime.now()

        # Create a new project for the current logged-in user
        new_project = Project(name=name, start_date=start_date, user_id=current_user.id, status='ongoing')
        db.session.add(new_project)
        db.session.commit()

        flash('Project created successfully!')
        return redirect(url_for('dashboard'))

    return render_template('create_project.html')


# Clock-in & out routes
@app.route('/clock_in/<int:project_id>', methods=['POST'])
@login_required
def clock_in(project_id):
    clock_in_time = datetime.now()

    # Create a new timesheet entry for the current user and project
    new_timesheet = TimeSheet(project_id=project_id, user_id=current_user.id, clock_in=clock_in_time)
    db.session.add(new_timesheet)
    db.session.commit()

    flash('Clocked in successfully!')
    return redirect(url_for('dashboard'))


@app.route('/clock_out/<int:timesheet_id>', methods=['POST'])
@login_required
def clock_out(timesheet_id):
    clock_out_time = datetime.now()
    note = request.form.get('note')

    # Find the timesheet entry and update it with the clock out time and note
    timesheet = TimeSheet.query.get(timesheet_id)
    if timesheet and timesheet.user_id == current_user.id:
        timesheet.clock_out = clock_out_time
        timesheet.note = note
        db.session.commit()

        flash('Clocked out successfully!')
    else:
        flash('Error: Timesheet not found or unauthorized action.')

    return redirect(url_for('dashboard'))






# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
