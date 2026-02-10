import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from models import MongoDB
from auth import login_manager, create_user
from routes import register_routes
from websocket_handler import socketio
import os

def create_app(config_class=Config):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, supports_credentials=True)
    login_manager.init_app(app)
    
    # Initialize MongoDB
    with app.app_context():
        mongo = MongoDB()
        mongo.init_db()  # Ensure database is initialized
        app.mongo = mongo
    
    # Register routes
    register_routes(app)
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    
    # Initialize camera manager
    from camera_integration import camera_manager
    
    # Create default admin user if not exists
    @app.before_first_request
    def create_default_users():
        from models import User
        from werkzeug.security import generate_password_hash
        
        # Check if admin exists
        admin = User.find_by_email('admin@smartroads.com')
        if not admin:
            admin_user = User()
            admin_user.username = 'admin'
            admin_user.email = 'admin@smartroads.com'
            admin_user.password_hash = generate_password_hash('admin123')
            admin_user.full_name = 'System Administrator'
            admin_user.role = 'admin'
            admin_user.department = 'Administration'
            admin_user.save()
            print("Default admin user created: admin@smartroads.com / admin123")
        
        # Check if system user exists
        system = User.find_by_email('system@smartroads.com')
        if not system:
            system_user = User()
            system_user.username = 'system'
            system_user.email = 'system@smartroads.com'
            system_user.password_hash = generate_password_hash('system123')
            system_user.full_name = 'AI Detection System'
            system_user.role = 'authority'
            system_user.department = 'System'
            system_user.save()
            print("System user created for AI detections")
        
        # Register default ESP32 camera for development
        if app.config.get('GPS_SIMULATION'):
            camera_manager.register_camera(
                'esp32_dev',
                app.config['ESP32_CAM_IP'],
                app.config['ESP32_CAM_PORT']
            )
            print(f"Registered default ESP32 camera: {app.config['ESP32_CAM_IP']}:{app.config['ESP32_CAM_PORT']}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    print("Starting Smart Road Monitor System...")
    print(f"MongoDB URI: {app.config['MONGO_URI'][:30]}...")
    print(f"ESP32 Camera: {app.config['ESP32_CAM_IP']}:{app.config['ESP32_CAM_PORT']}")
    print(f"AI Model: {app.config['MODEL_PATH']}")
    
    # Start camera manager
    from camera_integration import camera_manager
    if app.config.get('GPS_SIMULATION'):
        camera_manager.start_all_cameras()
    
    # Run app with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True,
        log_output=True
    )