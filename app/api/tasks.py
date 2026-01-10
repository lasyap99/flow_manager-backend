"""
API endpoints for task management and flow execution.
"""

from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import db
from app.models.flow import Flow
from app.models.schemas import (
    flow_execution_request_schema,
    flow_execution_response_schema
)
from app.core.task_registry import task_registry
from app.core.flow_engine import FlowEngine
import logging

tasks_bp = Blueprint('tasks', __name__)
logger = logging.getLogger('api.tasks')


@tasks_bp.route('', methods=['GET'])
def list_tasks():
    """
    List all registered tasks
    ---
    tags:
      - Tasks
    summary: List available tasks
    description: Get a list of all registered tasks in the system
    responses:
      200:
        description: List of registered tasks
        schema:
          type: object
          properties:
            data:
              type: object
              additionalProperties:
                type: string
              example:
                task1: "Fetch data from source"
                task2: "Process and transform data"
                task3: "Store processed data"
            count:
              type: integer
              example: 3
    """
    try:
        tasks = task_registry.list_tasks()
        
        return jsonify({
            'data': tasks,
            'count': len(tasks)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@tasks_bp.route('/<task_name>', methods=['GET'])
def get_task(task_name):
    """
    Get task details
    ---
    tags:
      - Tasks
    summary: Get task by name
    description: Retrieve details of a specific task
    parameters:
      - name: task_name
        in: path
        type: string
        required: true
        description: Task name
        example: "task1"
    responses:
      200:
        description: Task details
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                name:
                  type: string
                  example: "task1"
                description:
                  type: string
                  example: "Fetch data from source"
      404:
        description: Task not found
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        task = task_registry.get_task(task_name)
        
        if not task:
            return jsonify({
                'error': 'Not Found',
                'message': f"Task '{task_name}' not found"
            }), 404
        
        return jsonify({
            'data': {
                'name': task.name,
                'description': task.description
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting task {task_name}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@tasks_bp.route('/flows/<flow_id>/execute', methods=['POST'])
def execute_flow(flow_id):
    """
    Execute a flow
    ---
    tags:
      - Flow Execution
    summary: Execute a flow
    description: Start execution of a flow with optional input context. The flow will execute all tasks sequentially based on defined conditions.
    parameters:
      - name: flow_id
        in: path
        type: string
        required: true
        description: Flow ID to execute
        example: "flow123"
      - in: body
        name: body
        description: Execution parameters
        required: false
        schema:
          type: object
          properties:
            input_context:
              type: object
              description: Optional input data for the flow execution
              example:
                batch_id: "batch_001"
                source: "API"
                user_id: "user123"
    responses:
      200:
        description: Flow execution completed
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Flow execution completed"
            data:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                flow_id:
                  type: string
                  example: "flow123"
                status:
                  type: string
                  example: "completed"
                  enum: ["pending", "running", "completed", "failure"]
                total_tasks_executed:
                  type: integer
                  example: 3
                started_at:
                  type: string
                  format: date-time
                  example: "2026-01-10T21:55:30.251170"
                completed_at:
                  type: string
                  format: date-time
                  example: "2026-01-10T21:55:31.400948"
                input_context:
                  type: object
                output_data:
                  type: object
                task_executions:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      task_name:
                        type: string
                        example: "task1"
                      task_description:
                        type: string
                        example: "Fetch data"
                      status:
                        type: string
                        example: "success"
                      sequence_number:
                        type: integer
                        example: 1
                      duration_seconds:
                        type: number
                        format: float
                        example: 0.51
                      output_data:
                        type: object
      400:
        description: Flow not active or validation error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Bad Request"
            message:
              type: string
              example: "Flow 'flow123' is not active"
      404:
        description: Flow not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Not Found"
            message:
              type: string
              example: "Flow 'flow123' not found"
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        # Get the flow
        flow = Flow.query.filter_by(id=flow_id).first()
        
        if not flow:
            return jsonify({
                'error': 'Not Found',
                'message': f"Flow '{flow_id}' not found"
            }), 404
        
        # Check if flow is active
        if not flow.is_active:
            return jsonify({
                'error': 'Bad Request',
                'message': f"Flow '{flow_id}' is not active"
            }), 400
        
        # Validate request data
        data = flow_execution_request_schema.load(request.json or {})
        input_context = data.get('input_context', {})
        
        # Execute the flow
        flow_engine = FlowEngine()
        execution = flow_engine.execute_flow(flow, input_context)
        
        logger.info(f"Flow {flow_id} execution {execution.id} completed with status: {execution.status.value}")
        
        return jsonify({
            'message': 'Flow execution completed',
            'data': flow_execution_response_schema.dump(
                execution.to_dict(include_tasks=True)
            )
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid request data',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error executing flow {flow_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500
