from threading import Lock
import threading
import pytesseract
from PIL import Image
import cv2
import numpy as np

class ParkingState:
    def __init__(self):
        self.spots = {i: {'status': 'empty', 'plate': None} for i in range(1, 13)}
        self.lock = threading.Lock()
        self.available = 12
        self.occupied = 0
        self.last_update = None

    def update_spots_from_detection(self, detections):
        """Update spots based on model detections"""
        with self.lock:
            # Reset counts
            self.available = 12
            self.occupied = 0
            
            # Update based on detections
            for spot_num, data in detections.items():
                if spot_num in self.spots:
                    if isinstance(data, dict):
                        self.spots[spot_num]['status'] = data.get('status', 'empty')
                        if 'plate' in data and data['plate']:
                            self.spots[spot_num]['plate'] = data['plate']
                        elif data.get('status') == 'empty':
                            self.spots[spot_num]['plate'] = None
                        
                        # Count occupied spots
                        if data.get('status') == 'occupied':
                            self.occupied += 1
                            self.available -= 1
                    else:
                        # Handle string format (backwards compatibility)
                        self.spots[spot_num]['status'] = data
                        if data == 'empty':
                            self.spots[spot_num]['plate'] = None
                        # Count occupied spots (for string data)
                        elif data == 'occupied':
                            self.occupied += 1
                            self.available -= 1

    def get_spot_status(self, spot_num):
        with self.lock:
            return self.spots.get(spot_num, {'status': 'unknown', 'plate': None})

    def get_all_spots(self):
        with self.lock:
            return self.spots.copy()

    def get_status(self):
        with self.lock:
            return {
                'total_spots': 12,
                'available': self.available,
                'occupied': self.occupied,
                'spots': [{'id': i, 'status': self.spots[i]['status'], 'plate': self.spots[i]['plate']} for i in range(1, 13)]
            }

    def update_spots_from_image(self, image):
        """Update spots based on OCR detection from the image."""
        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply thresholding to get a binary image
        _, binary_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY_INV)

        # Use Tesseract to do OCR on the processed image
        detected_text = pytesseract.image_to_string(binary_image, config='--psm 6')

        # Process detected text to update parking spots
        for line in detected_text.splitlines():
            if line.strip():  # Check if the line is not empty
                # Assuming the format is "Spot X: Plate Y"
                parts = line.split(':')
                if len(parts) == 2:
                    spot_num = int(parts[0].replace('Spot', '').strip())
                    plate = parts[1].strip()
                    if spot_num in self.spots:
                        self.spots[spot_num]['status'] = 'occupied'
                        self.spots[spot_num]['plate'] = plate
                        self.occupied += 1
                        self.available -= 1
                    else:
                        print(f"Spot number {spot_num} is out of range.")

parking_state = ParkingState() 