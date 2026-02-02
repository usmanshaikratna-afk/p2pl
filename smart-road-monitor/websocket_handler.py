from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, session, current_app
from flask_login import current_user
import eventlet
import json
from datetime import datetime
from models import RoadReport, CameraDetection
from auth import api_token_required

socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')

# Store connected clients
connected_clients = {}

@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.utcnow(),
        'user_id': None,
        'rooms': []
    }
    print(f"Client connected: {client_id}")
    emit('connection_success', {'message': 'Connected to Smart Road Monitor'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    print(f"Client disconnected: {client_id}")

@socketio.on('authenticate')
def handle_authentication(data):
    """Authenticate WebSocket connection"""
    client_id = request.sid
    token = data.get('token')
    
    from auth import verify_token
    user, error = verify_token(token)
    
    if user and not error:
        connected_clients[client_id]['user_id'] = user.get_id()
        connected_clients[client_id]['user_role'] = user.role
        emit('auth_success', {
            'message': 'Authenticated successfully',
            'user': {
                'id': user.get_id(),
                'username': user.username,
                'role': user.role
            }
        })
    else:
        emit('auth_error', {'error': error or 'Authentication failed'})

@socketio.on('join_room')
def handle_join_room(data):
    """Join a specific room (e.g., map_updates, camera_feed)"""
    room = data.get('room')
    client_id = request.sid
    
    if room:
        join_room(room)
        connected_clients[client_id]['rooms'].append(room)
        emit('room_joined', {'room': room, 'client_id': client_id})

@socketio.on('leave_room')
def handle_leave_room(data):
    """Leave a room"""
    room = data.get('room')
    client_id = request.sid
    
    if room and room in connected_clients[client_id]['rooms']:
        leave_room(room)
        connected_clients[client_id]['rooms'].remove(room)
        emit('room_left', {'room': room})

@socketio.on('subscribe_map')
def handle_subscribe_map(data):
    """Subscribe to map updates for a specific area"""
    client_id = request.sid
    bounds = data.get('bounds')  # {north, south, east, west}
    
    if bounds:
        # Create a room name based on map bounds
        room_name = f"map_{bounds['north']:.4f}_{bounds['south']:.4f}_{bounds['east']:.4f}_{bounds['west']:.4f}"
        join_room(room_name)
        connected_clients[client_id]['rooms'].append(room_name)
        
        # Send current reports in the area
        from models import RoadReport
        reports = RoadReport.find_nearby(
            (bounds['east'] + bounds['west']) / 2,
            (bounds['north'] + bounds['south']) / 2,
            max_distance=5000
        )
        
        emit('initial_map_data', {
            'reports': [report.to_json() for report in reports]
        })

@socketio.on('report_update')
def handle_report_update(data):
    """Handle report status updates"""
    report_id = data.get('report_id')
    status = data.get('status')
    notes = data.get('notes')
    
    from models import RoadReport
    report = RoadReport.find_by_id(report_id)
    
    if report and status:
        old_status = report.status
        report.status = status
        
        if status == 'resolved':
            report.resolution_notes = notes
            report.resolved_at = datetime.utcnow()
        
        report.save()
        
        # Broadcast update to all clients
        emit('report_status_changed', {
            'report_id': report_id,
            'old_status': old_status,
            'new_status': status,
            'updated_at': datetime.utcnow().isoformat()
        }, broadcast=True)
        
        # Update map in real-time
        emit('map_update', {
            'type': 'report_updated',
            'data': report.to_json()
        }, broadcast=True)

@socketio.on('new_report')
def handle_new_report(data):
    """Handle new report submission"""
    from models import RoadReport, User
    from flask_login import current_user
    
    report = RoadReport()
    report.reporter_id = current_user.get_id() if current_user.is_authenticated else None
    report.location = data.get('location')
    report.address = data.get('address')
    report.issue_type = data.get('issue_type')
    report.severity = data.get('severity')
    report.description = data.get('description')
    report.images = data.get('images', [])
    report.status = 'pending'
    report.priority = 1 if data.get('severity') == 'high' else 2
    
    report_id = report.save()
    
    # Broadcast to all connected clients
    emit('new_report_added', {
        'report': report.to_json(),
        'message': 'New road issue reported'
    }, broadcast=True)
    
    # Notify authorities via their room
    emit('authority_notification', {
        'type': 'new_report',
        'data': report.to_json(),
        'message': 'New high priority report requires attention'
    }, room='authority_room')

@socketio.on('camera_stream_request')
def handle_camera_stream(data):
    """Handle camera stream requests"""
    camera_id = data.get('camera_id')
    action = data.get('action')  # start, stop, snapshot
    
    from camera_integration import camera_manager
    camera = camera_manager.get_camera(camera_id)
    
    if camera:
        if action == 'start':
            camera.start_streaming()
            emit('camera_stream_started', {'camera_id': camera_id})
        elif action == 'stop':
            camera.stop_streaming()
            emit('camera_stream_stopped', {'camera_id': camera_id})
        elif action == 'snapshot':
            snapshot = camera.get_snapshot()
            if snapshot:
                # Convert to base64 for WebSocket transmission
                import cv2
                import base64
                _, buffer = cv2.imencode('.jpg', snapshot)
                base64_image = base64.b64encode(buffer).decode('utf-8')
                emit('camera_snapshot', {
                    'camera_id': camera_id,
                    'image': base64_image,
                    'timestamp': datetime.utcnow().isoformat()
                })

def broadcast_detection(detection_data):
    """Broadcast AI detection to connected clients"""
    socketio.emit('ai_detection', {
        'camera_id': detection_data.get('camera_id'),
        'defect_type': detection_data.get('defect_type'),
        'confidence': detection_data.get('confidence'),
        'severity': detection_data.get('severity'),
        'location': detection_data.get('gps'),
        'timestamp': detection_data.get('timestamp'),
        'image_url': detection_data.get('image_path')
    }, broadcast=True)

def broadcast_map_update(update_type, data):
    """Broadcast map updates"""
    socketio.emit('map_update', {
        'type': update_type,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }, broadcast=True)

def send_notification(user_id, notification):
    """Send notification to specific user"""
    for client_id, client_data in connected_clients.items():
        if client_data.get('user_id') == user_id:
            emit('notification', notification, room=client_id)
            break

# Background task for periodic updates
def background_updates():
    """Send periodic updates to connected clients"""
    import time
    while True:
        try:
            # Update live statistics
            from models import Statistics
            stats = Statistics.update_daily_stats()
            
            # Broadcast statistics
            socketio.emit('live_statistics', {
                'total_reports': stats.get('total_reports', 0),
                'pending_reports': stats.get('pending_reports', 0),
                'resolved_today': stats.get('resolved_reports', 0),
                'ai_detections': stats.get('ai_detections', 0),
                'updated_at': datetime.utcnow().isoformat()
            })
            
            # Check for new camera detections
            from models import CameraDetection
            recent_detections = CameraDetection.get_recent(limit=5)
            if recent_detections:
                socketio.emit('recent_detections', {
                    'detections': [
                        {
                            'type': det.detections[0]['type'] if det.detections else 'unknown',
                            'confidence': det.confidence,
                            'timestamp': det.timestamp.isoformat() if det.timestamp else None,
                            'location': det.location
                        }
                        for det in recent_detections
                    ]
                })
            
        except Exception as e:
            print(f"Background update error: {e}")
        
        # Sleep for 30 seconds
        time.sleep(30)

# Start background thread
eventlet.spawn(background_updates)