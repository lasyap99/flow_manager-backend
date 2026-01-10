"""
Flow model - represents flow definitions in the system.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.models import db


class Flow(db.Model):
    """
    Flow model representing a flow definition.
    
    A flow consists of tasks and conditions that determine the execution path.
    """
    
    __tablename__ = 'flows'
    
    # Primary key
    id = Column(String(100), primary_key=True, nullable=False)
    
    # Flow metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    start_task = Column(String(100), nullable=False)
    
    # Flow definition stored as JSON
    # Contains: tasks list, conditions list, and other configuration
    definition = Column(JSON, nullable=False)
    
    # Status and versioning
    is_active = Column(Integer, default=1, nullable=False)  # 1 for active, 0 for inactive
    version = Column(Integer, default=1, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    executions = relationship('FlowExecution', back_populates='flow', cascade='all, delete-orphan')
    
    def __init__(self, id, name, start_task, definition, description=None):
        """
        Initialize a new Flow.
        
        Args:
            id: Unique identifier for the flow
            name: Human-readable name for the flow
            start_task: Name of the first task to execute
            definition: Complete flow definition as dictionary
            description: Optional description of the flow
        """
        self.id = id
        self.name = name
        self.start_task = start_task
        self.definition = definition
        self.description = description
    
    def __repr__(self):
        """String representation of Flow."""
        return f'<Flow {self.id}: {self.name}>'
    
    def to_dict(self, include_definition=True):
        """
        Convert Flow to dictionary representation.
        
        Args:
            include_definition: Whether to include the full definition JSON
        
        Returns:
            Dictionary representation of the Flow
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'start_task': self.start_task,
            'is_active': bool(self.is_active),
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_definition:
            data['definition'] = self.definition
        
        return data
    
    def get_task_by_name(self, task_name):
        """
        Get a task definition by name from the flow definition.
        
        Args:
            task_name: Name of the task to retrieve
        
        Returns:
            Task dictionary or None if not found
        """
        if not self.definition or 'tasks' not in self.definition:
            return None
        
        for task in self.definition['tasks']:
            if task.get('name') == task_name:
                return task
        
        return None
    
    def get_conditions_for_task(self, task_name):
        """
        Get all conditions where the given task is the source.
        
        Args:
            task_name: Name of the source task
        
        Returns:
            List of condition dictionaries
        """
        if not self.definition or 'conditions' not in self.definition:
            return []
        
        return [
            condition for condition in self.definition['conditions']
            if condition.get('source_task') == task_name
        ]
    
    def get_all_task_names(self):
        """
        Get list of all task names in the flow.
        
        Returns:
            List of task names
        """
        if not self.definition or 'tasks' not in self.definition:
            return []
        
        return [task.get('name') for task in self.definition['tasks'] if task.get('name')]
    
    def validate_flow_structure(self):
        """
        Validate the flow structure for basic consistency.
        
        Returns:
            Tuple (is_valid: bool, errors: list)
        """
        errors = []
        
        # Check if definition exists
        if not self.definition:
            errors.append("Flow definition is missing")
            return False, errors
        
        # Check if tasks exist
        if 'tasks' not in self.definition or not self.definition['tasks']:
            errors.append("Flow must contain at least one task")
            return False, errors
        
        task_names = self.get_all_task_names()
        
        # Check if start_task exists in tasks
        if self.start_task not in task_names:
            errors.append(f"Start task '{self.start_task}' not found in tasks list")
        
        # Check for duplicate task names
        if len(task_names) != len(set(task_names)):
            errors.append("Duplicate task names found in flow definition")
        
        # Validate conditions if present
        if 'conditions' in self.definition:
            for idx, condition in enumerate(self.definition['conditions']):
                source = condition.get('source_task')
                target_success = condition.get('target_task_success')
                target_failure = condition.get('target_task_failure')
                
                # Check if source task exists
                if source and source not in task_names:
                    errors.append(f"Condition {idx}: source_task '{source}' not found in tasks")
                
                # Check if target tasks exist (unless it's 'end')
                if target_success and target_success != 'end' and target_success not in task_names:
                    errors.append(f"Condition {idx}: target_task_success '{target_success}' not found in tasks")
                
                if target_failure and target_failure != 'end' and target_failure not in task_names:
                    errors.append(f"Condition {idx}: target_task_failure '{target_failure}' not found in tasks")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def create_from_json(flow_json):
        """
        Create a Flow instance from JSON definition.
        
        Args:
            flow_json: Dictionary containing flow definition
        
        Returns:
            Flow instance
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['id', 'name', 'start_task']
        for field in required_fields:
            if field not in flow_json:
                raise ValueError(f"Missing required field: {field}")
        
        return Flow(
            id=flow_json['id'],
            name=flow_json['name'],
            start_task=flow_json['start_task'],
            definition=flow_json,
            description=flow_json.get('description')
        )
