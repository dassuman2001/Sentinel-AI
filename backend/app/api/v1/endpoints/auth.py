from datetime import datetime, timedelta
from typing import Any
import httpx
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas, models
from app.database.session import get_db
from app.security import auth
from app.config.settings import settings

router = APIRouter()

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)) -> Any:
    """Register a new user."""
    # Check if user already exists
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    # First user registered in the system becomes Admin automatically
    user_count = db.query(models.User).count()
    role = "admin" if user_count == 0 else user_in.role
    
    hashed_pwd = auth.hash_password(user_in.password)
    db_user = models.User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=role,
        is_active=True,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login, retrieve access and refresh tokens."""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = auth.create_refresh_token(user.id)
    
    # Save session
    import hashlib
    refresh_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    session = models.UserSession(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)) -> Any:
    """Refresh access token using refresh token."""
    try:
        import jwt
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    # Check if session exists and is active in DB
    import hashlib
    refresh_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    session = db.query(models.UserSession).filter(
        models.UserSession.refresh_token_hash == refresh_hash,
        models.UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = auth.create_access_token(user_id, expires_delta=access_token_expires)
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/auth0-login", response_model=schemas.Token)
async def auth0_login(payload: schemas.Auth0Login, db: Session = Depends(get_db)) -> Any:
    """Authenticate or register user using Auth0 Google Token."""
    userinfo_url = f"https://{settings.AUTH0_DOMAIN}/userinfo"
    headers = {"Authorization": f"Bearer {payload.token}"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(userinfo_url, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Auth0 token or verification failed."
            )
        user_info = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Auth0 connection error: {str(e)}"
        )
        
    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auth0 token does not contain an email address."
        )
        
    # Check if user exists in our DB
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        # Create user
        first_name = user_info.get("given_name") or user_info.get("name", "").split(" ")[0]
        try:
            last_name = user_info.get("family_name") or user_info.get("name", "").split(" ")[1]
        except IndexError:
            last_name = ""
            
        user_count = db.query(models.User).count()
        role = "admin" if user_count == 0 else "member"
        
        # Secure random password
        random_password = secrets.token_hex(32)
        hashed_pwd = auth.hash_password(random_password)
        
        user = models.User(
            email=email,
            hashed_password=hashed_pwd,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            is_verified=user_info.get("email_verified", True)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Sync verified flag
        if user_info.get("email_verified") and not user.is_verified:
            user.is_verified = True
            db.commit()
            
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = auth.create_refresh_token(user.id)
    
    # Save session
    import hashlib
    refresh_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    session = models.UserSession(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/google-login")
async def google_login(
    req: schemas.GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user using Google OAuth ID Token (credential).
    Validates token against Google Tokeninfo API, then registers or logs in user.
    """
    tokeninfo_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(tokeninfo_url)
            
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google OAuth token or verification failed."
            )
        user_info = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google OAuth connection error: {str(e)}"
        )
        
    # Verify aud matches our Client ID
    aud = user_info.get("aud")
    if aud != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token audience (aud) mismatch. Potential security breach."
        )

    email = user_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token does not contain an email address."
        )
        
    # Check if user exists in our DB
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if req.is_signup:
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this Google email already exists. Please sign in."
            )
        # Create user
        first_name = user_info.get("given_name") or user_info.get("name", "").split(" ")[0]
        try:
            last_name = user_info.get("family_name") or user_info.get("name", "").split(" ")[1]
        except IndexError:
            last_name = ""
            
        user_count = db.query(models.User).count()
        role = "admin" if user_count == 0 else "member"
        
        # Secure random password
        random_password = secrets.token_hex(32)
        hashed_pwd = auth.hash_password(random_password)
        
        user = models.User(
            email=email,
            hashed_password=hashed_pwd,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            is_verified=str(user_info.get("email_verified", "true")).lower() == "true"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account associated with this Google email. Please sign up first."
            )
        # Sync verified flag
        email_verified_bool = str(user_info.get("email_verified", "false")).lower() == "true"
        if email_verified_bool and not user.is_verified:
            user.is_verified = True
            db.commit()
            
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = auth.create_refresh_token(user.id)
    
    # Save session
    import hashlib
    refresh_hash = hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    session = models.UserSession(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
