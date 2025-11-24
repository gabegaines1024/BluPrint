from datetime import datetime
from flask_bcrypt import Bcrypt
from app.database import db

bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parts = db.relationship('Part', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    builds = db.relationship('Build', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_email: bool = False) -> dict:
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'username': self.username,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_email:
            data['email'] = self.email
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'

class Part(db.Model):
    __tablename__ = 'parts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    part_type = db.Column(db.String(50), nullable=False)
    manufacturer = db.Column(db.String(100))
    price = db.Column(db.Float)
    specifications = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'part_type': self.part_type,
            'manufacturer': self.manufacturer,
            'price': self.price,
            'specifications': self.specifications,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Build(db.Model):
    __tablename__ = 'builds'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    parts = db.Column(db.JSON)
    total_price = db.Column(db.Float)
    is_compatible = db.Column(db.Boolean, default=True)
    compatibility_issues = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parts': self.parts,
            'total_price': self.total_price,
            'is_compatible': self.is_compatible,
            'compatibility_issues': self.compatibility_issues,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CompatibilityRule(db.Model):
    __tablename__ = 'compatibility_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    part_type_1 = db.Column(db.String(50), nullable=False)
    part_type_2 = db.Column(db.String(50), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)
    rule_data = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'part_type_1': self.part_type_1,
            'part_type_2': self.part_type_2,
            'rule_type': self.rule_type,
            'rule_data': self.rule_data,
            'is_active': self.is_active
        }