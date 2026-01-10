"""
Base task class for all tasks in the flow manager.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging


class BaseTask(ABC):
    """
    Abstract base class for all tasks.
    
    All tasks must inherit from this class and implement the execute method.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize base task.
        
        Args:
            name: Task name
            description: Task description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"task.{name}")
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task logic.
        
        Args:
            context: Dictionary containing data from previous tasks and input
        
        Returns:
            Dictionary with:
                - status: 'success' or 'failure'
                - data: Output data (optional)
                - error: Error message if status is 'failure' (optional)
        """
        pass
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper method that handles logging and error catching.
        
        Args:
            context: Execution context
        
        Returns:
            Task execution result
        """
        self.logger.info(f"Starting task: {self.name}")
        
        try:
            result = self.execute(context)
            
            # Ensure result has required fields
            if 'status' not in result:
                result['status'] = 'success'
            
            self.logger.info(f"Task {self.name} completed with status: {result['status']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Task {self.name} failed with error: {str(e)}", exc_info=True)
            return {
                'status': 'failure',
                'error': str(e)
            }
    
    def validate_input(self, context: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate that required keys exist in context.
        
        Args:
            context: Execution context
            required_keys: List of required keys
        
        Returns:
            True if all required keys present, False otherwise
        """
        for key in required_keys:
            if key not in context:
                self.logger.error(f"Missing required key in context: {key}")
                return False
        return True
