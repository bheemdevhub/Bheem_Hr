from sqlalchemy import Column, String, Date, Time, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.shared.models import Base, TimestampMixin, SoftDeleteMixin, AuditMixin
import uuid
from datetime import datetime

class DailyActivity(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "hr_daily_activities"
    __table_args__ = {'schema': 'hr'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=False, index=True)
    activity_date = Column(Date, nullable=False, default=datetime.utcnow)
    activity_type = Column(String(100), nullable=False)  # e.g. 'attendance', 'meeting', 'leave', 'task', etc.
    description = Column(Text, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    meta = Column(Text, nullable=True)  # JSON/text for extra info

    # Relationship
    employee = relationship("Employee", backref="daily_activities")
