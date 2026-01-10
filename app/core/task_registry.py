"""
Task registry for managing available tasks in the flow manager.
"""

from typing import Dict, Optional
from app.tasks.base_task import BaseTask
import logging


class TaskRegistry:
    """
    Singleton registry for managing task instances.
    
    Allows dynamic registration and retrieval of tasks.
    """
    
    _instance = None
    _tasks: Dict[str, BaseTask] = {}
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(TaskRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize registry if not already initialized."""
        if not self._initialized:
            self.logger = logging.getLogger('TaskRegistry')
            self._initialized = True
            self._register_default_tasks()
    
    def _register_default_tasks(self):
        """Register default tasks on initialization."""
        from app.tasks import FetchDataTask, ProcessDataTask, StoreDataTask
        
        self.register_task(FetchDataTask())
        self.register_task(ProcessDataTask())
        self.register_task(StoreDataTask())
        
        self.logger.info(f"Registered {len(self._tasks)} default tasks")
    
    def register_task(self, task: BaseTask) -> None:
        """
        Register a task in the registry.
        
        Args:
            task: Task instance to register
        
        Raises:
            ValueError: If task with same name already exists
        """
        if not isinstance(task, BaseTask):
            raise ValueError(f"Task must be an instance of BaseTask, got {type(task)}")
        
        if task.name in self._tasks:
            self.logger.warning(f"Task '{task.name}' already registered, overwriting")
        
        self._tasks[task.name] = task
        self.logger.info(f"Registered task: {task.name}")
    
    def get_task(self, task_name: str) -> Optional[BaseTask]:
        """
        Get a task by name.
        
        Args:
            task_name: Name of the task to retrieve
        
        Returns:
            Task instance or None if not found
        """
        task = self._tasks.get(task_name)
        if task is None:
            self.logger.warning(f"Task '{task_name}' not found in registry")
        return task
    
    def list_tasks(self) -> Dict[str, str]:
        """
        List all registered tasks.
        
        Returns:
            Dictionary mapping task names to descriptions
        """
        return {
            name: task.description
            for name, task in self._tasks.items()
        }
    
    def task_exists(self, task_name: str) -> bool:
        """
        Check if a task exists in the registry.
        
        Args:
            task_name: Name of the task
        
        Returns:
            True if task exists, False otherwise
        """
        return task_name in self._tasks
    
    def unregister_task(self, task_name: str) -> bool:
        """
        Remove a task from the registry.
        
        Args:
            task_name: Name of the task to remove
        
        Returns:
            True if task was removed, False if not found
        """
        if task_name in self._tasks:
            del self._tasks[task_name]
            self.logger.info(f"Unregistered task: {task_name}")
            return True
        return False
    
    def clear_registry(self):
        """Clear all tasks from registry. Useful for testing."""
        self._tasks.clear()
        self.logger.info("Cleared task registry")
    
    def get_task_count(self) -> int:
        """Get total number of registered tasks."""
        return len(self._tasks)


# Create global registry instance
task_registry = TaskRegistry()
