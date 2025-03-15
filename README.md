🚦 AI-Powered Adaptive Traffic Light System

🔥 Overview
The AI-Powered Adaptive Traffic Light System is a smart traffic management solution that dynamically adjusts traffic lights based on real-time congestion analysis. By leveraging computer vision, machine learning, and IoT communication, this system enhances urban mobility, reduces congestion, and optimizes traffic flow.

⚡ Key Features

✅ AI-Based Traffic Analysis – Uses a trained YOLOv5 model to detect vehicles and predict congestion patterns.
✅ Dynamic Traffic Light Control – Automatically adjusts signal timings based on live traffic density.
✅ IoT Integration (MQTT) – Uses an MQTT-based communication system to update traffic lights in real-time.
✅ Live Analytics Dashboard – A Flask + AWS dashboard visualizes congestion hotspots and system performance.
✅ Edge Processing on Raspberry Pi – Runs AI inference directly on a Raspberry Pi 5 with the Hailo AI Kit for real-time traffic detection.

📌 System Architecture

1️⃣ Traffic Data Collection

Streams live traffic footage from public cameras (or local webcams).
YOLOv5 detects vehicles (cars, buses, trucks) in each frame.
2️⃣ AI-Based Traffic Analysis

Analyzes congestion levels based on vehicle count.
A TensorFlow-trained ML model predicts future traffic patterns.
3️⃣ MQTT-Based Traffic Light Control

Traffic light duration adapts dynamically based on congestion.
Uses Mosquitto MQTT to communicate with IoT traffic lights.
4️⃣ Live Dashboard & Analytics

A Flask + AWS-hosted web dashboard visualizes traffic conditions.
Displays real-time vehicle counts, congestion levels, and traffic trends.
🛠️ Setup & Installation

1️⃣ Clone the Repository
git clone https://github.com/kevinomerkilic/smart-traffic-ai.git
cd smart-traffic-ai
2️⃣ Set Up Virtual Environment
python3 -m venv yolov5-venv
source yolov5-venv/bin/activate
pip install -r requirements.txt
3️⃣ Download Pretrained Model
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt
4️⃣ Run YOLOv5 for Traffic Detection
python detect.py --weights yolov5s.pt --source "https://your-traffic-camera-url.m3u8"
5️⃣ Set Up MQTT Broker (Mosquitto)
Install Mosquitto on the Raspberry Pi:

sudo apt update
sudo apt install mosquitto mosquitto-clients
Run the broker:

mosquitto -v
Test publishing messages:

mosquitto_pub -h localhost -t "traffic/lights" -m "green"
6️⃣ Run Flask Dashboard
python app.py
Access it in a browser at:

http://localhost:5000
📊 Live Dashboard Preview

The Flask-based dashboard provides: ✔ Real-time congestion updates
✔ Vehicle count graphs
✔ Adaptive traffic signal status
✔ Traffic trend predictions

🤖 How AI Model Works

The system uses a YOLOv5 model trained on a custom dataset of traffic images.
It detects vehicles and classifies them into cars, buses, and trucks.
A TensorFlow prediction model forecasts traffic congestion trends.
The system dynamically adjusts signal timing to optimize flow.
🚀 Future Improvements

🔹 Edge AI Optimization: Improve inference speed using TensorRT.
🔹 Multi-Camera Support: Integrate multiple street cameras for better accuracy.
🔹 Integration with City Infrastructure: Work with smart city APIs for real-world deployment.

👨‍💻 Developer

💡  Omer Kilic – AI & IoT System Development UI/UX, Backend, Data Science

📜 License

This project is licensed under the AGPL-3.0 License.

This README.md gives a comprehensive and structured overview of your project, including setup instructions, technical details, and future improvements. 🚀 Let me know if you'd like any modifications! 🚦
