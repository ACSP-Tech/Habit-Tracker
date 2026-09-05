from decouple import config
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import SQLModel, select
from datetime import datetime, timezone, timedelta
from .model import Habit
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_
import asyncio
from fastapi import FastAPI

def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

DATABASE_URL = config('DATABASE_URL')

#normalizing the aiven postgres url
def normalize_url(url: str) -> str:
    # Convert postgres:// → postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Convert postgresql:// → postgresql+asyncpg://
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Remove ?sslmode=require (asyncpg doesn't support it)
    if "sslmode" in url:
        url = url.split("?")[0]

    return url

#async postgres url
ASYNC_DATABASE_URL = normalize_url(DATABASE_URL)

# SQLModel engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Optional: set to False in production
    future=True
)
#async session maker
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

#asyn session
async def get_db():
    async with async_session() as session:
        try:
            yield session
        except IntegrityError:
            await session.rollback()
            raise
        except SQLAlchemyError:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise


#initialize and create db and tables
async def init_db() -> None:
    async with engine.begin() as conn:
        #print("Running init_db...")  
        await conn.run_sync(SQLModel.metadata.create_all)
        #print("Tables created (if not exist)")

async def break_habit():
    try:
        while True:
            async with AsyncSession(engine) as db:
                #handle broken habits 
                now = datetime.now(timezone.utc)
                statement = select(Habit).where(and_(Habit.next_frequency_date < now, Habit.delete_status == False, Habit.frequency_goal_count == 0))
                result = await db.exec(statement)
                broken_habit = result.all()
                
                for entry in broken_habit:
                    entry.user_streak_count = 0
                    entry.break_task_status = True
                    entry.system_streak_count += 1
                    entry.no_of_failed_streak += 1
                    # Habit cycle starts today at 01;00
                    entry.start_at = now.replace(hour=1, minute=0, second=0, microsecond=0)
                    # Calculate percentage performance
                    if entry.system_streak_count > 0:
                        perf = (entry.system_streak_count - entry.no_of_failed_streak) / entry.system_streak_count
                        entry.percentage_performance = round(float(perf * 100), 2)
                    else:
                        entry.percentage_performance = 0.0
                    #next_frequency_timeline
                    entry.next_frequency_date = (now + timedelta(days=1)).replace(hour=1, minute=0, second=0, microsecond=0) if entry.habit_frequency == "daily" else (now + timedelta(weeks=1)).replace(hour=1, minute=0, second=0, microsecond=0)
                                
                await db.commit()
                print(f"Cleanup task completed: {len(broken_habit)} entries processed") 
            now = datetime.now(timezone.utc)
            tomorrow_2am = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
            sleep_seconds = (tomorrow_2am - now).total_seconds()
            print(f"{sleep_seconds}")     
            await asyncio.sleep(sleep_seconds)
    except asyncio.CancelledError:
        print(f"Break habit background task cleanly shut down")
        return 