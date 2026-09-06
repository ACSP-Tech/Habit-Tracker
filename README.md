# Habit Tracker API

The Habit Tracker API is a backend service designed to help users define, track, and maintain daily and weekly habits. It automates streak tracking, enforces completion cadences, and runs periodic background workers to detect missed deadlines and break unfulfilled streaks.

The service provides endpoints for habit lifecycle management, streak analytics (highest and struggling streaks), frequency-based filtering, and JWT-authenticated user security.

## Features

1. User Authentication & Verification: Secure JWT-based registration and login flows with email verification safeguards and password hashing.

2. Habit Lifecycle Management: Complete CRUD workflow for habits including custom titles, descriptions, and frequency (daily or weekly)..

3. Automated Streak Calculation: Dynamically computes active streaks, user records, and tracks failure rates upon habit completion.

4. Soft-Delete Architecture: Safe deletion mechanisms ensuring historical metrics and completion audit logs remain intact.

5. Background Lifecycle Worker: An automated task running within the application lifespan that evaluates habit completion deadlines and breaks streaks for overdue habits.

6. Analytics & Filtering: Endpoints to inspect a user's longest active streak, identify struggling/weak habits, or filter by recurrence frequency..

7. Pagination Support: Scalable cursor/page pagination across all habit collection endpoints via fastapi-pagination.

## Tech Stack

1. Framework: FastAPI

2. Database: PostgreSQL

3. ORM: SQLModel & SQLAlchemy (Async engine)

4. Driver: asyncpg

5. Data Validation: Pydantic v2

6. Authentication: JWT (pyjwt) and Passlib / Bcrypt

7. Pagination: fastapi-pagination

## Installation and run instruction

-  Getting Started

1. Local Setup (Virtual Environment)

- Clone the repository: 
    - git clone <this github url> 
    - cd Habit Tracker

- Create and activate a virtual environment  on windows:

    - python -m venv .venv
    - .venv\Scripts\activate


- Install dependencies:

    - pip install -r requirements.txt



- Configure Environment Variables:
    - Create a .env file in the project root with the following keys.
    - input the database url, secret_key and algorithm
        https://drive.google.com/file/d/1ZBpyhV9XHRC2Shn0b0gfQdUpN-TV6UU2/view?usp=sharing

- Run the service:
    - The app will be available at (http://127.0.0.1:8000/).

    - uvicorn app.main:app





##  API Endpoints

- All endpoints documentation are available at (http://127.0.0.1:8000/docs) and (http://127.0.0.1:8000/redoc)
- use postman for the authenticated route.