from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.crud import user as user_crud
from app.security.jwt import verify_password, create_access_token
from app.models.user import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Register a new user account with email and password.
    
    **Allowed Roles:**
    - Buyer: Can create projects and assign tasks
    - Developer: Can complete tasks and submit solutions
    
    **Restrictions:**
    - Admin registration is blocked for security
    - Email must be unique
    
    **Request Body:**
    - email: Valid email address
    - password: User password (will be hashed)
    - role: Either "buyer" or "developer"
    - full_name: Optional full name
    
    **Returns:**
    - User object with id, email, role, and created_at timestamp
    """,
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Email already registered"},
        403: {"description": "Admin registration not allowed"}
    }
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (only Buyer or Developer, not Admin)"""
    # Prevent admin registration
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is not allowed"
        )
    
    # Check if user already exists
    db_user = user_crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    return user_crud.create_user(db=db, user=user)

@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="""
    Authenticate user and receive JWT access token.
    
    **Authentication Flow:**
    1. Provide email and password
    2. Server validates credentials
    3. Returns JWT token if valid
    4. Use token in Authorization header for protected endpoints
    
    **Request Body:**
    - email: Registered email address
    - password: User password
    
    **Returns:**
    - access_token: JWT token (valid for 7 days)
    - token_type: "bearer"
    
    **How to use the token:**
    ```
    Authorization: Bearer <your_access_token>
    ```
    
    **Token contains:**
    - User email
    - User role
    - Expiration time
    """,
    responses={
        200: {"description": "Login successful, token returned"},
        401: {"description": "Incorrect email or password"}
    }
)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = user_crud.get_user_by_email(db, email=user_login.email)
    
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}