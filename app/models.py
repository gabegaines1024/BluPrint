from datetime import datetime
from app.database import db

class Part(db.Model):
    __tablename__ = 'parts'
    
    id = db.Column(db.Integer, primary_key=True)
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