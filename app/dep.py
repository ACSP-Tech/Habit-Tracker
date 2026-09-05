from datetime import datetime, timezone, timedelta
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from decouple import config
from fastapi_pagination import Params
import jwt
from fastapi import HTTPException, status
from .model import Users
from sqlmodel import select
from sqlalchemy import and_
from fastapi import Depends, HTTPException, status
from .setup_main import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def password_hash(password):
    """permently Hash plain password"""
    return pwd_context.hash(password)

async def password_verify(plain_password, hashpassword):
    """verify user password"""
    return pwd_context.verify(plain_password, hashpassword)

SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config('ALGORITHM')

async def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, ALGORITHM)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token. Please log in again.",
        )
    
async def encode_token(payload, expires_delta: int = 86400):
    """
    Encode a JWT token with the given payload and expiration time.
    Args:
        payload (dict): The data to encode in the token.
        expires_delta (int, optional): Expiration time in minutes. Default is 24 hours.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = payload.copy()
    now = datetime.utcnow()
    expire = now + timedelta(minutes=expires_delta)

    # Add issued-at and expiry
    to_encode.update({
        "iat": now,
        "exp": expire
    })

    # return encoded JWT token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



async def is_user(token, session) -> bool:
    try:
        payload = await decode_token(token)
        email = payload.get("email")
        id = payload.get("id")
        statement = select(Users).where(and_(Users.email == email, Users.id == id))
        result = await session.execute(statement)
        user = result.scalars().first()
        if not user:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return False
    except HTTPException as http_exc:
        raise http_exc

# Define OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")

async def user_auth(token=Depends(oauth2_scheme), session=Depends(get_db)):
   """
   user authentication dependency.
   """
   try:
       await is_user(token, session)
       return token 
   except Exception as e:
       raise HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail=str(e)
       )

DEFAULT_HABITS = [
    {
        "title": "Morning Hydration",
        "description": "Drink at least 500ml of water immediately after waking up",
        "frequency": "daily",
    },
    {
        "title": "Daily Movement",
        "description": "Engage in at least 20 minutes of physical exercise or brisk walking",
        "frequency": "daily",
    },
    {
        "title": "Reading",
        "description": "Read at least 10 pages of an educational or personal growth book",
        "frequency": "daily",
    },
    {
        "title": "Weekly Planning",
        "description": "Review progress and plan key priorities for the upcoming week",
        "frequency": "weekly",
    },
    {
        "title": "Digital Declutter",
        "description": "Organize desktop files, clear unnecessary emails, and back up notes",
        "frequency": "weekly",
    },
]

def compute_initial_deadlines(frequency: str):
    """Calculates start_at and the first check-in deadline."""
    now = datetime.now(timezone.utc)
    start_date = now.replace(hour=1, minute=0, second=0, microsecond=0)
    
    if frequency == "daily":
        next_date = (now + timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0)
    else:  # weekly
        next_date = (now + timedelta(weeks=1)).replace(hour=1, minute=0, second=0, microsecond=0)
        
    return start_date, next_date

class MyParams(Params):
    size: int = 5