import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func
from app.db import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_type = Column(String(32), nullable=False)
    source_uri = Column(String(1024), nullable=False)
    snapshot_hash = Column(String(64), nullable=False)
    snapshot_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    json = Column(Text, nullable=False)
    status = Column(String(32), default="draft", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False)
    artifact_json = Column(Text, nullable=False)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    evaluation_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())


class Progress(Base):
    __tablename__ = "progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    kind = Column(String(64), nullable=False)
    status = Column(String(32), default="queued", nullable=False)
    error = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())


class LabSession(Base):
    __tablename__ = "lab_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    course_id = Column(String(128), nullable=False)
    learner_key = Column(String(128), nullable=False, default="local")
    workspace_path = Column(String(1024), nullable=False)
    progress_json = Column(Text, nullable=False, default='{"passed": []}')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())


class LabRun(Base):
    __tablename__ = "lab_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("lab_sessions.id"), nullable=False)
    checkpoint_id = Column(String(32), nullable=False)
    mode = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False, default="queued")
    source_hash = Column(String(64), nullable=False)
    result_json = Column(Text, nullable=True)
    artifact_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), server_default=func.now())


class LabMessage(Base):
    __tablename__ = "lab_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("lab_sessions.id"), nullable=False)
    checkpoint_id = Column(String(32), nullable=False)
    run_id = Column(String(36), ForeignKey("lab_runs.id"), nullable=True)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    hint_level = Column(String(8), nullable=False, default="0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now())
