#importing the necessary requirements
from .model import Habit, Users
from fastapi import HTTPException, status
from sqlmodel import select
from .schema import HabitOut, MessageOut, LogRes
from sqlalchemy import and_, func
from .dep import compute_initial_deadlines, password_hash, password_verify, DEFAULT_HABITS, decode_token, encode_token
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone, timedelta 

async def user_register(data, session):
    try:
        #avoid duplicate creation of user email
        statement = select(Users).where(Users.email == data.email)
        result = await session.execute(statement)
        user_email = result.scalars().first()
        if user_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email {data.email} already registered"
            )
        #hash password before storing
        hash_password = await password_hash(data.password)
        #add user to the database
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
        #confirm the email inputed is a registered user
        statement = select(Users).where(Users.email == data.email)
        result = await session.execute(statement)
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail= f"User with mail {data.email} not found"
            )
        #verify password inputed for registered email is correct
        verify = await password_verify(data.password, user.hashed_password)
        if not verify:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password")   
        #create payload to be encoded        
        payload = {
            "email": user.email,
            "id": user.id,
        }
        #encode payload to send to the login user
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
        #get payload from token and obtain user id from payload
        payload = await decode_token(token)
        user_id = payload.get("id")
        #check if habit title already exist for the user with the same frequency
        statement = select(Habit).where(and_(Habit.habit_title == data.title, Habit.habit_frequency == data.frequency, Habit.user_id == user_id, Habit.delete_status == False))
        result = await session.execute(statement)
        existing_habit = result.scalars().first()
        #raise expection if title and frquency for current user exist
        if existing_habit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Habit title {data.title} already exist for this frequency, chose a different tile or frequency"
            )
        #compute start date and next frequency date for the habit
        start_date, next_date = compute_initial_deadlines(data.frequency)
        #create new habit record for the user
        new_habit = Habit(
        habit_title = data.title,
        habit_description = data.description,
        habit_frequency = data.frequency,
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
        #get payload from token and user id
        payload = await decode_token(token)
        user_id = payload.get("id")
        #GET all habit for the current user that is not deleted, order by created_at in descending order
        statement = select(Habit).where(
            and_(Habit.user_id == user_id, Habit.delete_status == False)).order_by(Habit.created_at.desc())
        result = await session.execute(statement)
        all_habit = result.first()
        # check if any habit exists for the user
        if not all_habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active habits found for this user",
            )
        #return a paginated list of habits for the users, use page and size as query parameters to control pagination.
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

async def mark_habit_done(habit_id, session, token):
    try:
        #get payload from token and use_id 
        payload = await decode_token(token)
        user_id = payload.get("id")
        #get the current UTC time
        now = datetime.now(timezone.utc)
        #check if the habit exists for the user and is not deleted
        statement = select(Habit).where(and_(Habit.habit_id == habit_id, Habit.user_id == user_id, Habit.delete_status == False))
        result = await session.execute(statement)
        habit = result.scalars().first()
        # check if the habit exists for the user and is not deleted
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Habit with id {habit_id} not found"
            )
        # check if the habit is active (start_at <= now)
        statement = select(Habit).where(and_(Habit.habit_id == habit_id, Habit.user_id == user_id, Habit.delete_status == False, now >= Habit.start_at))
        result = await session.execute(statement)
        habit = result.scalars().first()
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Habit with id {habit_id} is not yet active. kindly check the get all habit for the start date"
            )
        # Update the habit's table to reflect that the habit has been completed for the current frequency cycle
        habit.frequency_goal_count = 1
        habit.complete_current_habit = True
        habit.break_task_status = False
        habit.user_streak_count += 1
        habit.system_streak_count += 1
        if habit.system_streak_count > 0:
            perf = (habit.system_streak_count - habit.no_of_failed_streak) / habit.system_streak_count
            habit.percentage_performance = round(float(perf * 100), 2)
        else:
            habit.percentage_performance = 0.0
        
        #next_frequency_timeline
        start_date = (habit.start_at + timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0) if habit.habit_frequency == "daily" else (now + timedelta(weeks=1)).replace(hour=1, minute=0, second=0, microsecond=0)
        end_date = (start_date + timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0) if habit.habit_frequency == "daily" else (start_date + timedelta(weeks=1)).replace(hour=1, minute=0, second=0, microsecond=0)
        habit.start_at = start_date
        habit.next_frequency_date = end_date

        await session.commit()
        await session.refresh(habit)

        response = f"Habit {habit.habit_title} marked as done. Next check-in is on {start_date}"
        return MessageOut(message=response)

    except HTTPException as Httpexc:
        await session.rollback()
        raise Httpexc

async def habit_deleted(habit_id, session, token):
    try:
        #get payload from token and user_id
        payload = await decode_token(token)
        user_id = payload.get("id")
        #check if the habit exists for the user and is not deleted
        statement = select(Habit).where(and_(Habit.habit_id == habit_id, Habit.user_id == user_id, Habit.delete_status == False))
        result = await session.execute(statement)
        habit = result.scalars().first()
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Habit with id {habit_id} not found"
            )
        # Soft delete the habit
        habit.delete_status = True
        await session.commit()
        await session.refresh(habit)

        response = f"Habit {habit.habit_title} deleted successfully."
        return MessageOut(message=response)

    except HTTPException as Httpexc:
        await session.rollback()
        raise Httpexc


async def streak_max(params,session, token):
    """
    Get the longest streak for the current user
    """
    try: 
        #get payload from token
        payload = await decode_token(token)
        user_id = payload.get("id")
        #1. Query the maximum streak count for the user
        max_streak_stmt = (
            select(func.max(Habit.user_streak_count))
            .where(
                and_(
                    Habit.user_id == user_id,
                    Habit.delete_status == False,
                    Habit.user_streak_count > 0
                )
            )
        )
        max_streak = (await session.execute(max_streak_stmt)).scalar()
        #raise an exception if max streak habits above zero found for the user
        if max_streak is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No max streak habits above zero found for this user",
            )

        # 2. Query all habits that match that max streak
        habits_stmt = (
            select(Habit)
            .where(
                and_(
                    Habit.user_id == user_id,
                    Habit.delete_status == False,
                    Habit.user_streak_count == max_streak
                )
            )
            .order_by(Habit.created_at.desc())
        )
        # 3. Paginate the results
        return await paginate(session, habits_stmt, params)

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

async def weak_habit(params, session, token):
    """
    Get the list of weak habit for current user, sort percentage performance in ascending order up until 70.0
    Returns weak habit listings
    """
    try:
        #get payload from token and user id
        payload = await decode_token(token)
        user_id = payload.get("id")
        #GET all habit for the current user that is not deleted and the percentage is below 70%
        statement = select(Habit).where(
            and_(Habit.user_id == user_id, Habit.delete_status == False, Habit.percentage_performance <= 70.0)).order_by(Habit.percentage_performance.asc())
        result = await session.execute(statement)
        weak_habit = result.first()
        #raise an exception if no weak habit found for the user
        if not weak_habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No weak habits found for this user",
            )
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


async def get_filtered_habits(frequency, params, token, session):
    """
    Get all filtered habit by the user with pagination
    """
    try:
        # get payload from token and user id from payload
        payload = await decode_token(token)
        user_id = payload.get("id")
        # GET all habit for the current user that is not deleted and matches the specified frequency
        statement = select(Habit).where(and_(
            Habit.user_id == user_id,
            Habit.delete_status == False,
            Habit.habit_frequency == frequency,
        )).order_by(Habit.created_at.desc())
        result = await session.execute(statement)
        all_habit = result.first()
        if not all_habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active habits found for this user",
            )
        #return a paginated list of habits for the habits, use page and size as query parameters to control pagination.
        return await paginate(session, statement, params)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving borrowed books: {str(e)}"
        )