"""
Condition evaluator for determining flow execution paths.
"""

from typing import Dict, Any, Optional
import logging


class ConditionEvaluator:
    """
    Evaluates conditions to determine the next task in a flow.
    """
    
    def __init__(self):
        """Initialize condition evaluator."""
        self.logger = logging.getLogger('ConditionEvaluator')
    
    def evaluate(self, condition: Dict[str, Any], task_result: Dict[str, Any]) -> str:
        """
        Evaluate a condition based on task result.
        
        Args:
            condition: Condition definition containing:
                - source_task: Name of the task that was executed
                - outcome: Expected outcome ('success', 'failure', 'any')
                - target_task_success: Next task if condition matches
                - target_task_failure: Next task if condition doesn't match
            task_result: Result from task execution containing:
                - status: 'success' or 'failure'
                - data: Optional output data
                - error: Optional error message
        
        Returns:
            Name of next task to execute, or 'end' to terminate flow
        """
        expected_outcome = condition.get('outcome', 'success')
        actual_status = task_result.get('status', 'failure')
        
        self.logger.debug(
            f"Evaluating condition: expected={expected_outcome}, actual={actual_status}"
        )
        
        # Check if outcome matches
        if self._outcome_matches(expected_outcome, actual_status):
            next_task = condition.get('target_task_success', 'end')
            self.logger.info(f"Condition matched, proceeding to: {next_task}")
            return next_task
        else:
            next_task = condition.get('target_task_failure', 'end')
            self.logger.info(f"Condition not matched, proceeding to: {next_task}")
            return next_task
    
    def _outcome_matches(self, expected: str, actual: str) -> bool:
        """
        Check if actual outcome matches expected outcome.
        
        Args:
            expected: Expected outcome ('success', 'failure', 'any')
            actual: Actual task status ('success', 'failure')
        
        Returns:
            True if outcomes match, False otherwise
        """
        if expected == 'any':
            return True
        return expected == actual
    
    def find_condition_for_task(
        self,
        task_name: str,
        conditions: list
    ) -> Optional[Dict[str, Any]]:
        """
        Find the condition for a specific source task.
        
        Args:
            task_name: Name of the source task
            conditions: List of condition definitions
        
        Returns:
            Condition dictionary or None if not found
        """
        for condition in conditions:
            if condition.get('source_task') == task_name:
                return condition
        
        self.logger.warning(f"No condition found for task: {task_name}")
        return None
    
    def validate_condition(self, condition: Dict[str, Any]) -> tuple:
        """
        Validate a condition definition.
        
        Args:
            condition: Condition dictionary to validate
        
        Returns:
            Tuple of (is_valid: bool, error_message: str or None)
        """
        required_fields = [
            'source_task',
            'outcome',
            'target_task_success',
            'target_task_failure'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in condition:
                return False, f"Missing required field: {field}"
        
        # Validate outcome value
        valid_outcomes = ['success', 'failure', 'any']
        if condition['outcome'] not in valid_outcomes:
            return False, f"Invalid outcome: {condition['outcome']}, must be one of {valid_outcomes}"
        
        return True, None
