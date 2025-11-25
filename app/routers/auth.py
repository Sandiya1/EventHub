from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.auth.security import create_access_token, verify_password, hash_password
from app.auth.deps import get_current_user
from app.config import settings

# ✅ define this line!
router = APIRouter(prefix="/auth", tags=["auth"])

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    role: Optional[str] = "participant"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    venue: str
    speaker: str
    event_date: datetime
    total_seats: int
class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    venue: Optional[str] = None
    speaker: Optional[str] = None
    event_date: Optional[datetime] = None
    total_seats: Optional[int] = None
