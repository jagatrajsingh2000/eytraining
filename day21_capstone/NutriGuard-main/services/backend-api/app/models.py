from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    goal = Column(String(50), nullable=False)
    goals = Column(JSON, nullable=True)
    diet_type = Column(String(50), nullable=True)
    health_conditions = Column(JSON, nullable=True)
    health_conditions_text = Column(Text, nullable=True)
    deficiencies = Column(JSON, nullable=True)
    deficiencies_text = Column(Text, nullable=True)
    supplements = Column(JSON, nullable=True)
    supplements_text = Column(Text, nullable=True)
    health_report_text = Column(Text, nullable=True)
    health_report_filename = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class MealLog(Base):
    __tablename__ = "meal_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_text = Column(Text, nullable=False)
    foods_text = Column(Text, nullable=True)
    drinks_text = Column(Text, nullable=True)
    supplements_text = Column(Text, nullable=True)
    notes_text = Column(Text, nullable=True)
    meal_type = Column(String(50), nullable=True)
    meal_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="RECEIVED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class NutritionFlag(Base):
    __tablename__ = "nutrition_flags"
    id = Column(Integer, primary_key=True, index=True)
    meal_log_id = Column(Integer, ForeignKey("meal_logs.id"), nullable=False)
    type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_log_id = Column(Integer, ForeignKey("meal_logs.id"), nullable=False)
    summary = Column(Text, nullable=False)
    recommendations = Column(JSON, nullable=True)
    safety_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
