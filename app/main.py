from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.dependencies import get_current_user, require_role
from app.models import Application, Company, Job, User
from app.schemas import (
    ApplicationResponse,
    ApplicationStatusUpdate,
    CompanyCreate,
    CompanyResponse,
    JobCreate,
    JobResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JobHub API",
    description="Job Portal Backend API",
    version="1.0.0",
)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Welcome to JobHub API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==========================================
# AUTHENTICATION
# ==========================================

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    allowed_roles = {
        "candidate",
        "recruiter"
    }

    if user_data.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Role must be candidate or recruiter"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(
            user_data.password
        ),
        role=user_data.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get(
    "/auth/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user


# ==========================================
# COMPANIES
# ==========================================

@app.post(
    "/companies",
    response_model=CompanyResponse,
    status_code=201
)
def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(
        require_role("recruiter")
    ),
    db: Session = Depends(get_db)
):
    company = Company(
        name=company_data.name,
        description=company_data.description,
        website=company_data.website,
        location=company_data.location,
        recruiter_id=current_user.id,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


@app.get(
    "/companies/{company_id}",
    response_model=CompanyResponse
)
def get_company(
    company_id: int,
    db: Session = Depends(get_db)
):
    company = db.get(Company, company_id)

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    return company


# ==========================================
# JOBS
# ==========================================

@app.post(
    "/jobs",
    response_model=JobResponse,
    status_code=201
)
def create_job(
    job_data: JobCreate,
    current_user: User = Depends(
        require_role("recruiter")
    ),
    db: Session = Depends(get_db)
):
    company = db.get(
        Company,
        job_data.company_id
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )

    if company.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create jobs for your company"
        )

    job = Job(
        title=job_data.title,
        description=job_data.description,
        location=job_data.location,
        salary=job_data.salary,
        job_type=job_data.job_type,
        experience=job_data.experience,
        company_id=job_data.company_id,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@app.get(
    "/jobs",
    response_model=list[JobResponse]
)
def get_jobs(
    location: Optional[str] = Query(
        default=None
    ),
    job_type: Optional[str] = Query(
        default=None
    ),
    experience: Optional[str] = Query(
        default=None
    ),
    search: Optional[str] = Query(
        default=None
    ),
    page: int = Query(
        default=1,
        ge=1
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100
    ),
    db: Session = Depends(get_db)
):
    query = db.query(Job).filter(
        Job.is_active == True
    )

    if location:
        query = query.filter(
            Job.location.ilike(
                f"%{location}%"
            )
        )

    if job_type:
        query = query.filter(
            Job.job_type.ilike(
                f"%{job_type}%"
            )
        )

    if experience:
        query = query.filter(
            Job.experience.ilike(
                f"%{experience}%"
            )
        )

    if search:
        query = query.filter(
            or_(
                Job.title.ilike(
                    f"%{search}%"
                ),
                Job.description.ilike(
                    f"%{search}%"
                )
            )
        )

    offset = (page - 1) * limit

    return (
        query
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job


@app.put(
    "/jobs/{job_id}",
    response_model=JobResponse
)
def update_job(
    job_id: int,
    job_data: JobCreate,
    current_user: User = Depends(
        require_role("recruiter")
    ),
    db: Session = Depends(get_db)
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    company = db.get(
        Company,
        job.company_id
    )

    if company.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update this job"
        )

    job.title = job_data.title
    job.description = job_data.description
    job.location = job_data.location
    job.salary = job_data.salary
    job.job_type = job_data.job_type
    job.experience = job_data.experience

    db.commit()
    db.refresh(job)

    return job


@app.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    current_user: User = Depends(
        require_role("recruiter")
    ),
    db: Session = Depends(get_db)
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    company = db.get(
        Company,
        job.company_id
    )

    if company.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete this job"
        )

    job.is_active = False

    db.commit()

    return {
        "message": "Job deleted successfully"
    }


# ==========================================
# APPLICATIONS
# ==========================================

@app.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationResponse,
    status_code=201
)
def apply_job(
    job_id: int,
    current_user: User = Depends(
        require_role("candidate")
    ),
    db: Session = Depends(get_db)
):
    job = db.get(Job, job_id)

    if not job or not job.is_active:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    existing_application = (
        db.query(Application)
        .filter(
            Application.candidate_id
            == current_user.id,
            Application.job_id
            == job_id
        )
        .first()
    )

    if existing_application:
        raise HTTPException(
            status_code=409,
            detail="You already applied for this job"
        )

    application = Application(
        candidate_id=current_user.id,
        job_id=job_id,
        status="APPLIED",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


@app.get(
    "/applications/my",
    response_model=list[ApplicationResponse]
)
def my_applications(
    current_user: User = Depends(
        require_role("candidate")
    ),
    db: Session = Depends(get_db)
):
    return (
        db.query(Application)
        .filter(
            Application.candidate_id
            == current_user.id
        )
        .order_by(
            Application.applied_at.desc()
        )
        .all()
    )


@app.get(
    "/jobs/{job_id}/applications",
    response_model=list[ApplicationResponse]
)
def get_job_applications(
    job_id: int,
    current_user: User = Depends(
        require_role("recruiter")
    ),
    db: Session = Depends(get_db)
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    company = db.get(
        Company,
        job.company_id
    )

    if company.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot view these applications"
        )

    return (
        db.query(Application)
        .filter(
            Application.job_id == job_id
        )
        .order_by(
            Application.applied_at.desc()
        )
        .all()
    )


@app.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse
)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    current_user: User = Depends(
        require_role("recruiter")
    ),
    db: Session = Depends(get_db)
):
    allowed_statuses = {
        "APPLIED",
        "SHORTLISTED",
        "REJECTED",
        "HIRED",
    }

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid application status"
        )

    application = db.get(
        Application,
        application_id
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    job = db.get(
        Job,
        application.job_id
    )

    company = db.get(
        Company,
        job.company_id
    )

    if company.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update this application"
        )

    application.status = status_data.status

    db.commit()
    db.refresh(application)

    return application