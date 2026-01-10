"""
Example task implementations for the flow manager.
"""

from app.tasks.base_task import BaseTask
from typing import Dict, Any
import random
import time


class FetchDataTask(BaseTask):
    """
    Task 1: Fetch data from a source.
    Simulates data fetching with a simple implementation.
    """
    
    def __init__(self):
        super().__init__("task1", "Fetch data from source")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate fetching data.
        
        In a real implementation, this would fetch from:
        - Database
        - API endpoint
        - File system
        - Message queue
        """
        self.logger.info("Fetching data from source...")
        
        # Simulate some processing time
        time.sleep(0.5)
        
        # Simulate fetching data
        # In real scenario, you might fetch from context['source_url'] or similar
        fetched_data = {
            'records': [
                {'id': 1, 'value': 100},
                {'id': 2, 'value': 200},
                {'id': 3, 'value': 300}
            ],
            'total_count': 3,
            'fetch_timestamp': time.time()
        }
        
        # Simulate occasional failures (10% chance)
        if random.random() < 0.1:
            return {
                'status': 'failure',
                'error': 'Failed to connect to data source'
            }
        
        return {
            'status': 'success',
            'data': fetched_data
        }


class ProcessDataTask(BaseTask):
    """
    Task 2: Process the fetched data.
    Performs transformations on the data.
    """
    
    def __init__(self):
        super().__init__("task2", "Process and transform data")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data from previous task.
        
        Expects 'task1' data in context.
        """
        self.logger.info("Processing data...")
        
        # Check if we have data from task1
        if 'task1' not in context or 'data' not in context['task1']:
            return {
                'status': 'failure',
                'error': 'No data from task1 to process'
            }
        
        task1_data = context['task1']['data']
        
        # Simulate processing time
        time.sleep(0.3)
        
        # Process the data (e.g., calculate sum, average, filter)
        records = task1_data.get('records', [])
        
        processed_data = {
            'total_value': sum(record['value'] for record in records),
            'average_value': sum(record['value'] for record in records) / len(records) if records else 0,
            'record_count': len(records),
            'processed_records': [
                {
                    'id': record['id'],
                    'value': record['value'],
                    'doubled_value': record['value'] * 2,
                    'category': 'high' if record['value'] > 150 else 'low'
                }
                for record in records
            ]
        }
        
        # Simulate occasional failures (5% chance)
        if random.random() < 0.05:
            return {
                'status': 'failure',
                'error': 'Data processing failed due to invalid format'
            }
        
        return {
            'status': 'success',
            'data': processed_data
        }


class StoreDataTask(BaseTask):
    """
    Task 3: Store the processed data.
    Persists data to storage.
    """
    
    def __init__(self):
        super().__init__("task3", "Store processed data")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store processed data.
        
        Expects 'task2' data in context.
        In a real implementation, this would store to:
        - Database
        - File system
        - Cloud storage
        - Another API
        """
        self.logger.info("Storing data...")
        
        # Check if we have data from task2
        if 'task2' not in context or 'data' not in context['task2']:
            return {
                'status': 'failure',
                'error': 'No processed data from task2 to store'
            }
        
        task2_data = context['task2']['data']
        
        # Simulate storage time
        time.sleep(0.2)
        
        # Simulate storing data
        # In real scenario, you would do: db.session.add(data) or write to file
        stored_info = {
            'storage_id': f"store_{int(time.time())}",
            'records_stored': task2_data.get('record_count', 0),
            'storage_location': '/data/processed/output.json',
            'storage_timestamp': time.time()
        }
        
        self.logger.info(f"Successfully stored {stored_info['records_stored']} records")
        
        return {
            'status': 'success',
            'data': stored_info
        }


# Additional example tasks for demonstration

class ValidateDataTask(BaseTask):
    """Example validation task."""
    
    def __init__(self):
        super().__init__("validate_data", "Validate input data")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data meets requirements."""
        # Example validation logic
        return {
            'status': 'success',
            'data': {'validation_passed': True}
        }


class SendNotificationTask(BaseTask):
    """Example notification task."""
    
    def __init__(self):
        super().__init__("send_notification", "Send completion notification")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification about flow completion."""
        # Example notification logic
        self.logger.info("Sending notification...")
        return {
            'status': 'success',
            'data': {'notification_sent': True}
        }
