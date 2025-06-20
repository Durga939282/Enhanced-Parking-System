from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from app.parking_state import parking_state
from run import get_latest_frame
import time

main = Blueprint('main', __name__)

def gen_frames():
    while True:
        frame = get_latest_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.01)  # Small delay to prevent overwhelming the client

@main.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@main.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('main.login'))
    return redirect(url_for('main.dashboard'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return render_template('register.html')

        new_user = User(
            username=username,
            password=generate_password_hash(password, method='sha256')
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('main.login'))

@main.route('/get_parking_status')
def get_parking_status():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(parking_state.get_status())

@main.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('main.login'))
    
    spots = parking_state.get_all_spots()  # Get the current parking status
    return render_template('dashboard.html', spots=spots)

@main.route('/api/parking/status')
def parking_status_api():
    spots = parking_state.get_all_spots()
    return jsonify(spots)

@main.route('/parking')
def parking_display():
    spots = parking_state.get_all_spots()
    return render_template('parking.html', spots=spots)

@main.route('/detected_numbers')
def detected_numbers():
    spots = parking_state.get_all_spots()
    return render_template('detected_numbers.html', spots=spots)

@main.route('/update_parking_slots', methods=['POST'])
def update_parking_slots():
    data = request.json
    parking_state.update_spots_from_detection(data)
    return jsonify({"status": "success", "message": "Parking slots updated."})

# Add your existing routes here 