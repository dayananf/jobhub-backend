JobHub Backend

A job portal REST API built using FastAPI, SQLAlchemy, and PostgreSQL.

Features

- User registration and login
- JWT-based authentication
- Role-based access control for candidates and recruiters
- Company management
- Job creation and search
- Candidate job applications
- Recruiter applicant management and application status updates
- Input validation and error handling

Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT authentication
- Git and GitHub

Run Locally

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install the required dependencies.
4. Configure your database connection and JWT secret using environment variables.
5. Start the API:

python -m uvicorn app.main:app --reload

Open "http://127.0.0.1:8000/docs" to explore the API using Swagger UI.

Security

Never commit database credentials, JWT secrets, or other sensitive environment variables.