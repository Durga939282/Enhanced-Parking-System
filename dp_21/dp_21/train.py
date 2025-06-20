from ultralytics import YOLO
import yaml
from pathlib import Path

def load_config(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)

def train_model(config_path="C:/Users/ganes/PycharmProjects/dp_21/parking.yaml"):
    # Load configuration
    config = load_config(config_path)
    
    # Initialize model
    model = YOLO(config["model_path"])
    
    # Train model
    model.train(
        data=config["data_yaml"],
        epochs=config["epochs"],
        batch=config["batch_size"],
        imgsz=config["image_size"],
        device=config["device"],
        project=config["project_path"],
        name=config["experiment_name"]
    )

if __name__ == "__main__":
    train_model()
