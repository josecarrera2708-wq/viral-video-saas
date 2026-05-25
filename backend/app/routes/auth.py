"""
Authentication routes
Login, signup, token refresh
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr

from ..database import get_db
from ..models.user import User
from ..auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    Token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    """Signup request payload"""
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response"""
    id: str
    email: str
    name: str
    credits_balance: int
    subscription_tier: str

    class Config:
        from_attributes = True


class TokenResponse(Token):
    """Token response with user data"""
    user: UserResponse


@router.post("/signup", response_model=TokenResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Create new user account"""

    # Check if user exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    try:
        user = User(
            email=request.email,
            name=request.name,
            hashed_password=get_password_hash(request.password),
            subscription_tier="free",
            credits_balance=0,  # Free tier starts with no credits
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Generate tokens
    access_token = create_access_token(user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        user=UserResponse.from_orm(user)
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""

    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()

    # Generate tokens
    access_token = create_access_token(user.id, user.email)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        user=UserResponse.from_orm(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    token: str = None,
    db: Session = Depends(get_db)
):
    """Get current user (requires Bearer token in header)"""

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify token
    token_data = verify_token(token)

    # Get user
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""

    # Verify refresh token
    token_data = verify_token(refresh_token)

    # Get user
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create new access token
    new_access_token = create_access_token(user.id, user.email)

    return Token(
        access_token=new_access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email
    )
