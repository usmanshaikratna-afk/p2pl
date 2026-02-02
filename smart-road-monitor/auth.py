from flask import current_app, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime
from models import User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.find_by_id(user_id)

def create_user(username, email, password, full_name=None, role='citizen'):
    """Create a new user"""
    if User.find_by_email(email):
        return None, 'Email already registered'
    
    if User.find_by_username(username):
        return None, 'Username already taken'
    
    user = User()
    user.username = username
    user.email = email
    user.password_hash = generate_password_hash(password)
    user.full_name = full_name or username
    user.role = role
    user.created_at = datetime.datetime.utcnow()
    
    user_id = user.save()
    return User.find_by_id(user_id), None

def authenticate_user(email, password):
    """Authenticate user and return user object if successful"""
    user = User.find_by_email(email)
    if not user or not user.is_active:
        return None, 'Invalid credentials or account inactive'
    
    if check_password_hash(user.password_hash, password):
        user.update_last_login()
        return user, None
    
    return None, 'Invalid credentials'

def generate_token(user, expiration_hours=24):
    """Generate JWT token for API authentication"""
    payload = {
        'user_id': str(user._id),
        'email': user.email,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expiration_hours)
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def verify_token(token):
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        user = User.find_by_id(payload['user_id'])
        if user and user.is_active:
            return user, None
        return None, 'User not found or inactive'
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'

def authority_required(f):
    """Decorator to require authority role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authority():
            from flask import flash, redirect, url_for
            flash('You need authority permissions to access this page.', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            from flask import flash, redirect, url_for
            flash('You need administrator permissions to access this page.', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def api_token_required(f):
    """Decorator for API token authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header missing'}), 401
        
        try:
            token = auth_header.split(' ')[1]
            user, error = verify_token(token)
            if error:
                return jsonify({'error': error}), 401
            request.user = user
        except Exception as e:
            return jsonify({'error': 'Invalid token format'}), 401
        
        return f(*args, **kwargs)
    return decorated_function