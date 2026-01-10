"""
Models package initialization.
Initializes SQLAlchemy and exports all models.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import models after db initialization to avoid circular imports
from app.models.flow import Flow
from app.models.execution import FlowExecution, TaskExecution, ExecutionStatus

# Export all models and db instance
__all__ = [
    'db',
    'Flow',
    'FlowExecution',
    'TaskExecution',
    'ExecutionStatus'
]
