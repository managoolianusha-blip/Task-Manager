"""SQLAlchemy data model for Task objects.

This module defines a `Task` ORM model alongside helper functions to
create the engine/session and initialize the database file. The model is
kept optional for projects that prefer the simple JSON storage used by the
app; switching to SQLAlchemy is supported via these helpers.
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, DateTime, Boolean, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

STATUS_CHOICES = ('pending', 'in_progress', 'done', 'archived')


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default='')
    priority = Column(Integer, default=3)
    due_date = Column(DateTime, nullable=True)
    status = Column(Enum(*STATUS_CHOICES, name='task_status'), default='pending')
    category = Column(String(100), default='')
    created_at = Column(DateTime, default=datetime.utcnow)

    """Represents a single task row in the database.

    Fields mirror the JSON representation used by the rest of the app and
    `to_dict()` returns a JSON-serializable mapping suitable for templates
    and APIs.
    """

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'category': self.category or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


def _default_db_url():
    """Return a sensible default SQLite URL located in `data/tasks.db`.

    The helper ensures the directory exists and formats the path for
    cross-platform compatibility (Windows path separators).
    """
    here = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(here, 'data', 'tasks.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # SQLite URLs on Windows should use forward slashes
    return 'sqlite:///' + db_path.replace('\\', '/')


def create_engine_and_session(db_url: str | None = None):
    url = db_url or _default_db_url()
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    return engine, Session


def init_db(db_url: str | None = None):
    engine, _ = create_engine_and_session(db_url)
    Base.metadata.create_all(engine)


__all__ = ['Base', 'Task', 'create_engine_and_session', 'init_db']
