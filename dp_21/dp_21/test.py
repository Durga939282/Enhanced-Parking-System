import cv2
import torch
import time
from threading import Thread, Event
import queue
import os
import sys

# Add headless mode flag
HEADLESS_MODE = False  # Set to False to display the video window

# Ensure we can import modules
try:
    from ultralytics import YOLO
    from detection.plate_detector import PlateDetector
    
    # Import config
    try:
        from config import get_video_url, MODEL_PATH, OCR_LANGUAGES, MIN_OCR_CONFIDENCE
    except ImportError:
        # Handle missing config values
        print("Some config values missing, using defaults")
        def get_video_url():
            return "http://100.109.214.6:4747/video"
        MODEL_PATH = r"C:\vs_code\dp_21\dp_21\smart_parking\weights\best.pt"
        OCR_LANGUAGES = ['en']
        MIN_OCR_CONFIDENCE = 0.6
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install torch ultralytics easyocr opencv-python")
    sys.exit(1)

class VideoStream:
    def __init__(self, src=0):
        print(f"Attempting to connect to: {src}")  # Debug print
        self.stream = cv2.VideoCapture(src)
        
        if not self.stream.isOpened():
            raise ValueError(f"Failed to connect to {src}")
        
        print(f"Successfully connected to: {src}")  # Confirm connection
        
        # Set camera properties
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.stream.set(cv2.CAP_PROP_FPS, 30)  # Set desired FPS
        
        # Set resolution to a lower value for better performance
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Adjust as needed
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Adjust as needed
        
        self.queue = queue.Queue(maxsize=1)
        self.stopped = Event()
        self.thread = None

    def start(self):
        print("Starting video stream thread...")
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()
        return self

    def update(self):
        while not self.stopped.is_set():
            ret, frame = self.stream.read()
            if not ret:
                print("Failed to grab frame")  # Debug print
                time.sleep(0.5)
                continue
            
            # Clear queue and add new frame
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
            
            self.queue.put(frame)

    def read(self):
        try:
            return self.queue.get(timeout=0.1)
        except queue.Empty:
            return None

    def stop(self):
        print("Stopping video stream...")
        self.stopped.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.stream.isOpened():
            self.stream.release()

def main():
    global HEADLESS_MODE  # Declare HEADLESS_MODE as global
    # Get video URL
    VIDEO_URL = get_video_url()  # Use the function to get the video URL
    print(f"Using video URL: {VIDEO_URL}")  # Debug print

    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print("Please check the MODEL_PATH in config.py")
        return

    # Initialize model
    print("Loading model...")
    try:
        model = YOLO(MODEL_PATH)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.to(device)
        print(f"Model loaded successfully on {device}")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Initialize plate detector
    try:
        print("Initializing plate detector...")
        plate_detector = PlateDetector(OCR_LANGUAGES, MIN_OCR_CONFIDENCE)
        print("Plate detector initialized")
    except Exception as e:
        print(f"Error initializing plate detector: {e}")
        plate_detector = None

    # Start video stream
    print("Starting video stream...")
    try:
        vs = VideoStream(VIDEO_URL).start()
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    time.sleep(2.0)  # Warm up camera

    try:
        print("Detection running. Press 'q' to stop.")
        while True:
            # Read frame
            frame = vs.read()
            if frame is None:
                print("No frame received, retrying...")
                time.sleep(0.5)
                continue

            # Run detection
            results = model(frame, verbose=False)
            
            # Process results
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Create text to display in console
                    class_name = "Empty" if label == 0 else "Occupied"
                    
                    # Add license plate detection for occupied spots
                    plate_number = None
                    if label == 1 and plate_detector is not None:  # If occupied
                        try:
                            plate_number, plate_conf = plate_detector.detect_plate(frame, (x1, y1, x2, y2))
                            if plate_number:
                                print(f"Detected plate: {plate_number} with confidence {plate_conf:.2f}")
                        except Exception as e:
                            print(f"Error detecting plate: {e}")
                    
                    # Draw bounding box
                    color = (0, 255, 0) if label == 0 else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Create text to display
                    status_text = f"{class_name} ({confidence:.2f})"
                    if plate_number:
                        status_text += f" Plate: {plate_number}"
                    
                    # Display text
                    cv2.putText(frame, status_text, 
                              (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                              0.5, color, 2)

            # Show frame if not in headless mode
            if not HEADLESS_MODE:
                cv2.namedWindow("Parking Detection", cv2.WINDOW_NORMAL)  # Create a resizable window
                cv2.imshow("Parking Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        print("Cleaning up...")
        vs.stop()
        # Only try to destroy windows if not in headless mode
        if not HEADLESS_MODE:
            try:
                cv2.destroyAllWindows()
            except Exception as e:
                print(f"Warning: Could not destroy windows: {e}")

if __name__ == "__main__":
    main()