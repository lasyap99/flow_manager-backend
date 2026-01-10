"""
Execution models - represents flow and task execution records.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.models import db


class ExecutionStatus(enum.Enum):
    """Enum for execution status values."""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILURE = 'failure'
    COMPLETED = 'completed'


class FlowExecution(db.Model):
    """
    FlowExecution model representing a single execution instance of a flow.
    
    Tracks the overall execution of a flow from start to completion/failure.
    """
    
    __tablename__ = 'flow_executions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to Flow
    flow_id = Column(String(100), ForeignKey('flows.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Execution status
    status = Column(
        SQLEnum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Input context for the flow execution
    input_context = Column(JSON, nullable=True)
    
    # Final output after flow completion
    output_data = Column(JSON, nullable=True)
    
    # Error information if execution failed
    error_message = Column(Text, nullable=True)
    error_task = Column(String(100), nullable=True)  # Task where error occurred
    
    # Execution metrics
    total_tasks_executed = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    flow = relationship('Flow', back_populates='executions')
    task_executions = relationship(
        'TaskExecution',
        back_populates='flow_execution',
        cascade='all, delete-orphan',
        order_by='TaskExecution.started_at'
    )
    
    def __init__(self, flow_id, input_context=None):
        """
        Initialize a new FlowExecution.
        
        Args:
            flow_id: ID of the flow being executed
            input_context: Initial context data for the flow execution
        """
        self.flow_id = flow_id
        self.input_context = input_context or {}
        self.status = ExecutionStatus.PENDING
    
    def __repr__(self):
        """String representation of FlowExecution."""
        return f'<FlowExecution {self.id}: Flow={self.flow_id}, Status={self.status.value}>'
    
    def to_dict(self, include_tasks=False):
        """
        Convert FlowExecution to dictionary representation.
        
        Args:
            include_tasks: Whether to include task execution details
        
        Returns:
            Dictionary representation of the FlowExecution
        """
        data = {
            'id': self.id,
            'flow_id': self.flow_id,
            'status': self.status.value,
            'input_context': self.input_context,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'error_task': self.error_task,
            'total_tasks_executed': self.total_tasks_executed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
        
        if include_tasks:
            data['task_executions'] = [
                task.to_dict() for task in self.task_executions
            ]
        
        return data
    
    def mark_running(self):
        """Mark the flow execution as running."""
        self.status = ExecutionStatus.RUNNING
    
    def mark_completed(self, output_data=None):
        """
        Mark the flow execution as completed successfully.
        
        Args:
            output_data: Final output data from the flow
        """
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.output_data = output_data
    
    def mark_failed(self, error_message, error_task=None):
        """
        Mark the flow execution as failed.
        
        Args:
            error_message: Description of the error
            error_task: Name of the task where failure occurred
        """
        self.status = ExecutionStatus.FAILURE
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_task = error_task
    
    def get_duration_seconds(self):
        """
        Calculate the duration of the execution in seconds.
        
        Returns:
            Duration in seconds or None if not completed
        """
        if not self.completed_at:
            return None
        
        duration = self.completed_at - self.started_at
        return duration.total_seconds()


class TaskExecution(db.Model):
    """
    TaskExecution model representing a single task execution within a flow.
    
    Tracks individual task executions with their inputs, outputs, and status.
    """
    
    __tablename__ = 'task_executions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to FlowExecution
    flow_execution_id = Column(
        Integer,
        ForeignKey('flow_executions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Task information
    task_name = Column(String(100), nullable=False, index=True)
    task_description = Column(String(500), nullable=True)
    
    # Execution order within the flow
    sequence_number = Column(Integer, nullable=False)
    
    # Task status
    status = Column(
        SQLEnum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Task input and output
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    flow_execution = relationship('FlowExecution', back_populates='task_executions')
    
    def __init__(self, flow_execution_id, task_name, sequence_number, task_description=None, input_data=None):
        """
        Initialize a new TaskExecution.
        
        Args:
            flow_execution_id: ID of the parent flow execution
            task_name: Name of the task being executed
            sequence_number: Order of this task in the execution
            task_description: Optional description of the task
            input_data: Input data for the task
        """
        self.flow_execution_id = flow_execution_id
        self.task_name = task_name
        self.sequence_number = sequence_number
        self.task_description = task_description
        self.input_data = input_data or {}
        self.status = ExecutionStatus.PENDING
    
    def __repr__(self):
        """String representation of TaskExecution."""
        return f'<TaskExecution {self.id}: Task={self.task_name}, Status={self.status.value}>'
    
    def to_dict(self):
        """
        Convert TaskExecution to dictionary representation.
        
        Returns:
            Dictionary representation of the TaskExecution
        """
        return {
            'id': self.id,
            'flow_execution_id': self.flow_execution_id,
            'task_name': self.task_name,
            'task_description': self.task_description,
            'sequence_number': self.sequence_number,
            'status': self.status.value,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.get_duration_seconds()
        }
    
    def mark_running(self):
        """Mark the task execution as running."""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def mark_success(self, output_data=None):
        """
        Mark the task execution as successful.
        
        Args:
            output_data: Output data produced by the task
        """
        self.status = ExecutionStatus.SUCCESS
        self.completed_at = datetime.utcnow()
        self.output_data = output_data
    
    def mark_failure(self, error_message, error_traceback=None):
        """
        Mark the task execution as failed.
        
        Args:
            error_message: Description of the error
            error_traceback: Full traceback of the error
        """
        self.status = ExecutionStatus.FAILURE
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_traceback = error_traceback
    
    def get_duration_seconds(self):
        """
        Calculate the duration of the task execution in seconds.
        
        Returns:
            Duration in seconds or None if not completed
        """
        if not self.completed_at:
            return None
        
        duration = self.completed_at - self.started_at
        return duration.total_seconds()
