import os
import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify, url_for, send_from_directory
from flask_socketio import SocketIO
from datetime import datetime
import logging
from ultralytics import YOLO
import threading
from engineio.async_drivers import threading as async_threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with explicit static and template folders
app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static',
    template_folder='templates'
)

# Configure Flask app
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize SocketIO with explicit configuration
socketio = SocketIO(
    app,
    async_mode='threading',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

# Initialize YOLO model
try:
    model = YOLO('yolov5su.pt')
    logger.info("✅ YOLO model loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading YOLO model: {e}")
    model = None

# Global variables for detection sharing
latest_frame = None
frame_lock = threading.Lock()
current_detection = None
detection_lock = threading.Lock()

def process_frame(frame):
    """Process frame through YOLOv5"""
    global current_detection
    
    try:
        # Run YOLOv5 detection
        results = model(frame)
        annotated_frame = results[0].plot()
        detections = results[0].boxes.data.tolist()
        
        # Calculate vehicle count and congestion
        vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
        vehicle_count = sum(1 for d in detections if int(d[5]) in vehicle_classes)
        
        # Create detection data with class information
        detection_data = []
        for d in detections:
            detection_data.append({
                'class': int(d[5]),
                'confidence': float(d[4]),
                'bbox': [float(x) for x in d[:4]]
            })
        
        # Determine congestion level
        if vehicle_count <= 5:
            congestion_level = 'low'
        elif vehicle_count <= 10:
            congestion_level = 'moderate'
        elif vehicle_count <= 15:
            congestion_level = 'high'
        else:
            congestion_level = 'severe'
            
        # Log detection data for debugging
        logger.info(f"Detected {len(detections)} objects, {vehicle_count} vehicles")
        
        # Create update data
        update_data = {
            'detections': detection_data,
            'timestamp': datetime.now().isoformat(),
            'vehicle_count': vehicle_count,
            'congestion_level': congestion_level,
            'total_objects': len(detections)
        }
        
        # Store detection data for WebSocket updates
        with detection_lock:
            current_detection = update_data
        
        return annotated_frame, detections
        
    except Exception as e:
        logger.error(f"❌ Error processing frame: {str(e)}")
        return frame, []

def emit_detection_updates():
    """Background thread to emit detection updates"""
    while True:
        try:
            with detection_lock:
                if current_detection:
                    socketio.emit('detection_update', current_detection)
            threading.Event().wait(0.1)  # Small delay between updates
        except Exception as e:
            logger.error(f"❌ Error in detection emitter: {e}")
            threading.Event().wait(1)  # Longer delay on error

def generate_frames():
    """Generate video frames with object detection"""
    camera_url = os.getenv('CAMERA_URL', "https://s7.nysdot.skyvdn.com/rtplive/R4_200/playlist.m3u8")
    logger.info(f"✅ Attempting to connect to camera: {camera_url}")
    
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        logger.error("❌ Failed to open video capture")
        return
    
    try:
        while True:
            success, frame = cap.read()
            if not success:
                logger.error("❌ Failed to read frame")
                break
            
            # Process frame and get results
            annotated_frame, _ = process_frame(frame)
            
            # Convert frame to JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        logger.error(f"❌ Error in generate_frames: {e}")
    finally:
        cap.release()

@app.route('/')
def index():
    """Render main dashboard"""
    try:
        logger.info("✅ Rendering index page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"❌ Error rendering index page: {e}")
        return str(e), 500

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    try:
        logger.info("✅ Starting video feed")
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"❌ Error in video feed: {e}")
        return str(e), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        logger.info(f"✅ Serving static file: {filename}")
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        logger.error(f"❌ Error serving static file {filename}: {e}")
        return str(e), 404

@app.route('/health')
def health():
    """Health check endpoint"""
    status = {
        'yolo_model': model is not None,
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status)

@app.route('/test')
def test():
    """Test route to verify Flask is working"""
    return jsonify({
        "status": "ok",
        "static_url": url_for('static', filename='js/main.js'),
        "template_url": url_for('index')
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("✅ Client connected")
    socketio.emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("❌ Client disconnected")

if __name__ == '__main__':
    # Start detection emitter thread
    emitter_thread = threading.Thread(target=emit_detection_updates, daemon=True)
    emitter_thread.start()
    
    logger.info("🚀 Starting Flask application")
    socketio.run(app, debug=True, host='127.0.0.1', port=5007, allow_unsafe_werkzeug=True)
