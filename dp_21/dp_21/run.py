from app import create_app
from detection.model import ParkingDetector
from detection.video_stream import VideoStream
from detection.plate_detector import PlateDetector
from app.parking_state import parking_state
import cv2
import time
import threading
import numpy as np
from collections import deque
import concurrent.futures
import os
import sys
import easyocr
from flask import jsonify, request
from flask_socketio import SocketIO
import pytesseract

# Set HEADLESS_MODE to False to display the video window
HEADLESS_MODE = False

# Ensure config.py exists and can be imported
try:
    from config import get_video_url, MODEL_PATH, OCR_LANGUAGES, MIN_OCR_CONFIDENCE
except ImportError as e:
    print(f"Error importing config: {e}")
    print("Using default configuration")
    def get_video_url():
        return "http://100.109.214.6:4747/video"
    MODEL_PATH = r"C:\vs_code\dp_21\dp_21\smart_parking\weights\best.pt"
    OCR_LANGUAGES = ['en']
    MIN_OCR_CONFIDENCE = 0.6

# Import configuration
VIDEO_URL = get_video_url()
print(f"Using video URL: {VIDEO_URL}")

# Verify model path exists
if not os.path.exists(MODEL_PATH):
    print(f"WARNING: Model file not found at {MODEL_PATH}")
    print("Please check the path in config.py")

# Frame buffer for smooth streaming
frame_buffer = deque(maxlen=3)
latest_frame = None
processing_lock = threading.Lock()

# Set a frame skip interval
FRAME_SKIP_INTERVAL = 2  # Process every 2nd frame
frame_count = 0

# Initialize the plate detector
try:
    plate_detector = PlateDetector(OCR_LANGUAGES, MIN_OCR_CONFIDENCE)
    print("Plate detector initialized successfully")
except Exception as e:
    print(f"Error initializing plate detector: {e}")
    plate_detector = None

# Initialize the OCR reader
reader = easyocr.Reader(['en'])

def process_frame_for_web(frame):
    """Optimize frame for web streaming"""
    try:
        scale_percent = 70
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        return buffer.tobytes()
    except Exception as e:
        print(f"Error processing frame for web: {e}")
        return None

def detect_numbers(frame):
    """Detect numbers in the given frame using OCR."""
    results = reader.readtext(frame)
    detected_numbers = []
    
    for (bbox, text, prob) in results:
        detected_numbers.append(text)
    
    return detected_numbers

def process_detections(frame, results):
    global latest_frame
    detection_frame = frame.copy()
    current_detections = {i: {'status': 'empty', 'plate': None} for i in range(1, 13)}

    # Detect numbers in the frame
    detected_numbers = detect_numbers(frame)

    # Create a mapping of detected numbers to their respective slots
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if conf < 0.3:
                continue

            spot_number = determine_spot_number(x1, y1, x2, y2, frame.shape)
            if spot_number is not None:
                status = 'occupied' if cls == 1 else 'empty'
                
                if status == 'occupied':
                    # Associate detected number with the parking slot
                    if detected_numbers:
                        # Use the detected number corresponding to the current slot
                        current_detections[spot_number]['plate'] = detected_numbers.pop(0)  # Get the first detected number

                current_detections[spot_number]['status'] = status

                # Emit the detected plate number to the frontend
                if current_detections[spot_number]['plate']:
                    update_parking_state(spot_number, current_detections[spot_number]['plate'])

                # Draw bounding boxes and display the detected number
                color = (0, 0, 255) if status == 'occupied' else (0, 255, 0)
                cv2.rectangle(detection_frame, (x1, y1), (x2, y2), color, 2)
                
                cv2.putText(detection_frame, f"Spot {spot_number}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                if current_detections[spot_number]['plate']:
                    cv2.putText(detection_frame, f"Plate: {current_detections[spot_number]['plate']}", (x1, y2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Update the parking state with detected numbers
    parking_state.update_spots_from_detection(current_detections)
    
    with processing_lock:
        latest_frame = detection_frame
        web_frame = process_frame_for_web(detection_frame)
        if web_frame:
            frame_buffer.append(web_frame)

    return detection_frame

def determine_spot_number(x1, y1, x2, y2, frame_shape):
    height, width = frame_shape[:2]
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    
    if center_y < height // 2:
        spot = int((center_x / width) * 6) + 1
        return spot if 1 <= spot <= 6 else None
    else:
        spot = int((center_x / width) * 6) + 7
        return spot if 7 <= spot <= 12 else None

def process_frame(frame):
    global detector
    results = detector.detect(frame)
    detection_frame = process_detections(frame, results)
    return detection_frame

def run_detection():
    global HEADLESS_MODE
    try:
        print(f"Initializing video stream from: {VIDEO_URL}")
        vs = VideoStream(VIDEO_URL).start()
        print("Initializing detector...")
        detector = ParkingDetector(MODEL_PATH)
        print("Detector initialized with model:", MODEL_PATH)
        time.sleep(2.0)
        
        target_fps = 30  # Aim for 30 FPS
        last_time = time.time()

        while True:
            frame = vs.read()
            if frame is None:
                print("No frame received, retrying...")
                time.sleep(0.1)  # Reduce retry delay
                continue

            # Resize frame for faster processing
            frame = cv2.resize(frame, (320, 240))

            # Increment frame count and skip frames based on the interval
            global frame_count
            frame_count += 1
            if frame_count % FRAME_SKIP_INTERVAL != 0:
                continue  # Skip processing this frame

            results = detector.detect(frame)
            detection_frame = process_detections(frame, results)

            if not HEADLESS_MODE:
                cv2.imshow("Parking Detection", detection_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            current_time = time.time()
            processing_time = current_time - last_time
            sleep_time = max(1/target_fps - processing_time, 0)
            time.sleep(sleep_time)
            last_time = time.time()

    except Exception as e:
        print(f"Error in detection: {e}")
    finally:
        print("Cleaning up...")
        vs.stop()
        if not HEADLESS_MODE:
            cv2.destroyAllWindows()

def get_latest_frame():
    with processing_lock:
        return frame_buffer[-1] if frame_buffer else None

def capture_and_update_parking_slots():
    # Capture the latest frame from the camera
    frame = get_latest_frame()  # Assuming this function exists and returns a frame
    if frame is not None:
        # Update parking slots based on the captured image
        parking_state.update_spots_from_image(frame)

# Call this function periodically or based on your application logic

# Emit notifications when parking status changes
def notify_parking_status_change(spot_number, status):
    socketio.emit('parking_status_update', {'spot_number': spot_number, 'status': status})

# Update the parking state and notify users
def update_parking_state(spot_number, plate):
    parking_state.spots[spot_number]['status'] = 'occupied'
    parking_state.spots[spot_number]['plate'] = plate
    notify_parking_status_change(spot_number, {'status': 'occupied', 'plate': plate})

# In your detection logic, call update_parking_state when a spot status changes

def preprocess_image(frame):
    """Preprocess the frame for OCR detection."""
    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    binary_image = cv2.adaptiveThreshold(blurred_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
    return binary_image

def process_frame_for_ocr(frame):
    """Preprocess the frame for OCR detection."""
    processed_frame = preprocess_image(frame)
    detected_text = pytesseract.image_to_string(processed_frame, config='--psm 7')
    return detected_text

if __name__ == "__main__":
    try:
        sys.path.append(r"C:\vs_code\dp_21\dp_21")
        print("Starting Flask web server...")
        app = create_app()
        
        # Initialize SocketIO after app is created
        socketio = SocketIO(app)

        app.secret_key = 'your-secret-key-here'
        
        # Define your routes here
        @app.route('/update_parking_slots', methods=['POST'])
        def update_parking_slots():
            data = request.json
            parking_state.update_spots_from_detection(data)
            return jsonify({"status": "success", "message": "Parking slots updated."})

        detection_thread = threading.Thread(target=run_detection)
        detection_thread.daemon = True
        detection_thread.start()
        
        print("Flask app is running! Visit http://localhost:5000/parking for the UI")
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        print(f"Error starting application: {e}")