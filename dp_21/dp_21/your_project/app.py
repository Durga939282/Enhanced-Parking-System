from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Create parking spots status dictionary
parking_status = {
    'P1': {'status': 'empty', 'number': None},
    'P2': {'status': 'empty', 'number': None},
    'P3': {'status': 'empty', 'number': None},
    'P4': {'status': 'empty', 'number': None},
    'P5': {'status': 'empty', 'number': None},
    'P6': {'status': 'empty', 'number': None}
}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already exists')
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/update_parking', methods=['POST'])
def update_parking():
    data = request.json
    parking_status.update(data)
    return jsonify({'status': 'success'})

@app.route('/get_parking_status')
def get_parking_status():
    return jsonify(parking_status)

# In your main detection loop, when parking status changes:
def update_parking_status(spot_id, status, number=None):
    data = {
        spot_id: {
            'status': 'occupied' if status == 'Occupied' else 'empty',
            'number': number
        }
    }
    requests.post('http://localhost:5000/update_parking', json=data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 