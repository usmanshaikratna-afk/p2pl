import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # MongoDB Atlas Configuration
    MONGO_URI = os.environ.get('MONGO_URI') or \
        'mongodb+srv://username:password@cluster.mongodb.net/smart_roads?retryWrites=true&w=majority'
    
    # MongoDB Database Name
    MONGO_DBNAME = 'smart_roads'
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi'}
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_TYPE = 'filesystem'
    
    # Security
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ESP32 Camera Configuration
    ESP32_CAM_IP = os.environ.get('ESP32_CAM_IP', '192.168.1.100')
    ESP32_CAM_PORT = int(os.environ.get('ESP32_CAM_PORT', 80))
    ESP32_STREAM_URL = f"http://{ESP32_CAM_IP}:{ESP32_CAM_PORT}/stream"
    ESP32_SNAPSHOT_URL = f"http://{ESP32_CAM_IP}:{ESP32_CAM_PORT}/capture"
    
    # AI Model Configuration
    MODEL_PATH = os.path.join(basedir, 'ml_models', 'road_defect_model.h5')
    MODEL_CLASSES = ['pothole', 'crack', 'speed_hump', 'normal_road', 'debris', 'flooding']
    CONFIDENCE_THRESHOLD = 0.7
    
    # WebSocket Configuration
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # GPS Configuration
    GPS_SIMULATION = os.environ.get('GPS_SIMULATION', 'true').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        os.makedirs(os.path.join(basedir, 'uploads', 'reports'), exist_ok=True)
        os.makedirs(os.path.join(basedir, 'uploads', 'detections'), exist_ok=True)
        os.makedirs(os.path.join(basedir, 'uploads', 'temp'), exist_ok=True)
        os.makedirs(os.path.join(basedir, 'ml_models'), exist_ok=True)