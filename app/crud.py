from .model import Habit, Users
from fastapi import HTTPException, status
from sqlmodel import select
from .schema import HabitOut, MessageOut, LogRes
from sqlalchemy import and_
from .dep import compute_initial_deadlines, password_hash, password_verify, DEFAULT_HABITS, decode_token, encode_token
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.exc import SQLAlchemyError

async def user_register(data, session):
    try:
        #avoid duplicate
        statement = select(Users).where(Users.email == data.email)
        result = await session.execute(statement)
        user_email = result.scalars().first()
        if user_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email {data.email} already registered"
            )
        #hash password
        hash_password = await password_hash(data.password)
        #add user
        user = Users(
            email = data.email,
            hashed_password = hash_password,
        )
        session.add(user)
        await session.flush()  # Flushes user.id into session context without final commit

        # 2. Add the 5 predefined starter habits
        for starter in DEFAULT_HABITS:
            start_date, next_date = compute_initial_deadlines(starter["frequency"])
            habit_record = Habit(
                habit_title=starter["title"],
                habit_description=starter["description"],
                habit_frequency=starter["frequency"],
                user_id=user.id,  # Valid UUID from the new user
                start_at=start_date,
                next_frequency_date=next_date,
            )
            session.add(habit_record)

        await session.commit()
        await session.refresh(user)
        response = f"Account {data.email} successfully registered. Kindly use the login endpoint next"
        return MessageOut(message=response)
    except HTTPException as Httpexc:
        await session.rollback()
        raise Httpexc
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )  

async def user_login(data, session):
    try:
        statement = select(Users).where(Users.email == data.email)
        result = await session.execute(statement)
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail= f"User with mail {data.email} not found"
            )
        verify = await password_verify(data.password, user.hashed_password)
        if not verify:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password")           
        payload = {
            "email": user.email,
            "id": user.id,
        }
        user_token = await encode_token(payload)
        return LogRes(
            token=user_token,
            token_type="bearer"
        )
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed: {str(e)}"
        )

async def habit_creation(data, session,token):
    try:
        #get payload from token
        payload = await decode_token(token)
        user_id = payload.get("id")

        statement = select(Habit).where(and_(Habit.habit_title == data.title, Habit.habit_frequency == data.frequency, Habit.user_id == user_id, Habit.delete_status == False))
        result = await session.execute(statement)
        existing_habit = result.scalars().first()
        if existing_habit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Habit title {data.title} already exist for this frequency, chose a different tile or frequency"
            )
        start_date, next_date = compute_initial_deadlines(data.frequency)
        new_habit = Habit(
        habit_title = data.title,
        habit_description = data.description,
        habit_frequency = data.habit_frequency,
        user_id = user_id,
        start_at = start_date,
        next_frequency_date = next_date)
        session.add(new_habit)
        await session.commit()
        await session.refresh(new_habit)
        response = f"{data.title} successfully created"
        return HabitOut(message=response)
    except HTTPException as Httpexc:
        await session.rollback()
        raise Httpexc
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        ) 


async def Habit_lists(params, session, token):
    """
    Get all available habits for the user with pagination
    Returns Habit listings
    """
    try:
        #get payload from token
        payload = await decode_token(token)
        user_id = payload.get("id")
        #GET all habit for the current user that is not deleted
        statement = select(Habit).where(
            and_(Habit.user_id == user_id, Habit.delete_status == False)).order_by(Habit.created_at.desc())

        return await paginate(session, statement, params)

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
