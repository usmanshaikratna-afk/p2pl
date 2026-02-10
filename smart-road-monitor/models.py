from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient, GEOSPHERE, ASCENDING, DESCENDING
from flask import current_app
import json

class MongoDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize attributes
            cls._instance.client = None
            cls._instance.db = None
        return cls._instance
    
    def init_db(self):
        try:
            self.client = MongoClient(current_app.config['MONGO_URI'], serverSelectionTimeoutMS=5000)
            self.db = self.client[current_app.config['MONGO_DBNAME']]
            self.create_indexes()
            print(f"MongoDB connected to database: {current_app.config['MONGO_DBNAME']}")
            return True
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            self.client = None
            self.db = None
            return False
    
    def get_db(self):
        """Get database connection, initialize if needed"""
        if self.db is None:
            self.init_db()
        return self.db
    
    def create_indexes(self):
        if self.db is None:
            return
            
        try:
            # Users collection
            self.db.users.create_index([('email', ASCENDING)], unique=True)
            self.db.users.create_index([('username', ASCENDING)], unique=True)
            
            # Road reports collection
            self.db.road_reports.create_index([('location', GEOSPHERE)])
            self.db.road_reports.create_index([('status', ASCENDING)])
            self.db.road_reports.create_index([('severity', ASCENDING)])
            self.db.road_reports.create_index([('created_at', DESCENDING)])
            
            # Camera detections collection
            self.db.camera_detections.create_index([('timestamp', DESCENDING)])
            self.db.camera_detections.create_index([('location', GEOSPHERE)])
            
            # Maintenance teams collection
            self.db.maintenance_teams.create_index([('status', ASCENDING)])
            
            # Statistics collection
            self.db.statistics.create_index([('date', DESCENDING)])
            print("Database indexes created/verified")
        except Exception as e:
            print(f"Error creating indexes: {e}")

class User:
    def __init__(self, data=None):
        self._id = None
        self.username = None
        self.email = None
        self.password_hash = None
        self.full_name = None
        self.role = 'citizen'
        self.department = None
        self.phone = None
        self.avatar = None
        self.is_active = True
        self.created_at = datetime.utcnow()
        self.last_login = None
        
        if data:
            self._id = data.get('_id')
            self.username = data.get('username')
            self.email = data.get('email')
            self.password_hash = data.get('password_hash')
            self.full_name = data.get('full_name')
            self.role = data.get('role', 'citizen')
            self.department = data.get('department')
            self.phone = data.get('phone')
            self.avatar = data.get('avatar')
            self.is_active = data.get('is_active', True)
            self.created_at = data.get('created_at', datetime.utcnow())
            self.last_login = data.get('last_login')
    
    def save(self):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            print("Warning: MongoDB not available, user not saved")
            return None
            
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'full_name': self.full_name,
            'role': self.role,
            'department': self.department,
            'phone': self.phone,
            'avatar': self.avatar,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
        
        if self._id:
            result = db.users.update_one({'_id': self._id}, {'$set': user_data})
            return self._id
        else:
            result = db.users.insert_one(user_data)
            self._id = result.inserted_id
            return self._id
    
    @classmethod
    def find_by_email(cls, email):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return None
            
        user_data = db.users.find_one({'email': email})
        if user_data:
            return cls(user_data)
        return None
    
    @classmethod
    def find_by_username(cls, username):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return None
            
        user_data = db.users.find_one({'username': username})
        if user_data:
            return cls(user_data)
        return None
    
    @classmethod
    def find_by_id(cls, user_id):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return None
            
        try:
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return cls(user_data)
        except:
            pass
        return None
    
    def update_last_login(self):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return
            
        self.last_login = datetime.utcnow()
        db.users.update_one(
            {'_id': self._id},
            {'$set': {'last_login': self.last_login}}
        )
    
    def is_authority(self):
        return self.role in ['authority', 'admin']
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_id(self):
        return str(self._id) if self._id else None

class RoadReport:
    def __init__(self, data=None):
        self._id = None
        self.reporter_id = None
        self.location = None
        self.address = None
        self.issue_type = None
        self.severity = None
        self.description = None
        self.images = []
        self.status = 'pending'
        self.priority = 1
        self.assigned_to = None
        self.assigned_at = None
        self.resolved_at = None
        self.resolution_notes = None
        self.resolution_images = []
        self.verification_score = 0
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if data:
            self._id = data.get('_id')
            self.reporter_id = data.get('reporter_id')
            self.location = data.get('location')
            self.address = data.get('address')
            self.issue_type = data.get('issue_type')
            self.severity = data.get('severity')
            self.description = data.get('description')
            self.images = data.get('images', [])
            self.status = data.get('status', 'pending')
            self.priority = data.get('priority', 1)
            self.assigned_to = data.get('assigned_to')
            self.assigned_at = data.get('assigned_at')
            self.resolved_at = data.get('resolved_at')
            self.resolution_notes = data.get('resolution_notes')
            self.resolution_images = data.get('resolution_images', [])
            self.verification_score = data.get('verification_score', 0)
            self.created_at = data.get('created_at', datetime.utcnow())
            self.updated_at = data.get('updated_at', datetime.utcnow())
    
    def save(self):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            print("Warning: MongoDB not available, report not saved")
            return None
            
        report_data = {
            'reporter_id': self.reporter_id,
            'location': self.location,
            'address': self.address,
            'issue_type': self.issue_type,
            'severity': self.severity,
            'description': self.description,
            'images': self.images,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'assigned_at': self.assigned_at,
            'resolved_at': self.resolved_at,
            'resolution_notes': self.resolution_notes,
            'resolution_images': self.resolution_images,
            'verification_score': self.verification_score,
            'created_at': self.created_at,
            'updated_at': datetime.utcnow()
        }
        
        if self._id:
            result = db.road_reports.update_one({'_id': self._id}, {'$set': report_data})
            return self._id
        else:
            result = db.road_reports.insert_one(report_data)
            self._id = result.inserted_id
            return self._id
    
    @classmethod
    def find_by_id(cls, report_id):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return None
            
        try:
            report_data = db.road_reports.find_one({'_id': ObjectId(report_id)})
            if report_data:
                return cls(report_data)
        except:
            pass
        return None
    
    @classmethod
    def find_nearby(cls, longitude, latitude, max_distance=5000):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return []
            
        query = {
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [longitude, latitude]
                    },
                    '$maxDistance': max_distance
                }
            }
        }
        reports = db.road_reports.find(query)
        return [cls(report) for report in reports]
    
    @classmethod
    def get_all(cls, filters=None, page=1, per_page=20):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return {'reports': [], 'total': 0, 'page': page, 'per_page': per_page, 'pages': 0}
            
        query = {}
        
        if filters:
            if 'status' in filters:
                query['status'] = filters['status']
            if 'severity' in filters:
                query['severity'] = filters['severity']
            if 'issue_type' in filters:
                query['issue_type'] = filters['issue_type']
            if 'date_from' in filters:
                query['created_at'] = {'$gte': filters['date_from']}
            if 'date_to' in filters:
                if 'created_at' in query:
                    query['created_at']['$lte'] = filters['date_to']
                else:
                    query['created_at'] = {'$lte': filters['date_to']}
        
        skip = (page - 1) * per_page
        reports = db.road_reports.find(query).sort('created_at', DESCENDING).skip(skip).limit(per_page)
        total = db.road_reports.count_documents(query)
        
        return {
            'reports': [cls(report) for report in reports],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    def assign_to(self, user_id, team_id=None):
        self.assigned_to = user_id
        self.assigned_at = datetime.utcnow()
        self.status = 'assigned'
        self.save()
    
    def mark_resolved(self, notes=None, images=None):
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = notes
        if images:
            self.resolution_images = images
        self.save()
    
    def to_json(self):
        return {
            'id': str(self._id) if self._id else None,
            'reporter_id': str(self.reporter_id) if self.reporter_id else None,
            'location': self.location,
            'address': self.address,
            'issue_type': self.issue_type,
            'severity': self.severity,
            'description': self.description,
            'images': self.images,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': str(self.assigned_to) if self.assigned_to else None,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CameraDetection:
    def __init__(self, data=None):
        self._id = None
        self.camera_id = None
        self.location = None
        self.image_url = None
        self.detections = []
        self.confidence = None
        self.processed = False
        self.report_id = None
        self.timestamp = datetime.utcnow()
        
        if data:
            self._id = data.get('_id')
            self.camera_id = data.get('camera_id')
            self.location = data.get('location')
            self.image_url = data.get('image_url')
            self.detections = data.get('detections', [])
            self.confidence = data.get('confidence')
            self.processed = data.get('processed', False)
            self.report_id = data.get('report_id')
            self.timestamp = data.get('timestamp', datetime.utcnow())
    
    def save(self):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            print("Warning: MongoDB not available, detection not saved")
            return None
            
        detection_data = {
            'camera_id': self.camera_id,
            'location': self.location,
            'image_url': self.image_url,
            'detections': self.detections,
            'confidence': self.confidence,
            'processed': self.processed,
            'report_id': self.report_id,
            'timestamp': self.timestamp
        }
        
        if self._id:
            result = db.camera_detections.update_one({'_id': self._id}, {'$set': detection_data})
            return self._id
        else:
            result = db.camera_detections.insert_one(detection_data)
            self._id = result.inserted_id
            return self._id
    
    @classmethod
    def get_recent(cls, limit=100):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return []
            
        detections = db.camera_detections.find().sort('timestamp', DESCENDING).limit(limit)
        return [cls(detection) for detection in detections]

class MaintenanceTeam:
    def __init__(self, data=None):
        self._id = None
        self.name = None
        self.members = []
        self.location = None
        self.status = 'available'
        self.current_assignment = None
        self.equipment = []
        self.contact = None
        
        if data:
            self._id = data.get('_id')
            self.name = data.get('name')
            self.members = data.get('members', [])
            self.location = data.get('location')
            self.status = data.get('status', 'available')
            self.current_assignment = data.get('current_assignment')
            self.equipment = data.get('equipment', [])
            self.contact = data.get('contact')
    
    def save(self):
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            print("Warning: MongoDB not available, team not saved")
            return None
            
        team_data = {
            'name': self.name,
            'members': self.members,
            'location': self.location,
            'status': self.status,
            'current_assignment': self.current_assignment,
            'equipment': self.equipment,
            'contact': self.contact
        }
        
        if self._id:
            result = db.maintenance_teams.update_one({'_id': self._id}, {'$set': team_data})
            return self._id
        else:
            result = db.maintenance_teams.insert_one(team_data)
            self._id = result.inserted_id
            return self._id

class Statistics:
    @staticmethod
    def update_daily_stats():
        mongo = MongoDB()
        db = mongo.get_db()
        if db is None:
            return {}
            
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count reports by status
        stats = {
            'date': today,
            'total_reports': db.road_reports.count_documents({'created_at': {'$gte': today}}),
            'pending_reports': db.road_reports.count_documents({'status': 'pending'}),
            'resolved_reports': db.road_reports.count_documents({'status': 'resolved'}),
            'high_priority': db.road_reports.count_documents({'severity': 'high'}),
            'ai_detections': db.camera_detections.count_documents({'timestamp': {'$gte': today}}),
            'updated_at': datetime.utcnow()
        }
        
        db.statistics.update_one(
            {'date': today},
            {'$set': stats},
            upsert=True
        )
        
        return stats