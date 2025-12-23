from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parts = relationship('Part', back_populates='owner', cascade='all, delete-orphan')
    builds = relationship('Build', back_populates='owner', cascade='all, delete-orphan')
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = pwd_context.hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return pwd_context.verify(password, self.password_hash)
    
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


class Part(Base):
    __tablename__ = 'parts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    part_type = Column(String(50), nullable=False)
    manufacturer = Column(String(100))
    price = Column(Float)
    specifications = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship('User', back_populates='parts')
    
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


class Build(Base):
    __tablename__ = 'builds'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    parts = Column(JSON)
    total_price = Column(Float)
    is_compatible = Column(Boolean, default=True)
    compatibility_issues = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship('User', back_populates='builds')
    
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


class CompatibilityRule(Base):
    __tablename__ = 'compatibility_rules'
    
    id = Column(Integer, primary_key=True, index=True)
    part_type_1 = Column(String(50), nullable=False)
    part_type_2 = Column(String(50), nullable=False)
    rule_type = Column(String(50), nullable=False)
    rule_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'part_type_1': self.part_type_1,
            'part_type_2': self.part_type_2,
            'rule_type': self.rule_type,
            'rule_data': self.rule_data,
            'is_active': self.is_active
        }