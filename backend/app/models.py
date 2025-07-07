import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

from enum import Enum as PyEnum

class TargetType(PyEnum):
    LARAVEL = "laravel"
    WORDPRESS = "wordpress"

class Severity(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Target(Base):
    __tablename__ = "targets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_or_name = Column(String(255), nullable=False)
    type = Column(Enum(TargetType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scan_at = Column(DateTime)
    findings = relationship("Finding", back_populates="target", cascade="all, delete-orphan")

class Finding(Base):
    __tablename__ = "findings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id", ondelete="CASCADE"))
    component = Column(String(255))         # package / plugin / theme
    detected_version = Column(String(50))
    fixed_version = Column(String(50))
    cve = Column(String(50))                # may be empty
    title = Column(Text)
    severity = Column(Enum(Severity))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)

    target = relationship("Target", back_populates="findings")
