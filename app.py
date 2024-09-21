from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the Flask app
app = Flask(__name__)

# Set up the SQLite database URI
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'project_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# User model
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     username = db.Column(db.String(150), unique=True, nullable=False)
     password = db.Column(db.String(150), nullable=False)

     def set_password(self, password):
          self.password = generate_password_hash(password)

     def check_password(self, password):
          return check_password_hash(self.password, password)
                                                    
# Project Model
class Project(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.String(200), unique=True, nullable=False)
     status = db.Column(db.String(50), default='ongoing')
     start_date = db.Column(db.DateTime, nullable=False)
     end_date = db.Column(db.DateTime, nullable=True)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Timesheet Model
class TimeSheet(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
     clock_in = db.Column(db.DateTime, nullable=False)
     clock_out = db.Column(db.DateTime, nullable=True)
     note = db.Column(db.String(500), nullable=True)

# Archive Model
class Archive(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
     completed_date = db.Column(db.DateTime, nullable=False)

# Initialize The Table
# @app.before_first_request
# def create_tables():
#      db.create_all()

if __name__ == '__main__':
    # Create database tables before starting the app
    with app.app_context():
        db.create_all()

    app.run(debug=True)


@app.route('/')
def home():
     return "Hello, Project Time Tracker!"

if __name__ == '__main__':
     app.run(debugger=True)