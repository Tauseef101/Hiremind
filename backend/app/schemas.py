from pydantic import BaseModel, Field
from typing import List, Optional

class Register(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=6)
    role: str

class Login(BaseModel):
    email: str
    password: str

class JobCreate(BaseModel):
    title: str
    description: str
    skills: List[str]
    experience: int = 0
    location: str = 'Remote'
    employment_type: str = 'Full-time'
    salary: str = ''
    openings: int = 1
    deadline: str = ''

class StatusUpdate(BaseModel):
    status: str

class InterviewSubmit(BaseModel):
    answers: List[str]

class CodingSubmit(BaseModel):
    code: str

class ScheduleCreate(BaseModel):
    test_type: str          # 'interview' | 'coding' | 'final' | 'project' | 'skills' | 'situational'
    scheduled_at: str       # ISO datetime string
    notes: Optional[str] = ''

class ProjectItem(BaseModel):
    title: str
    description: str
    github_url: Optional[str] = ''
    live_url: Optional[str] = ''
    technologies: List[str] = []

class ProjectVerifySubmit(BaseModel):
    projects: List[ProjectItem]
    portfolio_url: Optional[str] = ''
    portfolio_summary: Optional[str] = ''

class SkillAssessmentSubmit(BaseModel):
    answers: List[str]

class SituationalSubmit(BaseModel):
    responses: List[str]

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None  # UUID, generated on frontend, reused per session
