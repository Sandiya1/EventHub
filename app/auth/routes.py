from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

from pydantic import BaseModel

class SignupPayload(BaseModel):
    name: str
    email: str
    password: str
    role: str

@router.post("/signup", status_code=201)
def signup(payload: SignupPayload, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(payload.password)
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hashed_pw,
        role=payload.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}



# ---------- LOGIN ----------
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": user.email, "role": user.role.value})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value
    }

