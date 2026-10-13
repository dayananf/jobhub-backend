from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =========================
# USER
# =========================

class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    role: str = Field(default="candidate")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime


# =========================
# COMPANY
# =========================

class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = None
    website: Optional[str] = None
    location: str = Field(min_length=2, max_length=100)


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    website: Optional[str]
    location: str
    recruiter_id: int


# =========================
# JOB
# =========================

class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10)
    location: str = Field(min_length=2, max_length=100)
    salary: Optional[int] = Field(default=None, gt=0)
    job_type: str
    experience: str
    company_id: int


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    location: str
    salary: Optional[int]
    job_type: str
    experience: str
    company_id: int
    is_active: bool
    created_at: datetime


# =========================
# APPLICATION
# =========================

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    status: str
    applied_at: datetime


class ApplicationStatusUpdate(BaseModel):
    status: str