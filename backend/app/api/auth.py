import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from app.database import db_manager
from app.dependencies import get_current_user
from app.models.user import UserInDB
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.security.jwt import create_access_token
from app.security.passwords import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest):
    """
    Registers a new user account with hashed password and generates an initial JWT token.
    """
    email_clean = request.email.lower().strip()

    # Check for existing account
    existing = db_manager.users.find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(request.password)
    now = datetime.now(timezone.utc)

    user_record = {
        "_id": user_id,
        "id": user_id,
        "email": email_clean,
        "hashed_password": hashed_pwd,
        "full_name": request.full_name.strip() if request.full_name else None,
        "is_active": True,
        "created_at": now
    }

    db_manager.users.insert_one(user_record)

    token = create_access_token(data={"sub": user_id, "email": email_clean})
    user_resp = UserResponse(
        id=user_id,
        email=email_clean,
        full_name=user_record["full_name"],
        created_at=now,
        is_active=True
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """
    Authenticates user credentials and issues a signed JWT access token.
    """
    email_clean = request.email.lower().strip()
    user_dict = db_manager.users.find_one({"email": email_clean})

    if not user_dict or not verify_password(request.password, user_dict.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user_dict.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    user_id = user_dict.get("id") or str(user_dict.get("_id"))
    token = create_access_token(data={"sub": user_id, "email": email_clean})

    created_at = user_dict.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    elif not created_at:
        created_at = datetime.now(timezone.utc)

    user_resp = UserResponse(
        id=user_id,
        email=email_clean,
        full_name=user_dict.get("full_name"),
        created_at=created_at,
        is_active=True
    )

    return TokenResponse(access_token=token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Returns profile information for the currently authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )
