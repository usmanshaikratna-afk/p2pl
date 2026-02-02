import cv2
import numpy as np
import requests
import threading
import time
import json
from datetime import datetime
from flask import current_app
from models import CameraDetection, RoadReport, User
from ai_detection import detector
import base64
import io
from PIL import Image

class ESP32Camera:
    def __init__(self, ip=None, port=None):
        self.ip = ip or current_app.config['ESP32_CAM_IP']
        self.port = port or current_app.config['ESP32_CAM_PORT']
        self.stream_url = f"http://{self.ip}:{self.port}/stream"
        self.snapshot_url = f"http://{self.ip}:{self.ip}/capture"
        self.is_streaming = False
        self.stream_thread = None
        self.gps_data = None
        self.camera_id = f"esp32_{self.ip.replace('.', '_')}"
        
    def get_snapshot(self):
        """Capture a single snapshot from ESP32 camera"""
        try:
            response = requests.get(self.snapshot_url, timeout=5)
            if response.status_code == 200:
                # Convert bytes to image
                image_array = np.frombuffer(response.content, dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                return image
        except Exception as e:
            print(f"Error getting snapshot: {e}")
        return None
    
    def start_streaming(self, gps_callback=None, detection_callback=None):
        """Start streaming and processing frames"""
        if self.is_streaming:
            return False
        
        self.is_streaming = True
        self.gps_callback = gps_callback
        self.detection_callback = detection_callback
        
        self.stream_thread = threading.Thread(
            target=self._stream_worker,
            daemon=True
        )
        self.stream_thread.start()
        return True
    
    def stop_streaming(self):
        """Stop the streaming thread"""
        self.is_streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=2)
        self.stream_thread = None
    
    def _stream_worker(self):
        """Worker thread for streaming and processing"""
        cap = None
        frame_count = 0
        
        try:
            # Open video stream
            cap = cv2.VideoCapture(self.stream_url)
            if not cap.isOpened():
                print(f"Failed to open stream: {self.stream_url}")
                return
            
            print(f"Started streaming from ESP32 camera at {self.stream_url}")
            
            while self.is_streaming and cap.isOpened():
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                
                # Get current GPS data if callback available
                if self.gps_callback:
                    self.gps_data = self.gps_callback()
                
                # Process frame for defects
                detection_result = detector.process_video_frame(
                    frame, frame_count, self.gps_data
                )
                
                if detection_result and detection_result.get('detected'):
                    # Save detection to database
                    self._save_detection(detection_result, frame)
                    
                    # Create report if confidence is high
                    if detection_result['confidence'] > 0.8:
                        self._create_report(detection_result)
                    
                    # Call detection callback if available
                    if self.detection_callback:
                        self.detection_callback(detection_result)
                
                # Limit frame rate
                time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            if cap:
                cap.release()
            self.is_streaming = False
            print("Streaming stopped")
    
    def _save_detection(self, detection_result, original_frame):
        """Save detection to database"""
        try:
            # Create detection record
            detection = CameraDetection()
            detection.camera_id = self.camera_id
            detection.location = detection_result.get('gps')
            detection.image_url = detection_result.get('image_path', '')
            detection.detections = [{
                'type': detection_result['defect_type'],
                'confidence': detection_result['confidence'],
                'severity': detection_result['severity'],
                'bbox': detection_result.get('bbox', {})
            }]
            detection.confidence = detection_result['confidence']
            detection.timestamp = datetime.utcnow()
            
            detection.save()
            
            print(f"Detection saved: {detection_result['defect_type']} "
                  f"with confidence {detection_result['confidence']:.2f}")
            
        except Exception as e:
            print(f"Error saving detection: {e}")
    
    def _create_report(self, detection_result):
        """Create a road report from detection"""
        try:
            # Check if similar report already exists nearby
            if detection_result.get('gps'):
                lat = detection_result['gps'].get('latitude')
                lon = detection_result['gps'].get('longitude')
                
                if lat and lon:
                    # Look for existing reports within 50 meters
                    existing_reports = RoadReport.find_nearby(lon, lat, 50)
                    
                    if existing_reports:
                        # Update existing report if found
                        report = existing_reports[0]
                        report.verification_score = min(1.0, report.verification_score + 0.1)
                        report.save()
                        return report
            
            # Create new report
            report = RoadReport()
            
            # Use system user or find admin user
            system_user = User.find_by_email('system@smartroads.com')
            if system_user:
                report.reporter_id = system_user.get_id()
            
            # Set location
            if detection_result.get('gps'):
                report.location = {
                    'type': 'Point',
                    'coordinates': [
                        detection_result['gps'].get('longitude', 0),
                        detection_result['gps'].get('latitude', 0)
                    ]
                }
            
            report.issue_type = detection_result['defect_type']
            report.severity = detection_result['severity']
            report.description = f"Automatically detected by AI camera system. Confidence: {detection_result['confidence']:.2f}"
            report.images = [detection_result.get('image_path', '')]
            report.status = 'pending'
            report.priority = 1 if detection_result['severity'] == 'high' else 2
            report.verification_score = detection_result['confidence']
            
            report.save()
            
            print(f"Report created: {report.issue_type} at {report.location}")
            return report
            
        except Exception as e:
            print(f"Error creating report: {e}")
            return None
    
    def get_live_feed_base64(self):
        """Get current frame as base64 encoded image"""
        snapshot = self.get_snapshot()
        if snapshot is not None:
            # Convert to base64
            _, buffer = cv2.imencode('.jpg', snapshot)
            return base64.b64encode(buffer).decode('utf-8')
        return None

class CameraManager:
    """Manage multiple ESP32 cameras"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cameras = {}
            cls._instance.gps_simulator = GPSSimulator()
        return cls._instance
    
    def register_camera(self, camera_id, ip, port=80):
        """Register a new camera"""
        camera = ESP32Camera(ip, port)
        self.cameras[camera_id] = camera
        return camera
    
    def get_camera(self, camera_id):
        """Get camera by ID"""
        return self.cameras.get(camera_id)
    
    def start_all_cameras(self):
        """Start all registered cameras"""
        for camera_id, camera in self.cameras.items():
            if not camera.is_streaming:
                # Use GPS simulator for development
                camera.start_streaming(
                    gps_callback=self.gps_simulator.get_current_location,
                    detection_callback=self.on_detection
                )
                print(f"Started camera: {camera_id}")
    
    def stop_all_cameras(self):
        """Stop all cameras"""
        for camera_id, camera in self.cameras.items():
            if camera.is_streaming:
                camera.stop_streaming()
                print(f"Stopped camera: {camera_id}")
    
    def on_detection(self, detection_result):
        """Callback when a detection is made"""
        # Broadcast detection via WebSocket
        from websocket_handler import socketio
        socketio.emit('new_detection', {
            'camera_id': detection_result.get('camera_id', 'unknown'),
            'defect_type': detection_result.get('defect_type'),
            'confidence': detection_result.get('confidence'),
            'severity': detection_result.get('severity'),
            'location': detection_result.get('gps'),
            'timestamp': detection_result.get('timestamp'),
            'image_url': detection_result.get('image_path')
        })
        
        # Also emit for map updates
        socketio.emit('map_update', {
            'type': 'new_issue',
            'data': {
                'id': f"ai_{datetime.utcnow().timestamp()}",
                'type': detection_result.get('defect_type'),
                'severity': detection_result.get('severity'),
                'location': detection_result.get('gps'),
                'source': 'ai_camera',
                'timestamp': detection_result.get('timestamp')
            }
        })

class GPSSimulator:
    """Simulate GPS data for development"""
    def __init__(self):
        self.current_lat = 40.7128  # New York
        self.current_lon = -74.0060
        self.speed = 0.0001  # degrees per update
        self.direction = 0  # degrees
    
    def get_current_location(self):
        """Get simulated GPS location"""
        # Simulate movement
        import math
        import random
        
        # Randomly change direction
        if random.random() < 0.1:
            self.direction = random.uniform(0, 360)
        
        # Convert direction to radians
        dir_rad = math.radians(self.direction)
        
        # Calculate new position
        self.current_lat += math.cos(dir_rad) * self.speed * random.uniform(0.5, 1.5)
        self.current_lon += math.sin(dir_rad) * self.speed * random.uniform(0.5, 1.5)
        
        # Add some random noise
        self.current_lat += random.uniform(-0.0001, 0.0001)
        self.current_lon += random.uniform(-0.0001, 0.0001)
        
        return {
            'latitude': self.current_lat,
            'longitude': self.current_lon,
            'accuracy': random.uniform(5, 20),
            'timestamp': datetime.utcnow().isoformat(),
            'speed': random.uniform(0, 60),
            'heading': self.direction
        }

# Global camera manager
camera_manager = CameraManager()