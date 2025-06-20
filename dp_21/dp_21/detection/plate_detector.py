import easyocr
import cv2
import numpy as np

class PlateDetector:
    def __init__(self, languages=['en'], min_confidence=0.5):
        print("Initializing EasyOCR with languages:", languages)
        try:
            self.reader = easyocr.Reader(languages)
            print("EasyOCR initialized successfully")
        except Exception as e:
            print(f"Error initializing EasyOCR: {e}")
            raise
        self.min_confidence = min_confidence
        self.plate_cache = {}  # Cache to improve stability

    def detect_plate(self, image, bbox):
        try:
            # Extract the region containing the vehicle
            x1, y1, x2, y2 = map(int, bbox)
            
            # Check if region is valid
            if x1 >= x2 or y1 >= y2 or x1 < 0 or y1 < 0 or x2 > image.shape[1] or y2 > image.shape[0]:
                print(f"Invalid bounding box: {bbox}")
                return None, 0.0
                
            vehicle_region = image[y1:y2, x1:x2]
            
            # Basic validation
            if vehicle_region.size == 0 or vehicle_region.shape[0] == 0 or vehicle_region.shape[1] == 0:
                print("Invalid vehicle region, skipping plate detection")
                return None, 0.0
            
            # Resize for better OCR
            height = min(200, vehicle_region.shape[0])
            width = int(height * (vehicle_region.shape[1] / vehicle_region.shape[0]))
            vehicle_region = cv2.resize(vehicle_region, (width, height))
            
            # Convert to grayscale
            gray = cv2.cvtColor(vehicle_region, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Detect text in the region
            results = self.reader.readtext(thresh)
            
            # Process results
            valid_plates = []
            for (box, text, prob) in results:
                if prob > self.min_confidence:
                    text = self.clean_plate_text(text)
                    if self.is_valid_plate(text):
                        valid_plates.append((text, prob))
            
            # Return highest confidence plate
            if valid_plates:
                valid_plates.sort(key=lambda x: x[1], reverse=True)
                return valid_plates[0]
            
            return None, 0.0
            
        except Exception as e:
            print(f"Error in plate detection: {e}")
            return None, 0.0
    
    @staticmethod
    def clean_plate_text(text):
        # Remove unwanted characters and normalize
        text = text.upper().strip()
        text = ''.join(c for c in text if c.isalnum())
        return text
    
    @staticmethod
    def is_valid_plate(text):
        # Basic validation for license plate format
        if len(text) >= 4 and len(text) <= 10:
            has_letters = any(c.isalpha() for c in text)
            has_numbers = any(c.isdigit() for c in text)
            return has_letters and has_numbers
        return False 