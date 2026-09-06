from fastapi import APIRouter, HTTPException, status, Depends, Query
from .schema import Register, MessageOut, LoginUser, LogRes, HabitCreate, HabitOut, GetHabitOut, HabitOutRes
from .crud import habit_creation, Habit_lists, user_register, user_login, mark_habit_done, habit_deleted, streak_max, weak_habit, get_filtered_habits
from .setup_main import get_db
from .dep import user_auth, MyParams


router = APIRouter(prefix="/Tracker", tags=["Habit Tracker Application"])

@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=MessageOut)
async def register(data:Register, session=Depends(get_db)):
    """
    **User Registration**

    Register a new user account, persist 5 predefined record to the database.

    **Arguments:**
    * **data**: User registration schema payload (Body).
    * **session**: Async database session instance (`get_db`).

    **Raises:**
    * **HTTPException (409 Conflict)**: Duplicate email or phone number detected.
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database error.

    **Returns:**
    * **MessageOut**: Confirmation response with HTTP 201 Created.
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
async def login(data:LoginUser, session=Depends(get_db)):
    """
    **User Authentication Flow**

    Authenticate an existing user, verify credentials, and return an access token.

    **Arguments:**
    * **data**: Login credentials schema payload (`LoginUser`).
    * **session**: Async database session instance (`get_db`).

    **Raises:**
    * **HTTPException (401 Unauthorized)**: Invalid credentials provided.
    * **HTTPException (403 Forbidden)**: User account is unverified.
    * **HTTPException (404 Not Found)**: User does not exist.
    * **HTTPException (500 Internal Server Error)**: Internal server or database failure.

    **Returns:**
    * **LogRes**: Access token payload with HTTP 200 OK.
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
    **Habit Creation Flow**

    Create and persist a new tracking habit associated with the authenticated user profile.

    **Arguments:**
    * **data**: Habit definition payload schema (`HabitCreate`).
    * **token**: Bearer token to verify current uses, if using postman, under authorization, select bearer token and input as gotten from login.
    * **session**: Async database session instance (`get_db`).

    **Raises:**
    * **HTTPException (409 Conflict)**: Duplicate habit title or conflict detected.
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database failure.

    **Returns:**
    * **MessageOut**: Confirmation status response with HTTP 201 Created.
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
    

@router.get("/habits/lists", status_code=status.HTTP_200_OK)
async def get_all_habits(params: MyParams = Depends(), session=Depends(get_db), token = Depends(user_auth)):
    """
    **Habit Retrieval Flow**

    Retrieve all habit details for the authenticated user.

    **Arguments:**
    * **token**: Bearer token to verify current uses, if using postman, under authorization, select bearer token and input as gotten from login.
    * **page**: Page query parameters to flip through page.
    * **size**: size query parameters to specify number of records per page.
    * **session**: Async database session instance (`get_db`).

    **Raises:**
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database failure.

    **Returns:**
    * **Get all habit in a list, the total habits, page and size per page. then the current page all in a dict**: Habit details response with HTTP 200 OK.
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

@router.patch("/habits/checker/{habit_id}", status_code=status.HTTP_200_OK, response_model=MessageOut)
async def checked_habit_done(habit_id: str, session = Depends(get_db), token = Depends(user_auth)):
    """
    **Mark Habit As Completed**

    Record a completion entry for a specific habit, increment the user's active streak count, and update the last completed timestamp.

    **Arguments:**
    * **habit_id**: Unique UUID string identifying the target habit (Path parameter).
    * **session**: Async database session instance (`get_db`).
    * **token**: Bearer token to verify current uses, if using postman, under authorization, select bearer token and input as gotten from login..

    **Raises:**
    * **HTTPException (400 Bad Request)**: Habit has already been completed for the current interval/period.
    * **HTTPException (401 Unauthorized)**: Authentication credentials invalid or expired.
    * **HTTPException (404 Not Found)**: Habit does not exist or has been deleted.
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database failure.

    **Returns:**
    * **MessageOut**: Success confirmation message with HTTP 200 OK.
    """
    try:
        response = await mark_habit_done(habit_id, session, token)
        return response
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.patch("/habits/deletion/{habit_id}", status_code=status.HTTP_200_OK, response_model=MessageOut)
async def delete_habit(habit_id: str, session = Depends(get_db), token = Depends(user_auth)):
    """
    **Soft Delete Habit**

    Mark an existing habit as deleted without permanently removing its historical record from the database.

    **Arguments:**
    * **habit_id**: Unique UUID string identifying the target habit (Path parameter).
    * **session**: Async database session instance (`get_db`).
    * **token**: Bearer token to verify current uses, if using postman, under authorization, select bearer token and input as gotten from login.

    **Raises:**
    * **HTTPException (401 Unauthorized)**: Authentication credentials invalid or expired.
    * **HTTPException (404 Not Found)**: Habit does not exist or has already been deleted.
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database failure.

    **Returns:**
    * **MessageOut**: Confirmation message indicating successful deletion with HTTP 200 OK.
    """
    try:
        response = await habit_deleted(habit_id, session, token)
        return response
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    

@router.get("/habits/longeststreak", status_code=status.HTTP_200_OK)
async def get_longest_streak(params: MyParams = Depends(),session=Depends(get_db), token = Depends(user_auth)):
    """
    **Longest Streak Retrieval Flow**

    Calculate and retrieve the habit(s) holding the maximum active streak count for the authenticated user, excluding habits with zero or inactive streaks.

    **Arguments:**
    * **params**: Pagination parameters schema (`MyParams`) uses pige and size as query parameters for further control
    * **page**: Page query parameters to flip through page.
    * **size**: size query parameters to specify number of records per page.
    * **session**: Async database session instance (`get_db`).
    * **token**: Bearer token to verify current uses, if using postman, under authorization, select bearer token and input as gotten from login.


    **Raises:**
    * **HTTPException (401 Unauthorized)**: Authentication credentials invalid or expired.
    * **HTTPException (404 Not Found)**: No active habits with longest streaks found for the user.
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database failure.

    **Returns:**
    * **Page[HabitOut]**: Paginated collection of habits matching the highest streak count with HTTP 200 OK.
    """
    try:
        return await streak_max(params,session, token)
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/habits/weakstreak", status_code=status.HTTP_200_OK)
async def weak_habit_list(params: MyParams = Depends(), session=Depends(get_db), token = Depends(user_auth)):
    """
    **Weakest Streak Retrieval Flow**

    Retrieve active habits that require attention, sorted by the lowest percentage performance until 70.0 percent for the authenticated user.

    **Arguments:**
    * **params**: Pagination parameters schema (`MyParams`), uses pige and size as query parameters for further control
    * **page**: Page query parameters to flip through page.
    * **size**: size query parameters to specify number of records per page.
    * **session**: Async database session instance (`get_db`).
    * **token**: Bearer token to verify current uses, if using postman, under authorization, select bearer token and input as gotten from login..

    **Raises:**
    * **HTTPException (401 Unauthorized)**: Authentication credentials invalid or expired.
    * **HTTPException (404 Not Found)**: No weak habits found for this user.
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database failure.

    **Returns:**
    * **Page[HabitOut]**: Paginated list of habits with the lowest streak values with HTTP 200 OK.
    """
    try:
        return await weak_habit(params, session, token)
    except HTTPException as Httpexc:
        raise Httpexc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/habits/filter", status_code=status.HTTP_200_OK)
async def filter_habit_by_frequency(
        frequency: str = Query("daily", alias="frequency", pattern="^(daily|weekly)$", description="Filter habits by frequency: daily or weekly"),
        params: MyParams = Depends(),
        token: str = Depends(user_auth),
        session=Depends(get_db)
):
    """
    **Filter Habits by Frequency**

    Retrieve a paginated list of habits for the authenticated user, filtered by frequency (`daily` or `weekly`).

    **Arguments:**
    * **frequency**: Recurrence pattern filter (`daily` or `weekly`). Defaults to `daily`.
    * **params**: Custom pagination parameters schema (`MyParams`), uses pige and size as query parameters for further control
    * **page**: Page query parameters to flip through page.
    * **size**: size query parameters to specify number of records per page.
    * **token**: Bearer token to verify current uses, if using postman, under authorization, select bearer token and input as gotten from login.
    * **session**: Async database session instance (`get_db`).

    **Raises:**
    * **HTTPException (401 Unauthorized)**: Authentication credentials invalid or expired.
    * **HTTPException (422 Unprocessable Entity)**: Invalid frequency parameter supplied.
    * **HTTPException (500 Internal Server Error)**: Unhandled server or database failure.

    **Returns:**
    * **Page[HabitOut]**: Paginated collection of matching active habits with HTTP 200 OK.
    """
    try:
        return await get_filtered_habits(frequency, params, token, session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )