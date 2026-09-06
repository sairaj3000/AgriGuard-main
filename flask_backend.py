from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import cv2
from ultralytics import YOLO
import serial
import time
import os
import json
from datetime import datetime
import threading
import queue
import base64
import numpy as np
import pickle

# Import database helpers
from database import DB, init_database

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_database()
os.makedirs("owner_models", exist_ok=True)

# ==================== GLOBAL CONFIG ====================

CONFIG = {
    "CAMERA_INDEX": 0,                # Default camera
    "ARDUINO_PORT": "COM11",          # Arduino USB port
    "ARDUINO_BAUD": 9600,            # Arduino baud
    "TELEGRAM_BOT_TOKEN": "",        # Telegram bot token
    "TELEGRAM_CHAT_ID": "",          # Chat ID
    "MODEL_PATH": "yolov8n.pt",      # YOLO model
    "SAVE_OWNER_MODELS": "owner_models",   # Folder for LBPH models
    "SAVE_DETECTED_IMAGES": "detected_images"
}

# ==================== GLOBAL STATE ====================
surveillance_running = False

# Face recognition data (load from database)
face_recognizers = {}
face_cascade = None

# Thread-safe queues
frame_queue = queue.Queue(maxsize=2)

# Global objects
model = None
arduino = None
camera = None
surveillance_thread = None

# ==================== FACE RECOGNITION ====================
def init_face_recognition():
    """Initialize face recognition components"""
    global face_cascade, face_recognizers
    
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    # Load owners from database
    owners = DB.get_owners()
    for owner in owners:
        model_path = DB.get_owner_face_data(owner['id'])
        if model_path and os.path.exists(model_path):
            try:
                recognizer = cv2.face.LBPHFaceRecognizer_create()
                recognizer.read(model_path)
                face_recognizers[owner['id']] = recognizer
                face_recognizers[owner['id']] = recognizer
            except Exception as e:
                DB.add_log('error', f"Failed to load recognizer for {owner['name']}: {e}")
    
    DB.add_log('info', f'Loaded {len(face_recognizers)} registered owners')

def recognize_face(frame):
    """Recognize if face in frame belongs to an owner"""
    settings = DB.get_all_settings()
    
    if not settings.get('faceRecognition', False):
        return None, 0
    
    if not face_cascade:
        return None, 0
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    for (x, y, w, h) in faces:
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi, (200, 200))
        
        # Check against all registered owners
        owners = DB.get_owners()
        for owner in owners:
            owner_id = owner['id']
            if owner_id in face_recognizers:
                recognizer = face_recognizers[owner_id]
                try:
                    label, confidence = recognizer.predict(face_roi)
                    threshold = settings.get('faceThreshold', 70)
                    
                    if confidence < threshold:
                        return owner['name'], confidence
                except:
                    continue
    
    return None, 100

# ==================== ARDUINO CONTROLLER ====================
class ArduinoController:
    def __init__(self, port, baud_rate=9600):
        try:
            self.serial = serial.Serial(port, baud_rate, timeout=1)
            time.sleep(2)
            self.connected = True
        except Exception as e:
            self.serial = None
            self.connected = False
    
    def send_command(self, command):
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(command.encode())
                return True
            except:
                return False
        return False
    
    def close(self):
        if self.serial:
            self.serial.close()

# ==================== SURVEILLANCE WORKER ====================
def surveillance_worker():
    global model, arduino, camera, surveillance_running
    
    DB.add_log('info', 'Initializing surveillance system...')
    
    try:
        model = YOLO(CONFIG["MODEL_PATH"])
        DB.add_log('success', 'YOLOv8 model loaded successfully')
    except Exception as e:
        DB.add_log('error', f'Failed to load YOLO model: {e}')
        surveillance_running = False
        return
    
    settings = DB.get_all_settings()
    
    try:
        arduino = ArduinoController(CONFIG["ARDUINO_PORT"], CONFIG["ARDUINO_BAUD"])
        if arduino.connected:
            DB.add_log('success', 'Arduino connected successfully')
        else:
            DB.add_log('warning', 'Arduino connection failed')
    except Exception as e:
        DB.add_log('warning', f'Arduino error: {e}')
    
    try:
        camera = cv2.VideoCapture(CONFIG["CAMERA_INDEX"])
        if not camera.isOpened():
            DB.add_log('error', 'Failed to open camera')
            surveillance_running = False
            return
        DB.add_log('success', 'Camera started successfully')
    except Exception as e:
        DB.add_log('error', f'Camera error: {e}')
        surveillance_running = False
        return
    
    # Clear active intrusions on start
    DB.clear_active_intrusions()
    
    while surveillance_running:
        try:
            ret, frame = camera.read()
            if not ret:
                continue
            
            # Get current settings
            settings = DB.get_all_settings()
            action_cooldown = settings.get('actionCooldown', 3)
            intrusion_timeout = settings.get('intrusionTimeout', 10)
            confidence_threshold = settings.get('confidenceThreshold', 0.5)
            
            results = model(frame, conf=confidence_threshold, verbose=False)
            
            current_time = time.time()
            detected_this_frame = set()
            active_intrusions = DB.get_active_intrusions()
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # Check for owner if person detected
                    if class_name == 'person':
                        owner_name, face_conf = recognize_face(frame)
                        
                        if owner_name:
                            # Owner detected - log only, no actions
                            if 'owner' not in active_intrusions:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                image_filename = f"OWNER_{owner_name}_{timestamp}.jpg"
                                image_path = os.path.join(CONFIG["SAVE_DETECTED_IMAGES"], image_filename)
                                os.makedirs('detected_images', exist_ok=True)
                                cv2.imwrite(image_path, frame)
                                
                                DB.add_detection('owner', confidence, f'No action - {owner_name} recognized', 
                                               image_filename, owner_name, is_owner=True)
                                DB.add_log('info', f'Owner {owner_name} detected (confidence: {face_conf:.1f})')
                            
                            DB.set_active_intrusion('owner', current_time, False, current_time)
                            detected_this_frame.add('owner')
                            continue
                    
                    # Map to intruder type
                    intruder_type = None
                    action = None
                    command = None
                    
                    if class_name == 'bird':
                        intruder_type = 'bird'
                        action = 'Motor Rotation'
                        command = 'M'
                    elif class_name == 'person':
                        intruder_type = 'person'
                        action = 'Emergency Lights'
                        command = 'L'
                    elif class_name == 'elephant':
                        intruder_type = 'elephant'
                        action = 'Buzzer Sound'
                        command = 'B'
                    elif class_name in ['bear', 'zebra', 'giraffe', 'deer', 'cow', 'horse', 'sheep', 'dog', 'cat']:
                        intruder_type = 'wild_animal'
                        action = 'Buzzer Sound'
                        command = 'B'
                    
                    if intruder_type:
                        detected_this_frame.add(intruder_type)
                        is_new_intrusion = intruder_type not in active_intrusions
                        
                        # NEW INTRUSION
                        if is_new_intrusion:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            image_filename = f"{intruder_type}_{timestamp}.jpg"
                            image_path = os.path.join('detected_images', image_filename)
                            os.makedirs('detected_images', exist_ok=True)
                            cv2.imwrite(image_path, frame)
                            
                            DB.add_detection(intruder_type, confidence, action, image_filename)
                            DB.add_log('warning', f'🚨 NEW {intruder_type.upper()} intrusion detected - Telegram alert sent')
                            
                            # Send Telegram alert
                            if settings.get('telegramAlerts', False):
                                send_telegram_alert(intruder_type, confidence, action, image_path, settings)
                            
                            DB.set_active_intrusion(intruder_type, current_time, True, current_time)
                            
                            # Trigger Arduino
                            if arduino and arduino.connected:
                                arduino.send_command(command)
                        
                        # ONGOING INTRUSION
                        else:
                            intrusion_data = active_intrusions[intruder_type]
                            last_action = intrusion_data.get('last_action', 0)
                            
                            # Update last seen
                            DB.set_active_intrusion(intruder_type, current_time, True, last_action)
                            
                            # Trigger Arduino if cooldown passed
                            if current_time - last_action >= action_cooldown:
                                if arduino and arduino.connected:
                                    arduino.send_command(command)
                                    DB.add_log('info', f'↻ Continuing {action} for ongoing {intruder_type} intrusion')
                                
                                DB.set_active_intrusion(intruder_type, current_time, True, current_time)
            
            # Check for ended intrusions
            active_intrusions = DB.get_active_intrusions()
            for intruder_type, data in list(active_intrusions.items()):
                if (current_time - data['last_seen']) > intrusion_timeout:
                    DB.remove_active_intrusion(intruder_type)
                    DB.add_log('success', f'✓ {intruder_type.upper()} intrusion ended - Ready for new detection')
                    
                    # Stop Arduino
                    if arduino and arduino.connected:
                        arduino.send_command('S')
            
            # Add annotated frame to queue
            annotated_frame = results[0].plot()
            if not frame_queue.full():
                frame_queue.put(annotated_frame)
            
            time.sleep(0.03)
            
        except Exception as e:
            DB.add_log('error', f'Detection error: {e}')
    
    if camera:
        camera.release()
    if arduino:
        arduino.close()
    DB.add_log('info', 'Surveillance stopped')

def send_telegram_alert(intruder_type, confidence, action, image_path, settings):
    """Send Telegram alert with photo"""
    try:
        import requests
        bot_token = CONFIG["TELEGRAM_BOT_TOKEN"]
        chat_id = CONFIG["TELEGRAM_CHAT_ID"]

        if not bot_token or not chat_id:
            return
        
        alert_message = f"""
🚨 <b>NEW INTRUDER DETECTED</b> 🚨

🔍 <b>Type:</b> {intruder_type.upper()}
📊 <b>Confidence:</b> {confidence:.2%}
⚡ <b>Action:</b> {action}
🕐 <b>Time:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📍 <b>Status:</b> UNIQUE INTRUSION

Arduino defense activated continuously while intruder present.
        """
        
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        with open(image_path, 'rb') as photo:
            files = {"photo": photo}
            data = {"chat_id": chat_id, "caption": alert_message.strip(), "parse_mode": "HTML"}
            requests.post(url, data=data, files=files)
    except Exception as e:
        DB.add_log('error', f'Telegram error: {e}')

def generate_frames():
    while surveillance_running:
        try:
            if not frame_queue.empty():
                frame = frame_queue.get()
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Streaming error: {e}")
        time.sleep(0.03)

# ==================== API ROUTES ====================

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'running': surveillance_running,
        'stats': DB.get_stats(),
        'settings': DB.get_all_settings()
    })

@app.route('/api/system/start', methods=['POST'])
def start_system():
    global surveillance_thread, surveillance_running
    
    if surveillance_running:
        return jsonify({'error': 'System already running'}), 400
    
    surveillance_running = True
    surveillance_thread = threading.Thread(target=surveillance_worker, daemon=True)
    surveillance_thread.start()
    
    DB.add_log('success', 'Surveillance system started')
    return jsonify({'status': 'started'})

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    global surveillance_running
    
    if not surveillance_running:
        return jsonify({'error': 'System not running'}), 400
    
    surveillance_running = False
    DB.clear_active_intrusions()
    DB.add_log('error', 'Surveillance system stopped')
    return jsonify({'status': 'stopped'})

@app.route('/api/detections', methods=['GET'])
def get_detections():
    return jsonify(DB.get_detections(50))

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(DB.get_logs(100))

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    DB.clear_logs()
    DB.add_log('info', 'Logs cleared')
    return jsonify({'status': 'cleared'})

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        return jsonify(DB.get_all_settings())
    
    elif request.method == 'POST':
        data = request.get_json()
        DB.update_settings(data)
        DB.add_log('success', 'Settings updated successfully')
        return jsonify({'status': 'updated', 'settings': DB.get_all_settings()})

@app.route('/api/action/manual', methods=['POST'])
def manual_action():
    data = request.get_json()
    action_type = data.get('action')
    
    if not arduino or not arduino.connected:
        return jsonify({'error': 'Arduino not connected'}), 400
    
    command_map = {'motor': 'M', 'buzzer': 'B', 'lights': 'L', 'stop': 'S'}
    
    if action_type.lower() in command_map:
        arduino.send_command(command_map[action_type.lower()])
        DB.add_log('info', f'Manual action triggered: {action_type}')
        return jsonify({'status': 'executed', 'action': action_type})
    
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/video_feed')
def video_feed():
    if not surveillance_running:
        return jsonify({'error': 'System not running'}), 400
    
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/image/<filename>')
def get_image(filename):
    try:
        image_path = os.path.join('detected_images', filename)
        return send_file(image_path, mimetype='image/jpeg')
    except:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/api/stats/export', methods=['GET'])
def export_stats():
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Type', 'Confidence', 'Action', 'Timestamp', 'Image', 'Owner Name'])
    for detection in DB.get_detections(1000):
        writer.writerow([
            detection['type'],
            detection['confidence'],
            detection['action'],
            detection['timestamp'],
            detection['image'],
            detection.get('owner_name', '')
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=detections.csv'}
    )

@app.route('/api/test/telegram', methods=['POST'])
def test_telegram():
    try:
        import requests
        settings = DB.get_all_settings()
        bot_token = settings.get('telegramBotToken', '')
        chat_id = settings.get('telegramChatId', '')
        
        if not bot_token or not chat_id:
            return jsonify({'error': 'Telegram credentials not configured'}), 400
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': '🧪 Test Alert from AgriGuard Pro\n\nTelegram integration is working correctly!'
        }
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            DB.add_log('success', 'Test alert sent to Telegram')
            return jsonify({'status': 'sent'})
        else:
            DB.add_log('error', 'Failed to send Telegram alert')
            return jsonify({'error': 'Failed to send'}), 400
    except Exception as e:
        DB.add_log('error', f'Telegram test error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/face/upload', methods=['POST'])
def upload_face_images():
    try:
        name = request.form.get('name')
        files = request.files.getlist('images')

        if not name or not files:
            return jsonify({'error': 'Name and images required'}), 400

        owner_dir = os.path.join('owner_faces', name.replace(' ', '_'))
        os.makedirs(owner_dir, exist_ok=True)

        saved = 0
        for file in files:
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                filename = os.path.join(owner_dir, f"sample_{saved:03d}.jpg")
                cv2.imwrite(filename, img)
                saved += 1

        return jsonify({'status': 'uploaded', 'saved': saved})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== FACE RECOGNITION API ====================

@app.route('/api/face/owners', methods=['GET'])
def get_owners():
    return jsonify(DB.get_owners())

@app.route('/api/face/capture', methods=['POST'])
def capture_face():
    try:
        data = request.get_json()
        name = data.get('name')
        image_data = data.get('image')
        sample_number = data.get('sample_number', 0)
        
        if not name or not image_data:
            return jsonify({'error': 'Name and image required'}), 400
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        if not face_cascade:
            return jsonify({'error': 'Face cascade not initialized'}), 500
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
        
        if len(faces) == 0:
            return jsonify({'error': 'No face detected', 'retry': True}), 400
        
        if len(faces) > 1:
            return jsonify({'error': 'Multiple faces detected', 'retry': True}), 400
        
        owner_dir = os.path.join('owner_faces', name.replace(' ', '_'))
        os.makedirs(owner_dir, exist_ok=True)
        
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        face_roi = gray[y:y+h, x:x+w]
        face_roi_resized = cv2.resize(face_roi, (200, 200))
        
        filename = os.path.join(owner_dir, f'sample_{sample_number:03d}.jpg')
        cv2.imwrite(filename, face_roi_resized)
        
        return jsonify({'status': 'captured', 'sample': sample_number})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/face/train', methods=['POST'])
def train_face():
    try:
        data = request.get_json()
        name = data.get('name')
        owner_dir = os.path.join('owner_faces', name.replace(' ', '_'))
        
        if not os.path.exists(owner_dir):
            return jsonify({'error': 'No face samples found'}), 400
        
        face_images = []
        face_labels = []
        
        for filename in os.listdir(owner_dir):
            if filename.endswith('.jpg'):
                img_path = os.path.join(owner_dir, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    face_images.append(img)
                    face_labels.append(1)
        
        if len(face_images) < 10:
            return jsonify({'error': f'Only {len(face_images)} valid samples. Need at least 10.'}), 400
        
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(face_images, np.array(face_labels))
        
        owner_id = name.replace(' ', '_').lower()
        model_path = os.path.join(CONFIG["SAVE_OWNER_MODELS"], f"{owner_id}.xml")
        recognizer.write(model_path)

        DB.add_owner(owner_id, name, len(face_images), model_path)
        face_recognizers[owner_id] = recognizer

        
        DB.add_log('success', f'Owner {name} registered with {len(face_images)} samples')
        return jsonify({'status': 'trained', 'samples': len(face_images)})
        
    except Exception as e:
        DB.add_log('error', f'Training error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/face/owner/<owner_id>', methods=['DELETE'])
def delete_owner(owner_id):
    try:
        DB.delete_owner(owner_id)
        model_path = DB.get_owner_face_data(owner_id)
        if model_path and os.path.exists(model_path):
            os.remove(model_path)
        if owner_id in face_recognizers:
            del face_recognizers[owner_id]
        DB.add_log('info', f'Owner {owner_id} deleted')
        return jsonify({'status': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/face/recognize', methods=['POST'])
def recognize_face_test():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        owner_name, confidence = recognize_face(frame)
        
        if owner_name:
            return jsonify({'recognized': True, 'name': owner_name, 'confidence': int(100 - confidence)})
        else:
            return jsonify({'recognized': False, 'name': 'Unknown', 'confidence': 0})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    print("=" * 60)
    print("🌾 AgriGuard Pro - Backend API Server with SQLite")
    print("=" * 60)
    print("\n✓ Database connected")
    print("✓ Server starting on http://localhost:5000")
    print("✓ API endpoints ready")
    print("✓ CORS enabled for frontend")
    print("\nPress Ctrl+C to stop\n")
    
    os.makedirs(CONFIG["SAVE_DETECTED_IMAGES"], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('owner_faces', exist_ok=True)
    os.makedirs(CONFIG["SAVE_OWNER_MODELS"], exist_ok=True)

    init_face_recognition()
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)