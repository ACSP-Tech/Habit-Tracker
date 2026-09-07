#importing necessary requirements
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .setup_main import init_db, break_habit, configure_cors
import asyncio
from fastapi_pagination import add_pagination

#import router
from .routers import router as habit_router

# Define the application lifespan context manager to handle startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and establish connection pools before serving requests
    await init_db()
    # Launch the recurring background task to check and break expired habit streaks
    habit_cleanup_task = asyncio.create_task(break_habit())
    try:
        # Yield control back to FastAPI; the app runs and serves requests during this period
        yield
    finally:
        # Signal the background task to stop when the server receives a shutdown signal
        habit_cleanup_task.cancel()
        try:
            # Await the task to ensure it finishes its current cycle and cleans up properly
            await habit_cleanup_task
        except (asyncio.CancelledError, Exception) as exc:
            pass

# Instantiate the core FastAPI application
app = FastAPI(
    # Set the human-readable project title for interactive OpenAPI documentation (/docs and /redoc)
    title="Habit Tracker API",
    # Provide an overview of the API's features and scope displayed in the documentation header
    description="API for tracking user habits, managing streaks, and handling habit-related operations.",
    # Define the current semantic version of the application
    version="1.0.0",
    # Register the async context manager to handle startup (DB init, background workers) and shutdown cleanup
    lifespan=lifespan
)

#definiing the cors function and any other custom middleware
configure_cors(app)

#include routers
app.include_router(habit_router)



#adding pagination to the app
add_pagination(app)