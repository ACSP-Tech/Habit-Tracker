from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Annotated
import re

class Register(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=15, description="must include at least 1 letter(either uppercase or lower), 1 integer, and 1 special charater")]
    #field_validator to enforce description
    @field_validator("password")
    def validate_password(cls, v:str) ->str:
        v = v.strip()
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v
    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class MessageOut(BaseModel):
    message: str

class LoginUser(BaseModel):
    email: EmailStr
    password: str
    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

class LogRes(BaseModel):
    token: str
    token_type: str


class HabitCreate(BaseModel):
    """ 
    Pydantic model for add habit input validation.
    This model ensures that the habit title, description, and frequency are provided and meet the required
    criteria, frequency must be complete before 2am the said otherwise the habit will be considered broken and the user streak count will be reset to 0.
    Input: 
        email: specific user email, must be a valid email string 
        session: database session, default to system get_db
        raises: value error if title, description, or frequency do not meet the specified criteria
    """
    title: Annotated[str, Field(min_length=3, max_length=55, description="Habit title (3 to 55 characters)")]
    description: Annotated[str, Field(min_length=3, max_length=200, description="Habit details (3 to 200 characters")]
    frequency: Annotated[str, Field(description="Input either daily or weekly")]
    #field_validator 
    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()
    @field_validator("title")
    def normalize_title(cls, v: str) -> str:
        # Strip leading/trailing spaces and collapse multiple inner spaces into one
        cleaned = " ".join(v.split())

        # Ensure length is between 3 and 55 characters
        if not (3 <= len(cleaned) <= 55):
            raise ValueError("Title must be between 3 and 55 characters long")

        # Allow letters and single spaces between words (must start and end with a letter)
        if not re.fullmatch(r"[A-Za-z]+( [A-Za-z]+)*", cleaned):
            raise ValueError("Title must only contain alphabetic characters and spaces")
        return cleaned.title()
    
    @field_validator("description")
    def normalize_description(cls, v: str) -> str:
        # Strip edge spaces and collapse multiple inner spaces
        cleaned = " ".join(v.split())

        # Check length bounds
        if not (3 <= len(cleaned) <= 200):
            raise ValueError("Description must be between 3 and 200 characters long")

        # Allow letters, spaces, and standard punctuation (. , ! ? ' -)
        if not re.fullmatch(r"^[A-Za-z0-9\s.,!?'\-]+$", cleaned):
            raise ValueError("Description contains invalid characters")

        return cleaned.capitalize()
    @field_validator("frequency")
    def validate_and_normalize_frequency(cls, v: str) -> str:
        cleaned = v.strip().lower()
        allowed = {"daily", "weekly"}
        
        if cleaned not in allowed:
            raise ValueError(f"Frequency must be either 'daily' or 'weekly', got '{v}'")
            
        return cleaned


class HabitOut(BaseModel):
    """"
    Pydantic model for add habit output validation.
    Input: 
        email: specific user email, must be a valid email string 
    
    """
    message: str


class GetHabitOut(BaseModel):
    """
    Pydantic model for getting all habit output validation.
    """
    habit_id: str
    habit_title: str
    habit_description: str
    habit_frequency: str
    delete_status: bool
    is_active: bool
    break_task_status: bool
    system_streak_count: int
    user_streak_count: int
    frequency_goal_count: int
    no_of_failed_streak: int
    percentage_performance: float
    created_at: str
    start_at: str
    updated_at: str
    next_frequency_date: str
    user_id: str