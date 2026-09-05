from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import String, Integer, Boolean, DateTime, func, text, Float
from typing import Optional, List
import uuid
from pydantic import EmailStr
from datetime import datetime

class Users(SQLModel, table=True):
    id: str = Field(
    default_factory=lambda: str(uuid.uuid4()),
    sa_column=Column(String(36), primary_key=True, nullable=False)
    )
    email: EmailStr = Field(
        sa_column=Column(String, unique=True, nullable=False, index=True)
    )
    hashed_password: str = Field(
        sa_column=Column(String, nullable=False))
    
    #defining relationships
    Habits: List["Habit"] = Relationship(back_populates="users")

class Habit(SQLModel, table=True):
    habit_id: str = Field(
    default_factory=lambda: str(uuid.uuid4()),
    sa_column=Column(String(36), primary_key=True, nullable=False)
    )
    habit_title: str = Field(
        sa_column=Column(String, nullable=False))
    habit_description: str = Field(
        sa_column=Column(String, nullable=False))
    habit_frequency: str = Field(
        sa_column=Column(String, nullable=False))
    delete_status: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default=text("false"), index=True))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, server_default=text("true"), index=True))
    break_task_status: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default=text("false"), index=True))
    system_streak_count: int = Field(default= 0, sa_column=Column(Integer, nullable=False, index=True))
    user_streak_count: int = Field(default= 0, sa_column=Column(Integer, nullable=False, index=True))
    frequency_goal_count: int = Field(default= 0, sa_column=Column(Integer, nullable=False, index=True))
    no_of_failed_streak: int = Field(default= 0, sa_column=Column(Integer, nullable=False, index=True))
    percentage_performance: float = Field(default=0.0, sa_column=Column(Float, nullable=False, default=0.0, index=True))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    start_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False))
    next_frequency_date: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=True, index=True))
    user_id: str = Field(foreign_key="users.id")

    #defining relationships
    users: Optional["Users"] = Relationship(back_populates="Habits")