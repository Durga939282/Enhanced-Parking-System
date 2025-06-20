# DroidCam Configuration
def get_video_url():
    return "http://100.116.151.91:4747/video"  # Ensure this URL is accessible

# Model Configuration
MODEL_PATH = r"C:\vs_code\dp_21\dp_21\smart_parking\weights\best.pt"  # Path to your trained YOLO model

# OCR Configuration
OCR_LANGUAGES = ['en']  # Languages for license plate recognition
MIN_OCR_CONFIDENCE = 0.6  # Minimum confidence for OCR detection

# Flask Configuration
SECRET_KEY = 'your-secret-key-here'
DATABASE_URI = 'sqlite:///parking.db'
