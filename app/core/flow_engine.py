"""
Flow engine - Core execution logic for running flows.
"""

from typing import Dict, Any, Optional
from app.core.task_registry import task_registry
from app.core.condition_evaluator import ConditionEvaluator
from app.models import db, FlowExecution, TaskExecution, ExecutionStatus
from app.models.flow import Flow
import logging
import traceback


class FlowEngine:
    """
    Main engine for executing flows.
    
    Orchestrates task execution based on flow definition and conditions.
    """
    
    def __init__(self):
        """Initialize flow engine."""
        self.task_registry = task_registry
        self.condition_evaluator = ConditionEvaluator()
        self.logger = logging.getLogger('FlowEngine')
    
    def execute_flow(
        self,
        flow: Flow,
        input_context: Optional[Dict[str, Any]] = None
    ) -> FlowExecution:
        """
        Execute a complete flow.
        
        Args:
            flow: Flow model instance
            input_context: Initial context data for the flow
        
        Returns:
            FlowExecution instance with execution results
        """
        # Create flow execution record
        flow_execution = FlowExecution(
            flow_id=flow.id,
            input_context=input_context or {}
        )
        db.session.add(flow_execution)
        db.session.commit()
        
        self.logger.info(f"Starting flow execution {flow_execution.id} for flow {flow.id}")
        
        try:
            # Mark as running
            flow_execution.mark_running()
            db.session.commit()
            
            # Initialize execution context
            context = input_context.copy() if input_context else {}
            
            # Start execution loop
            current_task_name = flow.start_task
            sequence_number = 1
            
            while current_task_name != 'end':
                # Execute current task
                task_result = self._execute_task(
                    flow_execution,
                    flow,
                    current_task_name,
                    context,
                    sequence_number
                )
                
                # Update execution counter
                flow_execution.total_tasks_executed = sequence_number
                db.session.commit()
                
                # Check if task failed and no condition exists
                conditions = flow.get_conditions_for_task(current_task_name)
                
                if not conditions:
                    # No conditions defined, end flow
                    if task_result.get('status') == 'failure':
                        flow_execution.mark_failed(
                            task_result.get('error', 'Task failed'),
                            current_task_name
                        )
                    else:
                        flow_execution.mark_completed(context)
                    db.session.commit()
                    break
                
                # Evaluate conditions to get next task
                condition = conditions[0]  # Use first condition for the task
                next_task_name = self.condition_evaluator.evaluate(
                    condition,
                    task_result
                )
                
                self.logger.info(
                    f"Task {current_task_name} completed with status {task_result.get('status')}, "
                    f"next task: {next_task_name}"
                )
                
                # Check if we should end
                if next_task_name == 'end':
                    if task_result.get('status') == 'failure':
                        flow_execution.mark_failed(
                            task_result.get('error', 'Flow ended due to task failure'),
                            current_task_name
                        )
                    else:
                        flow_execution.mark_completed(context)
                    db.session.commit()
                    break
                
                # Move to next task
                current_task_name = next_task_name
                sequence_number += 1
            
            self.logger.info(f"Flow execution {flow_execution.id} completed successfully")
            
        except Exception as e:
            self.logger.error(
                f"Flow execution {flow_execution.id} failed with error: {str(e)}",
                exc_info=True
            )
            flow_execution.mark_failed(str(e))
            db.session.commit()
        
        return flow_execution
    
    def _execute_task(
        self,
        flow_execution: FlowExecution,
        flow: Flow,
        task_name: str,
        context: Dict[str, Any],
        sequence_number: int
    ) -> Dict[str, Any]:
        """
        Execute a single task and record its execution.
        
        Args:
            flow_execution: Parent flow execution
            flow: Flow definition
            task_name: Name of task to execute
            context: Current execution context
            sequence_number: Order of this task in the flow
        
        Returns:
            Task execution result dictionary
        """
        # Get task definition from flow
        task_def = flow.get_task_by_name(task_name)
        
        if not task_def:
            error_msg = f"Task '{task_name}' not found in flow definition"
            self.logger.error(error_msg)
            return {
                'status': 'failure',
                'error': error_msg
            }
        
        # Get task implementation from registry
        task = self.task_registry.get_task(task_name)
        
        if not task:
            error_msg = f"Task '{task_name}' not found in task registry"
            self.logger.error(error_msg)
            return {
                'status': 'failure',
                'error': error_msg
            }
        
        # Create task execution record
        task_execution = TaskExecution(
            flow_execution_id=flow_execution.id,
            task_name=task_name,
            sequence_number=sequence_number,
            task_description=task_def.get('description'),
            input_data=context.copy()
        )
        db.session.add(task_execution)
        db.session.commit()
        
        try:
            # Mark as running
            task_execution.mark_running()
            db.session.commit()
            
            # Execute the task
            self.logger.info(f"Executing task: {task_name}")
            result = task.run(context)
            
            # Update context with task result
            context[task_name] = result
            
            # Mark as success or failure
            if result.get('status') == 'success':
                task_execution.mark_success(result.get('data'))
            else:
                task_execution.mark_failure(
                    result.get('error', 'Task failed without error message')
                )
            
            db.session.commit()
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            self.logger.error(
                f"Task {task_name} execution failed: {error_msg}",
                exc_info=True
            )
            
            task_execution.mark_failure(error_msg, error_trace)
            db.session.commit()
            
            return {
                'status': 'failure',
                'error': error_msg
            }
    
    def validate_flow_executable(self, flow: Flow) -> tuple:
        """
        Validate that a flow can be executed.
        
        Args:
            flow: Flow to validate
        
        Returns:
            Tuple of (is_valid: bool, errors: list)
        """
        errors = []
        
        # Validate flow structure
        is_valid, structure_errors = flow.validate_flow_structure()
        if not is_valid:
            errors.extend(structure_errors)
        
        # Check if all tasks exist in registry
        task_names = flow.get_all_task_names()
        for task_name in task_names:
            if not self.task_registry.task_exists(task_name):
                errors.append(
                    f"Task '{task_name}' not found in task registry"
                )
        
        return len(errors) == 0, errors
