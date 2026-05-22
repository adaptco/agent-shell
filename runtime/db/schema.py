from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import DeclarativeBase, relationship
import enum

class Base(DeclarativeBase):
    pass

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    permissions = Column(JSON)  # List of allowed capabilities

class Worker(Base):
    __tablename__ = 'workers'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'))
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    role = relationship("Role")

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    task_id = Column(String, unique=True, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    assigned_worker_id = Column(String, ForeignKey('workers.id'), nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ApprovalRequest(Base):
    __tablename__ = 'approval_requests'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    operation = Column(String, nullable=False)  # e.g., "bash_command", "git_push"
    details = Column(JSON)  # The specific command or tool call data
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    requester_id = Column(String, nullable=False)
    resolver_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

class Receipt(Base):
    __tablename__ = 'receipts'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=True)
    action = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    metadata_json = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class WorkflowSpec(Base):
    __tablename__ = 'workflow_specs'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # e.g., "PRD", "PROGRESS"
    content = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
