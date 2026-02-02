import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
from PIL import Image
import io
import base64
from datetime import datetime
import os
from config import Config

class RoadDefectDetector:
    def __init__(self):
        self.model = None
        self.classes = Config.MODEL_CLASSES
        self.confidence_threshold = Config.CONFIDENCE_THRESHOLD
        self.load_model()
    
    def load_model(self):
        """Load the trained AI model"""
        try:
            if os.path.exists(Config.MODEL_PATH):
                self.model = keras.models.load_model(Config.MODEL_PATH)
                print(f"AI Model loaded from {Config.MODEL_PATH}")
            else:
                print("No pre-trained model found. Using mock predictions.")
                self.model = None
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def preprocess_image(self, image):
        """Preprocess image for model input"""
        # Convert to RGB if needed
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize to model input size
        image = cv2.resize(image, (224, 224))
        
        # Normalize
        image = image.astype(np.float32) / 255.0
        
        # Add batch dimension
        image = np.expand_dims(image, axis=0)
        
        return image
    
    def detect_defects(self, image, gps_data=None):
        """
        Detect road defects in image
        
        Args:
            image: numpy array or PIL Image
            gps_data: dict with 'latitude' and 'longitude'
        
        Returns:
            dict with detection results
        """
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # Store original image for visualization
        original_image = image.copy()
        
        if self.model is None:
            # Mock detection for development
            return self.mock_detection(original_image, gps_data)
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Make prediction
            predictions = self.model.predict(processed_image, verbose=0)[0]
            
            # Get top prediction
            class_idx = np.argmax(predictions)
            confidence = float(predictions[class_idx])
            defect_type = self.classes[class_idx]
            
            if confidence < self.confidence_threshold:
                return {
                    'detected': False,
                    'confidence': confidence,
                    'type': defect_type,
                    'message': 'No significant defects detected',
                    'timestamp': datetime.utcnow().isoformat(),
                    'gps': gps_data
                }
            
            # Create bounding box (mock, replace with actual detection)
            height, width = original_image.shape[:2]
            bbox = {
                'x': int(width * 0.2),
                'y': int(height * 0.2),
                'width': int(width * 0.6),
                'height': int(height * 0.6),
                'confidence': confidence
            }
            
            # Calculate severity based on type and confidence
            severity = self.calculate_severity(defect_type, confidence, bbox)
            
            # Create annotated image
            annotated_image = self.annotate_image(original_image, bbox, defect_type, confidence)
            
            # Save detection image
            detection_id = f"detection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            image_path = self.save_detection_image(annotated_image, detection_id)
            
            return {
                'detected': True,
                'defect_type': defect_type,
                'confidence': confidence,
                'severity': severity,
                'bbox': bbox,
                'image_path': image_path,
                'original_size': {'width': width, 'height': height},
                'timestamp': datetime.utcnow().isoformat(),
                'gps': gps_data,
                'detection_id': detection_id
            }
            
        except Exception as e:
            print(f"Error during detection: {e}")
            return {
                'detected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'gps': gps_data
            }
    
    def mock_detection(self, image, gps_data=None):
        """Mock detection for development when no model is available"""
        import random
        
        height, width = image.shape[:2]
        
        # Simulate random detection (30% chance)
        if random.random() < 0.3:
            defect_types = ['pothole', 'crack', 'speed_hump', 'debris']
            defect_type = random.choice(defect_types)
            confidence = random.uniform(0.7, 0.95)
            
            bbox = {
                'x': int(width * random.uniform(0.1, 0.7)),
                'y': int(height * random.uniform(0.1, 0.7)),
                'width': int(width * random.uniform(0.2, 0.4)),
                'height': int(height * random.uniform(0.2, 0.4)),
                'confidence': confidence
            }
            
            severity = self.calculate_severity(defect_type, confidence, bbox)
            
            # Annotate image
            annotated_image = self.annotate_image(image, bbox, defect_type, confidence)
            
            # Save image
            detection_id = f"mock_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            image_path = self.save_detection_image(annotated_image, detection_id)
            
            return {
                'detected': True,
                'defect_type': defect_type,
                'confidence': confidence,
                'severity': severity,
                'bbox': bbox,
                'image_path': image_path,
                'original_size': {'width': width, 'height': height},
                'timestamp': datetime.utcnow().isoformat(),
                'gps': gps_data,
                'detection_id': detection_id,
                'note': 'Mock detection - for development only'
            }
        else:
            return {
                'detected': False,
                'confidence': 0.1,
                'type': 'normal_road',
                'message': 'No defects detected',
                'timestamp': datetime.utcnow().isoformat(),
                'gps': gps_data,
                'note': 'Mock detection - for development only'
            }
    
    def calculate_severity(self, defect_type, confidence, bbox):
        """Calculate severity based on defect type, confidence, and size"""
        # Base severity by defect type
        severity_map = {
            'pothole': 'high',
            'speed_hump': 'medium',
            'crack': 'medium',
            'debris': 'low',
            'flooding': 'high',
            'normal_road': 'low'
        }
        
        base_severity = severity_map.get(defect_type, 'low')
        
        # Adjust based on confidence
        if confidence > 0.9:
            if base_severity == 'medium':
                base_severity = 'high'
        elif confidence < 0.5:
            if base_severity == 'high':
                base_severity = 'medium'
        
        # Adjust based on size (bbox area)
        area = bbox['width'] * bbox['height']
        if area > 10000:  # Large defect
            if base_severity == 'medium':
                base_severity = 'high'
        
        return base_severity
    
    def annotate_image(self, image, bbox, defect_type, confidence):
        """Draw bounding box and label on image"""
        annotated = image.copy()
        
        # Draw bounding box
        color_map = {
            'pothole': (0, 0, 255),      # Red
            'crack': (0, 165, 255),      # Orange
            'speed_hump': (255, 255, 0), # Cyan
            'debris': (0, 255, 0),       # Green
            'flooding': (255, 0, 255),   # Magenta
            'normal_road': (128, 128, 128) # Gray
        }
        
        color = color_map.get(defect_type, (255, 255, 255))
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        
        # Draw rectangle
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 3)
        
        # Draw label background
        label = f"{defect_type}: {confidence:.2f}"
        (label_width, label_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
        )
        
        cv2.rectangle(
            annotated,
            (x, y - label_height - 10),
            (x + label_width, y),
            color,
            -1
        )
        
        # Draw label text
        cv2.putText(
            annotated,
            label,
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        # Add timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(
            annotated,
            timestamp,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )
        
        return annotated
    
    def save_detection_image(self, image, detection_id):
        """Save detection image to disk"""
        from config import Config
        import os
        
        # Create directory if it doesn't exist
        detections_dir = os.path.join(Config.UPLOAD_FOLDER, 'detections')
        os.makedirs(detections_dir, exist_ok=True)
        
        # Save image
        filename = f"{detection_id}.jpg"
        filepath = os.path.join(detections_dir, filename)
        cv2.imwrite(filepath, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        
        # Return relative path
        return f"/uploads/detections/{filename}"
    
    def process_video_frame(self, frame, frame_count, gps_data=None):
        """Process a single video frame"""
        # Only process every 10th frame for performance
        if frame_count % 10 != 0:
            return None
        
        return self.detect_defects(frame, gps_data)
    
    def image_to_base64(self, image):
        """Convert image to base64 string"""
        success, buffer = cv2.imencode('.jpg', image)
        if success:
            return base64.b64encode(buffer).decode('utf-8')
        return None

# Global detector instance
detector = RoadDefectDetector()