from flask import render_template, request, jsonify, redirect, url_for, flash, send_file, session
from flask_login import login_user, logout_user, login_required, current_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import json

from models import User, RoadReport, CameraDetection, MaintenanceTeam, Statistics
from auth import create_user, authenticate_user, authority_required, admin_required, api_token_required
from camera_integration import camera_manager
from ai_detection import detector
from websocket_handler import socketio, broadcast_map_update

def register_routes(app):
    """Register all routes with the Flask app"""
    
    # Home page
    @app.route('/')
    def index():
        stats = Statistics.update_daily_stats()
        return render_template('index.html', stats=stats, user=current_user)
    
    # About page
    @app.route('/about')
    def about():
        return render_template('about.html', user=current_user)
    
    # Map page
    @app.route('/map')
    def map_page():
        return render_template('map.html', user=current_user)
    
    # Report page
    @app.route('/report', methods=['GET', 'POST'])
    def report():
        if request.method == 'POST':
            return handle_report_submission()
        return render_template('report.html', user=current_user)
    
    # Dashboard
    @app.route('/dashboard')
    @login_required
    def dashboard():
        if not current_user.is_authority():
            flash('You need authority access to view the dashboard.', 'warning')
            return redirect(url_for('index'))
        
        # Get dashboard data
        reports = RoadReport.get_all(per_page=50)
        stats = Statistics.update_daily_stats()
        teams = MaintenanceTeam.find_all()
        
        return render_template('dashboard.html', 
                             user=current_user,
                             reports=reports,
                             stats=stats,
                             teams=teams)
    
    # Live camera page
    @app.route('/camera_live')
    @authority_required
    def camera_live():
        cameras = list(camera_manager.cameras.keys())
        return render_template('camera_live.html', 
                             user=current_user,
                             cameras=cameras)
    
    # Contact page
    @app.route('/contact')
    def contact():
        return render_template('contact.html', user=current_user)
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard' if current_user.is_authority() else 'index'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = request.form.get('remember', False)
            
            user, error = authenticate_user(email, password)
            if user and not error:
                login_user(user, remember=remember)
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard' if user.is_authority() else 'index'))
            else:
                flash(error or 'Invalid credentials', 'danger')
        
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
            full_name = request.form.get('full_name')
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
            else:
                user, error = create_user(username, email, password, full_name)
                if user and not error:
                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash(error or 'Registration failed', 'danger')
        
        return render_template('register.html', user=current_user)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully', 'info')
        return redirect(url_for('index'))
    
    # API Routes
    @app.route('/api/reports', methods=['GET'])
    def get_reports():
        """Get reports with filters"""
        filters = {}
        
        # Parse filter parameters
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('severity'):
            filters['severity'] = request.args.get('severity')
        if request.args.get('type'):
            filters['issue_type'] = request.args.get('type')
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        result = RoadReport.get_all(filters, page, per_page)
        
        return jsonify({
            'success': True,
            'reports': [report.to_json() for report in result['reports']],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'pages': result['pages']
            }
        })
    
    @app.route('/api/reports/nearby', methods=['GET'])
    def get_nearby_reports():
        """Get reports near a location"""
        try:
            lat = float(request.args.get('lat', 0))
            lon = float(request.args.get('lon', 0))
            distance = int(request.args.get('distance', 5000))  # meters
            
            reports = RoadReport.find_nearby(lon, lat, distance)
            
            return jsonify({
                'success': True,
                'reports': [report.to_json() for report in reports],
                'count': len(reports)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/reports', methods=['POST'])
    @api_token_required
    def create_report_api():
        """Create a new report via API"""
        try:
            data = request.get_json()
            
            report = RoadReport()
            report.reporter_id = request.user.get_id()
            report.location = data.get('location')
            report.address = data.get('address', '')
            report.issue_type = data.get('issue_type')
            report.severity = data.get('severity', 'medium')
            report.description = data.get('description', '')
            report.images = data.get('images', [])
            report.status = 'pending'
            report.priority = 1 if data.get('severity') == 'high' else 2
            
            report_id = report.save()
            
            # Broadcast via WebSocket
            broadcast_map_update('new_report', report.to_json())
            
            return jsonify({
                'success': True,
                'report_id': str(report_id),
                'message': 'Report created successfully'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/reports/<report_id>', methods=['PUT'])
    @api_token_required
    def update_report_api(report_id):
        """Update a report"""
        try:
            report = RoadReport.find_by_id(report_id)
            if not report:
                return jsonify({'success': False, 'error': 'Report not found'}), 404
            
            data = request.get_json()
            
            # Update allowed fields
            if 'status' in data:
                report.status = data['status']
                if data['status'] == 'resolved':
                    report.resolved_at = datetime.utcnow()
                    report.resolution_notes = data.get('resolution_notes', '')
            
            if 'assigned_to' in data:
                report.assigned_to = data['assigned_to']
                report.assigned_at = datetime.utcnow()
                report.status = 'assigned'
            
            if 'priority' in data:
                report.priority = data['priority']
            
            report.save()
            
            # Broadcast update
            broadcast_map_update('report_updated', report.to_json())
            
            return jsonify({
                'success': True,
                'message': 'Report updated successfully',
                'report': report.to_json()
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/camera/register', methods=['POST'])
    @api_token_required
    def register_camera():
        """Register an ESP32 camera"""
        try:
            data = request.get_json()
            camera_id = data.get('camera_id')
            ip = data.get('ip')
            port = data.get('port', 80)
            
            camera = camera_manager.register_camera(camera_id, ip, port)
            
            return jsonify({
                'success': True,
                'camera_id': camera_id,
                'stream_url': camera.stream_url,
                'message': 'Camera registered successfully'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/camera/<camera_id>/stream', methods=['POST'])
    @api_token_required
    def start_camera_stream(camera_id):
        """Start camera stream"""
        try:
            camera = camera_manager.get_camera(camera_id)
            if not camera:
                return jsonify({'success': False, 'error': 'Camera not found'}), 404
            
            data = request.get_json()
            gps_data = data.get('gps')
            
            if camera.start_streaming(gps_data=gps_data):
                return jsonify({
                    'success': True,
                    'message': 'Camera stream started'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Camera already streaming'
                })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/camera/<camera_id>/snapshot', methods=['GET'])
    def get_camera_snapshot(camera_id):
        """Get camera snapshot"""
        try:
            camera = camera_manager.get_camera(camera_id)
            if not camera:
                return jsonify({'success': False, 'error': 'Camera not found'}), 404
            
            snapshot = camera.get_snapshot()
            if snapshot is None:
                return jsonify({'success': False, 'error': 'Failed to capture snapshot'}), 500
            
            # Convert to base64
            import cv2
            import base64
            _, buffer = cv2.imencode('.jpg', snapshot)
            base64_image = base64.b64encode(buffer).decode('utf-8')
            
            return jsonify({
                'success': True,
                'image': base64_image,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/detect', methods=['POST'])
    def detect_defects():
        """Detect defects in uploaded image"""
        try:
            if 'image' not in request.files:
                return jsonify({'success': False, 'error': 'No image provided'}), 400
            
            image_file = request.files['image']
            gps_data = request.form.get('gps')
            
            if gps_data:
                gps_data = json.loads(gps_data)
            
            # Read image
            import cv2
            import numpy as np
            from PIL import Image
            
            image = Image.open(image_file)
            image_np = np.array(image)
            
            # Detect defects
            result = detector.detect_defects(image_np, gps_data)
            
            return jsonify({
                'success': True,
                'detection': result
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/api/statistics', methods=['GET'])
    def get_statistics():
        """Get system statistics"""
        stats = Statistics.update_daily_stats()
        
        # Calculate additional stats
        total_reports = RoadReport.count_documents({})
        reports_today = RoadReport.count_documents({
            'created_at': {'$gte': datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
        })
        
        return jsonify({
            'success': True,
            'stats': {
                'total_reports': total_reports,
                'reports_today': reports_today,
                'pending_reports': stats.get('pending_reports', 0),
                'resolved_today': stats.get('resolved_reports', 0),
                'high_priority': stats.get('high_priority', 0),
                'ai_detections': stats.get('ai_detections', 0),
                'response_rate': self.calculate_response_rate(),
                'average_resolution_time': self.calculate_avg_resolution_time()
            }
        })
    
    @app.route('/api/upload', methods=['POST'])
    @api_token_required
    def upload_file():
        """Upload file (images for reports)"""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            if file and self.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid collisions
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                upload_path = os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    'reports',
                    filename
                )
                
                file.save(upload_path)
                
                # Return relative URL
                file_url = f"/uploads/reports/{filename}"
                
                return jsonify({
                    'success': True,
                    'file_url': file_url,
                    'filename': filename
                })
            else:
                return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files"""
        return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    # Helper methods
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    def calculate_response_rate():
        """Calculate average response rate"""
        # This would calculate based on historical data
        return 0.85  # Placeholder
    
    def calculate_avg_resolution_time():
        """Calculate average resolution time in hours"""
        # This would calculate based on resolved reports
        return 24  # Placeholder
    
    def handle_report_submission():
        """Handle report form submission"""
        try:
            # Get form data
            location = request.form.get('location')
            issue_type = request.form.get('issue_type')
            severity = request.form.get('severity')
            description = request.form.get('description')
            address = request.form.get('address', '')
            
            # Handle file uploads
            images = []
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
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
                        images.append(f"/uploads/reports/{filename}")
            
            # Parse location (expecting JSON string)
            try:
                location_data = json.loads(location) if location else None
            except:
                location_data = None
            
            # Create report
            report = RoadReport()
            if current_user.is_authenticated:
                report.reporter_id = current_user.get_id()
            
            if location_data:
                report.location = {
                    'type': 'Point',
                    'coordinates': [
                        location_data.get('longitude', 0),
                        location_data.get('latitude', 0)
                    ]
                }
            
            report.address = address
            report.issue_type = issue_type
            report.severity = severity
            report.description = description
            report.images = images
            report.status = 'pending'
            report.priority = 1 if severity == 'high' else 2
            
            report.save()
            
            flash('Report submitted successfully!', 'success')
            return redirect(url_for('report'))
            
        except Exception as e:
            app.logger.error(f"Error submitting report: {e}")
            flash('Error submitting report. Please try again.', 'danger')
            return redirect(url_for('report'))