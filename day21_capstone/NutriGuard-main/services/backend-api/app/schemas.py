from pydantic import BaseModel, EmailStr
from pydantic import Field
from datetime import datetime
from typing import List, Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class UserProfileCreate(BaseModel):
    goal: Optional[str] = None
    goals: Optional[List[str]] = None
    diet_type: Optional[str] = None
    health_conditions: Optional[List[str]] = None
    health_conditions_text: Optional[str] = None
    deficiencies: Optional[List[str]] = None
    deficiencies_text: Optional[str] = None
    supplements: Optional[List[str]] = None
    supplements_text: Optional[str] = None
    health_report_text: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class MealCreate(BaseModel):
    user_id: int
    meal_text: Optional[str] = None
    foods_text: Optional[str] = None
    drinks_text: Optional[str] = None
    supplements_text: Optional[str] = None
    notes_text: Optional[str] = None
    meal_type: Optional[str] = None
    meal_time: Optional[datetime] = None


class MealResponse(BaseModel):
    meal_log_id: int
    status: str
    message: str


class ReportResponse(BaseModel):
    status: str
    summary: str
    recommendations: List[str]
    safety_note: str
