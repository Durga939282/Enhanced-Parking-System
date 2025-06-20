from ultralytics import YOLO
import torch

class ParkingDetector:
    def __init__(self, model_path, conf=0.25, iou=0.45):
        self.model = YOLO(model_path)
        self.model.to('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.conf = conf
        self.model.iou = iou
        self.model.agnostic = True
        self.model.max_det = 10

    def detect(self, frame):
        with torch.no_grad():
            results = self.model(frame, verbose=False)
        return results 