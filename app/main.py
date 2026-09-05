#importing necessary requirements
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .setup_main import init_db, break_habit, configure_cors
import asyncio
from fastapi_pagination import add_pagination

#import router
from .router import add_habit

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start-up code
    await init_db()
    habit_cleanup_task = asyncio.create_task(break_habit())
    try:
        yield
    finally:
        habit_cleanup_task.cancel()
        try:
            await habit_cleanup_task
        except asyncio.CancelledError:
            pass

#calling an instance of fast api
app = FastAPI(
    title="Habit Tracker API",
    description="API for tracking user habits, managing streaks, and handling habit-related operations.",
    version="1.0.0",
    lifespan=lifespan
)

#definiing the cors function and any other custom middleware
configure_cors(app)

#include routers
app.include_router(add_habit.router)



#adding pagination to the app
add_pagination(app)