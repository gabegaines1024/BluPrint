"""Pydantic schemas for request/response validation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============ User Schemas ============

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============ Part Schemas ============

class PartBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    part_type: str = Field(..., min_length=1, max_length=50)
    manufacturer: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    specifications: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    part_type: Optional[str] = Field(None, min_length=1, max_length=50)
    manufacturer: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    specifications: Optional[Dict[str, Any]] = None


class PartResponse(PartBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Build Schemas ============

class BuildBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parts: List[int] = Field(..., min_items=1)


class BuildCreate(BuildBase):
    pass


class BuildUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    parts: Optional[List[int]] = None


class BuildResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parts: List[int]
    total_price: Optional[float] = None
    is_compatible: bool
    compatibility_issues: Optional[List[str]] = None
    compatibility_warnings: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Compatibility Schemas ============

class CompatibilityCheckRequest(BaseModel):
    part_ids: List[int] = Field(..., min_items=0)

    @field_validator('part_ids')
    @classmethod
    def validate_part_ids(cls, v):
        if not all(isinstance(pid, int) for pid in v):
            raise ValueError('All part IDs must be integers')
        return v


class CompatibilityCheckResponse(BaseModel):
    is_compatible: bool
    issues: List[str]
    warnings: List[str]


class CompatibilityRuleCreate(BaseModel):
    part_type_1: str = Field(..., min_length=1, max_length=50)
    part_type_2: str = Field(..., min_length=1, max_length=50)
    rule_type: str = Field(..., min_length=1, max_length=50)
    rule_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CompatibilityRuleResponse(BaseModel):
    id: int
    part_type_1: str
    part_type_2: str
    rule_type: str
    rule_data: Optional[Dict[str, Any]] = None
    is_active: bool

    class Config:
        from_attributes = True


# ============ Recommendation Schemas ============

class RecommendationRequest(BaseModel):
    part_type: Optional[str] = None
    budget: float = Field(..., gt=0)
    existing_parts: Optional[List[int]] = Field(default_factory=list)
    min_performance: Optional[float] = Field(5, ge=0, le=10)
    budget_ratio: Optional[float] = Field(0.3, ge=0, le=1)
    num_recommendations: Optional[int] = Field(10, ge=1, le=50)


class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    count: int
    model_version: str


class ModelStatusResponse(BaseModel):
    available: bool
    model_version: Optional[str] = None
    model_path: Optional[str] = None


# ============ Agent Schemas ============

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    message: str
    recommended_parts: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    build_suggestion: Optional[Dict[str, Any]] = None


class ContextResponse(BaseModel):
    context: Dict[str, Any]


class ResetResponse(BaseModel):
    message: str


class SaveBuildRequest(BaseModel):
    name: str = Field(default="My PC Build", min_length=1)
    parts: List[int] = Field(..., min_items=1)
    description: Optional[str] = None


# ============ Error Response ============

class ErrorResponse(BaseModel):
    error: str
    status_code: int
    detail: Optional[str] = None


# ============ Health Check ============

class HealthCheckResponse(BaseModel):
    status: str
    database: str


