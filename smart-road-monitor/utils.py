import os
import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import hashlib

def generate_id():
    """Generate a unique ID"""
    return str(uuid.uuid4())

def validate_email(email):
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    return True, "Password is valid"

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in meters"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def format_date(date_obj, format_str='%Y-%m-%d %H:%M:%S'):
    """Format datetime object to string"""
    if not date_obj:
        return ''
    return date_obj.strftime(format_str)

def parse_date(date_str, format_str='%Y-%m-%d %H:%M:%S'):
    """Parse string to datetime object"""
    try:
        return datetime.strptime(date_str, format_str)
    except:
        return None

def get_file_hash(file_path):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def create_thumbnail(image_path, size=(200, 200)):
    """Create thumbnail for image"""
    from PIL import Image
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size)
            thumb_path = os.path.splitext(image_path)[0] + '_thumb.jpg'
            img.save(thumb_path, 'JPEG')
            return thumb_path
    except Exception as e:
        print(f"Error creating thumbnail: {e}")
        return None

def rate_limit(limit=100, per=60):
    """Rate limiting decorator"""
    from collections import defaultdict
    from time import time
    
    calls = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = time()
            client_ip = request.remote_addr
            
            # Clean old calls
            calls[client_ip] = [call for call in calls[client_ip] if call > now - per]
            
            if len(calls[client_ip]) >= limit:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': per - (now - calls[client_ip][0])
                }), 429
            
            calls[client_ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal"""
    import re
    # Remove directory components
    filename = os.path.basename(filename)
    # Remove special characters
    filename = re.sub(r'[^\w\-_.]', '', filename)
    return filename

def get_system_info():
    """Get system information"""
    import platform
    import psutil
    
    info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'disk_usage': psutil.disk_usage('/')._asdict(),
        'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }
    
    return info

def send_email(to_email, subject, body):
    """Send email (stub for implementation)"""
    # In production, implement with SMTP or email service
    print(f"Email to {to_email}: {subject}")
    print(body)
    return True

def log_activity(user_id, action, details=None):
    """Log user activity"""
    from models import MongoDB
    db = MongoDB().db
    
    log_entry = {
        'user_id': user_id,
        'action': action,
        'details': details,
        'ip_address': request.remote_addr if request else None,
        'user_agent': request.user_agent.string if request else None,
        'timestamp': datetime.utcnow()
    }
    
    db.activity_logs.insert_one(log_entry)