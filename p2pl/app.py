from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import math
from bson import ObjectId
from pymongo import MongoClient, GEOSPHERE
import uuid
import base64
import cv2
import numpy as np
from PIL import Image
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize MongoDB
client = MongoClient(app.config['MONGO_URI'])
db = client[app.config['MONGO_DBNAME']]

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Create indexes
db.users.create_index('email', unique=True)
db.users.create_index('username', unique=True)
db.road_reports.create_index([('location', GEOSPHERE)])
db.road_reports.create_index('status')
db.road_reports.create_index('severity')
db.road_reports.create_index('created_at')

# User class for Flask-Login
class User:
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.password_hash = user_data['password_hash']
        self.full_name = user_data.get('full_name', '')
        self.role = user_data.get('role', 'citizen')
        self.department = user_data.get('department', '')
        self.phone = user_data.get('phone', '')
        self.avatar = user_data.get('avatar', '')
        self.is_active = user_data.get('is_active', True)
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.last_login = user_data.get('last_login')
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return self.is_active
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return self.id
    
    def is_authority(self):
        return self.role in ['authority', 'admin']
    
    def is_admin(self):
        return self.role == 'admin'
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Utility functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Add this function to app.py (after the imports)

def get_indian_city(lat, lon):
    """Get approximate Indian city name from coordinates"""
    # Major Indian cities with coordinates
    indian_cities = [
        ("Delhi", 28.6139, 77.2090),
        ("Mumbai", 19.0760, 72.8777),
        ("Bangalore", 12.9716, 77.5946),
        ("Chennai", 13.0827, 80.2707),
        ("Kolkata", 22.5726, 88.3639),
        ("Hyderabad", 17.3850, 78.4867),
        ("Pune", 18.5204, 73.8567),
        ("Ahmedabad", 23.0225, 72.5714),
        ("Jaipur", 26.9124, 75.7873),
        ("Lucknow", 26.8467, 80.9462),
        ("Surat", 21.1702, 72.8311),
        ("Kanpur", 26.4499, 80.3319),
        ("Nagpur", 21.1458, 79.0882),
        ("Patna", 25.5941, 85.1376),
        ("Indore", 22.7196, 75.8577),
        ("Bhopal", 23.2599, 77.4126),
        ("Ludhiana", 30.9010, 75.8573),
        ("Agra", 27.1767, 78.0081),
        ("Nashik", 19.9975, 73.7898),
        ("Faridabad", 28.4089, 77.3178),
        ("Meerut", 28.9845, 77.7064),
        ("Rajkot", 22.3039, 70.8022),
        ("Varanasi", 25.3176, 82.9739),
        ("Srinagar", 34.0837, 74.7973),
        ("Amritsar", 31.6340, 74.8723),
        ("Ranchi", 23.3441, 85.3096),
        ("Raipur", 21.2514, 81.6296),
        ("Jodhpur", 26.2389, 73.0243),
        ("Kochi", 9.9312, 76.2673),
        ("Guwahati", 26.1445, 91.7362),
        ("Chandigarh", 30.7333, 76.7794),
        ("Thiruvananthapuram", 8.5241, 76.9366),
        ("Bhubaneswar", 20.2961, 85.8245),
        ("Dehradun", 30.3165, 78.0322),
        ("Gangtok", 27.3389, 88.6065),
        ("Shimla", 31.1048, 77.1734),
        ("Panaji", 15.4909, 73.8278),
        ("Port Blair", 11.6234, 92.7265)
    ]
    
    # Find the closest city
    min_distance = float('inf')
    closest_city = "Unknown"
    
    for city, city_lat, city_lon in indian_cities:
        distance = haversine_distance(lat, lon, city_lat, city_lon)
        if distance < min_distance:
            min_distance = distance
            closest_city = city
    
    # Return city name if within 100km, otherwise region
    if min_distance < 100:
        return closest_city
    elif min_distance < 300:
        return f"Near {closest_city}"
    else:
        # Determine region
        if lat > 28: return "Northern India"
        elif lat > 20: return "Central India"
        elif lat > 8: return "Southern India"
        else: return "India"

# Add this context processor to make the function available in templates
@app.context_processor
def utility_processor():
    return dict(get_indian_city=get_indian_city)
def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        upload_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            'reports',
            filename
        )
        
        file.save(upload_path)
        return f"/uploads/reports/{filename}"
    return None

def create_default_users():
    """Create default admin and system users"""
    # Check if admin exists
    admin = db.users.find_one({'email': 'admin@smartroads.com'})
    if not admin:
        admin_data = {
            'username': 'admin',
            'email': 'admin@smartroads.com',
            'password_hash': generate_password_hash('admin123'),
            'full_name': 'System Administrator',
            'role': 'admin',
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        db.users.insert_one(admin_data)
        print("Default admin user created: admin@smartroads.com / admin123")
    
    # Check if system user exists
    system = db.users.find_one({'email': 'system@smartroads.com'})
    if not system:
        system_data = {
            'username': 'system',
            'email': 'system@smartroads.com',
            'password_hash': generate_password_hash('system123'),
            'full_name': 'AI Detection System',
            'role': 'authority',
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        db.users.insert_one(system_data)
        print("System user created for AI detections")

def get_statistics():
    """Get system statistics"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats = {
        'total_reports': db.road_reports.count_documents({}),
        'reports_today': db.road_reports.count_documents({'created_at': {'$gte': today}}),
        'pending_reports': db.road_reports.count_documents({'status': 'pending'}),
        'resolved_today': db.road_reports.count_documents({'status': 'resolved', 'resolved_at': {'$gte': today}}),
        'high_priority': db.road_reports.count_documents({'severity': 'high'}),
        'ai_detections': db.camera_detections.count_documents({'timestamp': {'$gte': today}}) if 'camera_detections' in db.list_collection_names() else 0
    }
    
    return stats

# Geometry utility functions
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2) * math.sin(delta_lat/2) + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon/2) * math.sin(delta_lon/2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def distance_to_line(point_lat, point_lon, line_lat1, line_lon1, line_lat2, line_lon2):
    """Calculate distance from point to line segment"""
    # Convert to radians
    lat1 = math.radians(line_lat1)
    lon1 = math.radians(line_lon1)
    lat2 = math.radians(line_lat2)
    lon2 = math.radians(line_lon2)
    latp = math.radians(point_lat)
    lonp = math.radians(point_lon)
    
    # Calculate using spherical geometry
    # Simplified calculation - in production use proper geodesic distance
    dx = lon2 - lon1
    dy = lat2 - lat1
    
    if dx == 0 and dy == 0:
        return haversine_distance(point_lat, point_lon, line_lat1, line_lon1)
    
    # Project point onto line
    t = ((lonp - lon1) * dx + (latp - lat1) * dy) / (dx*dx + dy*dy)
    t = max(0, min(1, t))
    
    # Find closest point on line
    closest_lon = lon1 + t * dx
    closest_lat = lat1 + t * dy
    
    # Convert back to degrees
    closest_lat_deg = math.degrees(closest_lat)
    closest_lon_deg = math.degrees(closest_lon)
    
    return haversine_distance(point_lat, point_lon, closest_lat_deg, closest_lon_deg)

# Routes
@app.route('/')
def index():
    stats = get_statistics()
    # Get recent reports for the homepage
    recent_reports = list(db.road_reports.find({}).sort('created_at', -1).limit(6))
    for report in recent_reports:
        report['_id'] = str(report['_id'])
    return render_template('index.html', stats=stats, recent_reports=recent_reports, user=current_user)

@app.route('/about')
def about():
    stats = get_statistics()
    return render_template('about.html', stats=stats, user=current_user)

@app.route('/map')
def map_page():
    # Get all reports for the map
    reports = list(db.road_reports.find({}).sort('created_at', -1).limit(100))
    
    # Convert ObjectId to string for JSON serialization
    for report in reports:
        report['_id'] = str(report['_id'])
        if 'reporter_id' in report and report['reporter_id']:
            report['reporter_id'] = str(report['reporter_id'])
        if 'assigned_to' in report and report['assigned_to']:
            report['assigned_to'] = str(report['assigned_to'])
    
    return render_template('map.html', 
                         reports=reports, 
                         user=current_user,
                         current_time=datetime.utcnow())

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        try:
            # Get form data
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            address = request.form.get('address', '')
            issue_type = request.form.get('issue_type')
            severity = request.form.get('severity', 'medium')
            description = request.form.get('description', '')
            
            # Handle file uploads
            images = []
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
                    if file and file.filename:
                        file_url = save_uploaded_file(file)
                        if file_url:
                            images.append(file_url)
            
            # Create report document
            report_data = {
                'reporter_id': ObjectId(current_user.id),
                'location': {
                    'type': 'Point',
                    'coordinates': [float(longitude), float(latitude)]
                } if latitude and longitude else None,
                'address': address,
                'issue_type': issue_type,
                'severity': severity,
                'description': description,
                'images': images,
                'status': 'pending',
                'priority': 1 if severity == 'high' else 2,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert into database
            result = db.road_reports.insert_one(report_data)
            
            flash('Report submitted successfully!', 'success')
            return redirect(url_for('report'))
            
        except Exception as e:
            flash(f'Error submitting report: {str(e)}', 'danger')
            return redirect(url_for('report'))
    
    return render_template('report.html', user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_authority():
        flash('You need authority access to view the dashboard.', 'warning')
        return redirect(url_for('index'))
    
    # Get dashboard data
    reports = list(db.road_reports.find({}).sort('created_at', -1).limit(50))
    stats = get_statistics()
    
    # Get maintenance teams
    teams = list(db.maintenance_teams.find({})) if 'maintenance_teams' in db.list_collection_names() else []
    
    # Get recent detections
    detections = list(db.camera_detections.find({}).sort('timestamp', -1).limit(5)) if 'camera_detections' in db.list_collection_names() else []
    
    # Convert ObjectId to string
    for report in reports:
        report['_id'] = str(report['_id'])
    
    for team in teams:
        team['_id'] = str(team['_id'])
    
    for detection in detections:
        detection['_id'] = str(detection['_id'])
    
    return render_template('dashboard.html', 
                         reports=reports, 
                         stats=stats, 
                         teams=teams,
                         detections=detections,
                         user=current_user)

@app.route('/camera_live')
@login_required
def camera_live():
    if not current_user.is_authority():
        flash('You need authority access to view camera feeds.', 'warning')
        return redirect(url_for('index'))
    
    # Get registered cameras
    cameras = list(db.cameras.find({})) if 'cameras' in db.list_collection_names() else []
    
    # Get recent detections
    detections = list(db.camera_detections.find({}).sort('timestamp', -1).limit(10)) if 'camera_detections' in db.list_collection_names() else []
    
    return render_template('camera_live.html', 
                         cameras=cameras,
                         detections=detections,
                         user=current_user)

@app.route('/contact')
def contact():
    return render_template('contact.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard' if current_user.is_authority() else 'index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user_data = db.users.find_one({'email': email})
        
        if user_data:
            user = User(user_data)
            if user.check_password(password) and user.is_active:
                login_user(user, remember=remember)
                
                # Update last login
                db.users.update_one(
                    {'_id': ObjectId(user.id)},
                    {'$set': {'last_login': datetime.utcnow()}}
                )
                
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard' if user.is_authority() else 'index'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html', user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name', '')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif db.users.find_one({'email': email}):
            flash('Email already registered', 'danger')
        elif db.users.find_one({'username': username}):
            flash('Username already taken', 'danger')
        else:
            # Create new user
            user_data = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                'full_name': full_name,
                'role': 'citizen',
                'created_at': datetime.utcnow(),
                'is_active': True
            }
            
            db.users.insert_one(user_data)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/report/<report_id>')
@login_required
def view_report(report_id):
    try:
        report = db.road_reports.find_one({'_id': ObjectId(report_id)})
        if not report:
            flash('Report not found', 'danger')
            return redirect(url_for('dashboard'))
        
        report['_id'] = str(report['_id'])
        
        # Get reporter info
        if 'reporter_id' in report and report['reporter_id']:
            reporter = db.users.find_one({'_id': ObjectId(report['reporter_id'])})
            report['reporter'] = reporter
        
        return render_template('view_report.html', report=report, user=current_user)
    except:
        flash('Invalid report ID', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/report/<report_id>/update', methods=['POST'])
@login_required
def update_report(report_id):
    if not current_user.is_authority():
        flash('You need authority access to update reports.', 'warning')
        return redirect(url_for('index'))
    
    try:
        status = request.form.get('status')
        assigned_to = request.form.get('assigned_to')
        resolution_notes = request.form.get('resolution_notes', '')
        
        update_data = {'updated_at': datetime.utcnow()}
        
        if status:
            update_data['status'] = status
            if status == 'resolved':
                update_data['resolved_at'] = datetime.utcnow()
                update_data['resolution_notes'] = resolution_notes
        
        if assigned_to:
            update_data['assigned_to'] = ObjectId(assigned_to)
            update_data['assigned_at'] = datetime.utcnow()
            if 'status' not in update_data:
                update_data['status'] = 'assigned'
        
        db.road_reports.update_one(
            {'_id': ObjectId(report_id)},
            {'$set': update_data}
        )
        
        flash('Report updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating report: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/detect', methods=['POST'])
@login_required
def detect_defects():
    if not current_user.is_authority():
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    try:
        # Read image
        image = Image.open(file)
        image_np = np.array(image)
        
        # Mock detection (replace with actual AI model)
        # For now, simulate detection
        import random
        
        if random.random() < 0.3:  # 30% chance of detection
            defect_types = ['pothole', 'crack', 'speed_hump', 'debris']
            defect_type = random.choice(defect_types)
            confidence = random.uniform(0.7, 0.95)
            
            height, width = image_np.shape[:2]
            bbox = {
                'x': int(width * random.uniform(0.1, 0.7)),
                'y': int(height * random.uniform(0.1, 0.7)),
                'width': int(width * random.uniform(0.2, 0.4)),
                'height': int(height * random.uniform(0.2, 0.4))
            }
            
            # Draw bounding box
            annotated = image_np.copy()
            cv2.rectangle(annotated, 
                         (bbox['x'], bbox['y']), 
                         (bbox['x'] + bbox['width'], bbox['y'] + bbox['height']), 
                         (0, 255, 0), 3)
            
            # Save annotated image
            detection_id = f"detection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            filename = f"{detection_id}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'detections', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            cv2.imwrite(filepath, cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
            
            # Save detection record
            detection_data = {
                'camera_id': request.form.get('camera_id', 'unknown'),
                'image_url': f"/uploads/detections/{filename}",
                'detections': [{
                    'type': defect_type,
                    'confidence': confidence,
                    'bbox': bbox
                }],
                'confidence': confidence,
                'processed': True,
                'timestamp': datetime.utcnow()
            }
            
            if 'camera_detections' not in db.list_collection_names():
                db.create_collection('camera_detections')
            
            db.camera_detections.insert_one(detection_data)
            
            return jsonify({
                'detected': True,
                'defect_type': defect_type,
                'confidence': confidence,
                'bbox': bbox,
                'image_url': f"/uploads/detections/{filename}"
            })
        else:
            return jsonify({
                'detected': False,
                'message': 'No defects detected'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/nearby')
def get_nearby_reports():
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        distance = int(request.args.get('distance', 5000))
        
        query = {
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [lon, lat]
                    },
                    '$maxDistance': distance
                }
            }
        }
        
        reports = list(db.road_reports.find(query).limit(50))
        
        # Convert ObjectId to string
        for report in reports:
            report['_id'] = str(report['_id'])
        
        return jsonify({'reports': reports})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/route_damages')
def get_route_damages():
    """Get damages along a route"""
    try:
        start_lat = float(request.args.get('start_lat', 0))
        start_lon = float(request.args.get('start_lon', 0))
        end_lat = float(request.args.get('end_lat', 0))
        end_lon = float(request.args.get('end_lon', 0))
        max_distance = float(request.args.get('distance', 0.5))  # 0.5km default
        
        # Calculate route line
        route_length = haversine_distance(start_lat, start_lon, end_lat, end_lon)
        
        # Find damages near route
        damages = []
        all_reports = list(db.road_reports.find({}))
        
        for report in all_reports:
            if 'location' in report and report['location']:
                dam_lat = report['location']['coordinates'][1]
                dam_lon = report['location']['coordinates'][0]
                
                # Calculate distance from damage to route line
                distance = distance_to_line(
                    dam_lat, dam_lon,
                    start_lat, start_lon,
                    end_lat, end_lon
                )
                
                if distance <= max_distance:
                    report['_id'] = str(report['_id'])
                    if 'reporter_id' in report:
                        report['reporter_id'] = str(report['reporter_id'])
                    report['distance_to_route'] = distance
                    damages.append(report)
        
        return jsonify({
            'success': True,
            'damages': damages,
            'route_length': route_length,
            'damage_count': len(damages)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# Update the add_sample_data function in app.py
@app.route('/api/add_sample_data')
def add_sample_data():
    """Add sample road damage data for India testing"""
    try:
        # Clear existing data
        db.road_reports.delete_many({})
        
        # Sample coordinates in India
        sample_damages = [
            {
                'reporter_id': ObjectId(),
                'location': {'type': 'Point', 'coordinates': [77.2090, 28.6139]},
                'address': 'Connaught Place, New Delhi',
                'issue_type': 'pothole',
                'severity': 'high',
                'description': 'Large pothole in main road, causing traffic congestion',
                'images': [],
                'status': 'pending',
                'priority': 1,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'reporter_id': ObjectId(),
                'location': {'type': 'Point', 'coordinates': [72.8777, 19.0760]},
                'address': 'Marine Drive, Mumbai',
                'issue_type': 'crack',
                'severity': 'medium',
                'description': 'Long crack along sea-facing road',
                'images': [],
                'status': 'assigned',
                'priority': 2,
                'created_at': datetime.utcnow() - timedelta(days=1),
                'updated_at': datetime.utcnow()
            },
            {
                'reporter_id': ObjectId(),
                'location': {'type': 'Point', 'coordinates': [77.5946, 12.9716]},
                'address': 'MG Road, Bangalore',
                'issue_type': 'speed_hump',
                'severity': 'low',
                'description': 'Unmarked speed hump near shopping area',
                'images': [],
                'status': 'in_progress',
                'priority': 2,
                'created_at': datetime.utcnow() - timedelta(days=2),
                'updated_at': datetime.utcnow()
            },
            {
                'reporter_id': ObjectId(),
                'location': {'type': 'Point', 'coordinates': [88.3639, 22.5726]},
                'address': 'Park Street, Kolkata',
                'issue_type': 'debris',
                'severity': 'high',
                'description': 'Construction debris blocking traffic during rush hour',
                'images': [],
                'status': 'pending',
                'priority': 1,
                'created_at': datetime.utcnow() - timedelta(hours=3),
                'updated_at': datetime.utcnow()
            },
            {
                'reporter_id': ObjectId(),
                'location': {'type': 'Point', 'coordinates': [78.4867, 17.3850]},
                'address': 'Charminar Road, Hyderabad',
                'issue_type': 'pothole',
                'severity': 'medium',
                'description': 'Medium sized pothole near historical monument',
                'images': [],
                'status': 'resolved',
                'resolved_at': datetime.utcnow() - timedelta(hours=1),
                'resolution_notes': 'Filled with asphalt mixture',
                'priority': 2,
                'created_at': datetime.utcnow() - timedelta(days=3),
                'updated_at': datetime.utcnow() - timedelta(hours=1)
            }
        ]
        
        # Insert sample data
        result = db.road_reports.insert_many(sample_damages)
        
        return jsonify({
            'success': True,
            'message': f'Added {len(result.inserted_ids)} sample damage reports for India',
            'inserted_ids': [str(id) for id in result.inserted_ids]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        create_default_users()
    
    print("Starting Smart Road Monitor System...")
    print(f"Server running at http://localhost:5000")
    print("\nDefault Users:")
    print("  Admin: admin@smartroads.com / admin123")
    print("  System: system@smartroads.com / system123")
    print("\nTo add sample data, visit: http://localhost:5000/api/add_sample_data")
    app.run(host='0.0.0.0', port=5000, debug=True)