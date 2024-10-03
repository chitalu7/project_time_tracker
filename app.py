from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
    clocked_in = db.Column(db.Boolean, default=False)  # Track clock-in status

# Archive model
class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    completed_date = db.Column(db.DateTime, nullable=False)

# Initialize the tables
with app.app_context():
    db.create_all()

# Root route that checks if the user is logged in and redirects accordingly
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))

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
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))

    return render_template('login.html')

# Logout route
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    user_projects = Project.query.filter_by(user_id=current_user.id).all()
    user_timesheets = TimeSheet.query.filter(TimeSheet.user_id == current_user.id).all()

    return render_template('dashboard.html', projects=user_projects, timesheets=user_timesheets)

# Create a new project
@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form.get('name')
        start_date = datetime.now()
        new_project = Project(name=name, start_date=start_date, user_id=current_user.id, status='ongoing')
        db.session.add(new_project)
        db.session.commit()

        flash('Project created successfully!')
        return redirect(url_for('dashboard'))

    return render_template('create_project.html')

# Clock-in route
@app.route('/clock_in/<int:project_id>', methods=['POST'])
@login_required
def clock_in(project_id):
    clock_in_time = datetime.now()

    # Create a new timesheet entry for the current user and project
    new_timesheet = TimeSheet(project_id=project_id, user_id=current_user.id, clock_in=clock_in_time, clocked_in=True)
    db.session.add(new_timesheet)
    db.session.commit()

    flash('Clocked in successfully!')
    return redirect(url_for('dashboard'))

# Clock-out route
@app.route('/clock_out/<int:timesheet_id>', methods=['POST'])
@login_required
def clock_out(timesheet_id):
    clock_out_time = datetime.now()
    note = request.form.get('note')
    timesheet = TimeSheet.query.get(timesheet_id)
    if timesheet and timesheet.user_id == current_user.id:
        timesheet.clock_out = clock_out_time
        timesheet.note = note
        timesheet.clocked_in = False  # Set clocked_in to False
        db.session.commit()

        flash('Clocked out successfully!')
    else:
        flash('Error: Timesheet not found or unauthorized action.')

    return redirect(url_for('dashboard'))

# Complete project route
@app.route('/complete_project/<int:project_id>', methods=['POST'])
@login_required
def complete_project(project_id):
    project = Project.query.get(project_id)
    if project and project.user_id == current_user.id:
        project.status = 'completed'
        project.end_date = datetime.now()
        archived_project = Archive(project_id=project.id, completed_date=project.end_date)
        db.session.add(archived_project)
        db.session.commit()

        flash('Project marked as complete and moved to archive.')
    else:
        flash('Project not found or unauthorized action.')

    return redirect(url_for('dashboard'))

# Archived project
@app.route('/archives')
@login_required
def archives():
    archived_projects = db.session.query(Archive, Project).filter(Archive.project_id == Project.id, Project.user_id == current_user.id).all()

    return render_template('archives.html', archived_projects=archived_projects)

# Clear database route
@app.route('/clear_db', methods=['POST'])
@login_required
def clear_db():
    try:
        db.session.query(TimeSheet).delete()
        db.session.query(Project).delete()
        db.session.query(Archive).delete()
        db.session.commit()

        flash('Database cleared successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while clearing the database: {str(e)}', 'danger')

    return redirect(url_for('dashboard'))

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
