# Enhanced-Parking-System
🚗 Enhanced Parking System (DP_21) 🚦 Welcome to the Enhanced Parking System (DP_21)! 🎉 This is a cutting-edge, computer vision-based solution designed to revolutionize parking management. 🌆 Using YOLOv8 for real-time vehicle detection, Flask for a dynamic web interface, and OpenCV for video processing, this project monitors parking spot occupancy via a DroidCam video stream. 🌐 Perfect for smart cities, commercial lots, or personal use! 🏙️

🌟 Features 🌟

🚘 Real-Time Detection: Leverages YOLOv8 to detect vehicles and update parking status instantly.

🌐 Web Dashboard: A vibrant Flask-based interface for monitoring parking spots.

🔒 User Authentication: Secure login and registration with password hashing.

📹 Video Streaming: Integrates with DroidCam for live feed input.

🎯 Model Training: Includes tools to train and evaluate the YOLOv8 model.

💾 Database Support: Uses SQLite to store user and parking data.

🛠️ Requirements 🛠️

🐍 Python: Version 3.8 or higher 📦 Dependencies (in requirements.txt):flask==2.0.1 flask-sqlalchemy==2.5.1 opencv-python==4.5.3.56 torch==1.9.0 ultralytics==8.0.0 requests==2.26.0 numpy==1.21.2

💻 Hardware: GPU recommended for faster inference (optional) 📱 Software: DroidCam on a mobile device or compatible camera

🎉 How to Get Started 🎉 🚀 Installation Steps

Clone the Repo: git clone https://github.com/Durga939282/DP_21.git cd DP_21

Set Up Virtual Environment 🌱: python -m venv venv s ource venv/bin/activate # On Windows: venv\Scripts\activate

Install Dependencies 📥: pip install -r requirements.txt

Configure the System ⚙️:

Update config.py with your DroidCam IP (e.g., http://192.168.1.100:4747/video). Set MODEL_PATH to smart_parking/weights/best.pt. Change SECRET_KEY to a secure string.

Initialize Database 💽: python -c "from app.models import db; db.create_all()"

🚗 How to Use 🚗 🎓 Training the Model

Prepare dataset in data/train, data/val, data/test.
Update smart_parking/args.yaml with paths and parameters.
Run:python train.py
Outputs saved in smart_parking/weights.

🕒 Testing the System

Test video and detection: python test.py

Press q to exit.
Run the full app: python run.py

Access at http://localhost:5000.

Web Interface 🌐:

Register at /register.
Login at /login.
View dashboard for real-time updates.
📂 Project Structure 📂

app/ 🌿: init.py, models.py, parking_state.py, routes.py, static/, templates/

detection/ 🔍: init.py, model.py, video_stream.py

smart_parking/ 🏋️: weights/, args.yaml, training visuals (e.g., confusion_matrix.png)

data/ 📊 test/, train/, val/, split.py, xml_to_yolo.py

config.py ⚙️: Configuration settings run.py ▶️: Main execution script test.py ✅: Testing script train.py 🎓: Training script requirements.txt 📋: Dependency list

📸 Output Screenshots 📸:
![Screenshot (26)](https://github.com/user-attachments/assets/0f20300a-46f0-4dc9-8995-ac7fb85a4753)

![Screenshot (27)](https://github.com/user-attachments/assets/32060634-0f1d-4fbb-9dc3-2e46bc4e793d)

![Screenshot (30)](https://github.com/user-attachments/assets/b7298efc-6eea-4f0d-bdee-2ea17602dc9b)

![Screenshot (29)](https://github.com/user-attachments/assets/788abe71-7871-494e-8f2a-08524e8b818f)

![Screenshot (28)](https://github.com/user-attachments/assets/d6765b3e-aa7a-4c61-8d84-a1e78d93055a)


💡 Benefits 💡

⏱️ Efficiency: Automates parking spot monitoring.

🌱 Scalability: Easily adaptable to different layouts.

🔐 Security: User authentication protects access.

📊 Insights: Visual analytics from training outputs.

🌍 Sustainability: Reduces manual effort in parking management.

⚙️ Advanced Configuration ⚙️

Parking Spots: Edit detection.py to adjust parking_spots coordinates.

Model Params: Modify smart_parking/args.yaml (e.g., epochs, batch_size).

Video Settings: Tune video_stream.py for resolution and FPS.

❗ Troubleshooting ❗

📡 Video Not Connecting: Check DroidCam IP and network.

🚫 Model Load Failure: Verify MODEL_PATH and best.pt.

🐞 Flask Errors: Ensure SECRET_KEY is set; check logs.

📉 Low Accuracy: Retrain with more data or adjust confidence in model.py.

🤝 Contributing 🤝

Love to contribute? 🚀

Fork the repo! 🍴

Create a branch: git checkout -b feature-branch

Commit: git commit -m "Add awesome feature"

Push: git push origin feature-branch

Open a PR! 🎉

📜 License 📜

This project is licensed under the MIT License. Check the LICENSE file for details! ✅
