import cv2
import torch
from ultralytics import YOLO
import time
from threading import Thread
import queue
import requests
import json

class VideoStream:
    def __init__(self, url):
        self.stream = cv2.VideoCapture(url)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        self.stream.set(cv2.CAP_PROP_FPS, 30)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.queue = queue.Queue(maxsize=2)
        self.stopped = False
        
    def start(self):
        thread = Thread(target=self.update, args=())
        thread.daemon = True
        thread.start()
        return self
        
    def update(self):
        while True:
            if self.stopped:
                return
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    pass
            ret, frame = self.stream.read()
            if not ret:
                self.stop()
                return
            self.queue.put(frame)
                
    def read(self):
        return self.queue.get()
        
    def stop(self):
        self.stopped = True
        self.stream.release()

def update_parking_status(spot_id, status, number=None):
    try:
        data = {
            spot_id: {
                'status': 'occupied' if status == 'Occupied' else 'empty',
                'number': number
            }
        }
        response = requests.post('http://localhost:5000/update_parking', json=data)
        if response.status_code == 200:
            print(f"Successfully updated spot {spot_id}")
        else:
            print(f"Failed to update spot {spot_id}")
    except Exception as e:
        print(f"Error updating parking status: {e}")

# Initialize video stream
vs = VideoStream(0).start()  # Use 0 for webcam or your video source URL

# Load YOLO model
model = YOLO(r"weights/best.pt")
model.to('cuda' if torch.cuda.is_available() else 'cpu')

# Define parking spots (adjust coordinates based on your camera view)
parking_spots = {
    "P1": {"coords": (100, 100, 200, 200)},
    "P2": {"coords": (250, 100, 350, 200)},
    "P3": {"coords": (400, 100, 500, 200)},
    "P4": {"coords": (100, 250, 200, 350)},
    "P5": {"coords": (250, 250, 350, 350)},
    "P6": {"coords": (400, 250, 500, 350)},
}

try:
    while True:
        frame = vs.read()
        
        if vs.queue.qsize() > 1:
            continue
            
        # Perform detection
        with torch.no_grad():
            results = model(frame, verbose=False)
        
        # Process detections and update parking spots
        for spot_id, spot_data in parking_spots.items():
            spot_occupied = False
            car_number = None
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = int(box.cls[0])
                    
                    # Check if detection is within this parking spot
                    spot_x1, spot_y1, spot_x2, spot_y2 = spot_data["coords"]
                    if (x1 >= spot_x1 and x2 <= spot_x2 and 
                        y1 >= spot_y1 and y2 <= spot_y2):
                        spot_occupied = (label == 1)  # 1 for occupied
                        # Here you could add number plate detection if needed
                        
            # Update web interface
            update_parking_status(spot_id, "Occupied" if spot_occupied else "Empty", car_number)
            
            # Draw on frame
            color = (0, 0, 255) if spot_occupied else (0, 255, 0)
            cv2.rectangle(frame, 
                         (spot_data["coords"][0], spot_data["coords"][1]),
                         (spot_data["coords"][2], spot_data["coords"][3]),
                         color, 2)
            
        # Display frame
        cv2.imshow("Parking Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    vs.stop()
    cv2.destroyAllWindows() 