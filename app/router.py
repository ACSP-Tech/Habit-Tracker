from fastapi import APIRouter, HTTPException, status, Depends
from .schema import Register, MessageOut, LoginUser, LogRes, HabitCreate, HabitOut, GetHabitOut
from .crud import habit_creation, Habit_lists, user_register, user_login
from .setup_main import get_db
from .dep import user_auth, MyParams

router = APIRouter(prefix="/Tracker", tags=["Habit Tracker Application"])

@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=MessageOut)
async def register(data:Register, session=Depends(get_db)):
    """
    step 1: user verification flow
    registration route, frontend integration: create user, send verification email to user
    Args: 
        data: Register Input Schema, Body parameter
        background_tasks: default FastAPI background tasks for sending email
        session: database session, default to system get_db
        raises:
            HTTPException 500 for internal server error and 409 conflict for duplicate email or phone_number
    Returns:
        MessageOut output schema, 201 created
        send verification email to client
    """
    try:
        return await user_register(data, session)
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/signin", response_model=LogRes, status_code=status.HTTP_200_OK)
async def Login(data:LoginUser, session=Depends(get_db)):
    """
    User Login API: send verification email if account not verified, else login user and return token
    Frontend integration
    Args:
        data: LoginUser Schema Body parameter
        session: default to database session
        raise: 404 user not found, 401 invalid password, 403 account not verified, 500 internal server error
    Returns:
        Logout schema json response
        200 ok response
    """
    try:
        return await user_login(data, session)
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/habits", status_code=status.HTTP_201_CREATED, response_model=HabitOut)
async def add_habit(data:HabitCreate, session=Depends(get_db), token = Depends(user_auth)):
    """
    step 1: user verification flow
    registration route, frontend integration: create user, send verification email to user
    Args: 
        data: Habitcreate Input Schema, Body parameter
        current_user: user object, default to system get_or_create_user
        session: database session, default to system get_db
        raises:
            HTTPException 500 for internal server error and 409 conflict for duplicate email or phone_number
    Returns:
        MessageOut output schema, 201 created
    """
    try: 
        return await habit_creation(data, session,token)
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    

@router.get("/habits/lists", status_code=status.HTTP_200_OK, response_model=GetHabitOut)
async def get_all_habits(params: MyParams = Depends(), session=Depends(get_db), token = Depends(user_auth)):
    """
    step 1: user verification flow
    registration route, frontend integration: create user, send verification email to user
    Args: 
        data: GetHabit Input Schema, Body parameter
        current_user: user object, default to system get_or_create_user
        session: database session, default to system get_db
        raises:
            HTTPException 500 for internal server error and 409 conflict for duplicate email or phone_number
    Returns:
        GetHabitOut output schema, 200 OK
    """
    try:
        return await Habit_lists(params, session, token)
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    