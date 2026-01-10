"""
API endpoints for flow execution management.
"""

from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import db
from app.models.execution import FlowExecution
from app.models.schemas import flow_execution_response_schema
import logging

executions_bp = Blueprint('executions', __name__)
logger = logging.getLogger('api.executions')


@executions_bp.route('/<int:execution_id>', methods=['GET'])
def get_execution(execution_id):
    """
    Get execution details by ID
    ---
    tags:
      - Executions
    summary: Get execution by ID
    description: Retrieve details of a specific flow execution
    parameters:
      - name: execution_id
        in: path
        type: integer
        required: true
        description: Execution ID
      - name: include_tasks
        in: query
        type: boolean
        default: false
        description: Include task execution details
    responses:
      200:
        description: Execution details
        schema:
          type: object
          properties:
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
                total_tasks_executed:
                  type: integer
                  example: 3
                started_at:
                  type: string
                  example: "2026-01-10T15:55:30.251170"
                completed_at:
                  type: string
                  example: "2026-01-10T15:55:31.400948"
      404:
        description: Execution not found
        schema:
          type: object
          properties:
            error:
              type: string
            message:
              type: string
    """
    try:
        include_tasks = request.args.get('include_tasks', 'false').lower() == 'true'
        
        execution = FlowExecution.query.filter_by(id=execution_id).first()
        
        if not execution:
            return jsonify({
                'error': 'Not Found',
                'message': f"Execution {execution_id} not found"
            }), 404
        
        return jsonify({
            'data': flow_execution_response_schema.dump(
                execution.to_dict(include_tasks=include_tasks)
            )
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting execution {execution_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@executions_bp.route('/<int:execution_id>/logs', methods=['GET'])
def get_execution_logs(execution_id):
    """
    Get detailed execution logs
    ---
    tags:
      - Executions
    summary: Get execution logs
    description: Get detailed execution logs including all task executions
    parameters:
      - name: execution_id
        in: path
        type: integer
        required: true
        description: Execution ID
    responses:
      200:
        description: Detailed execution logs with all tasks
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                id:
                  type: integer
                flow_id:
                  type: string
                status:
                  type: string
                task_executions:
                  type: array
                  items:
                    type: object
                    properties:
                      task_name:
                        type: string
                      status:
                        type: string
                      duration_seconds:
                        type: number
      404:
        description: Execution not found
    """
    try:
        execution = FlowExecution.query.filter_by(id=execution_id).first()
        
        if not execution:
            return jsonify({
                'error': 'Not Found',
                'message': f"Execution {execution_id} not found"
            }), 404
        
        return jsonify({
            'data': flow_execution_response_schema.dump(
                execution.to_dict(include_tasks=True)
            )
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting execution logs {execution_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@executions_bp.route('', methods=['GET'])
def list_executions():
    """
    List all executions
    ---
    tags:
      - Executions
    summary: List flow executions
    description: Get a paginated list of all flow executions with optional filtering
    parameters:
      - name: flow_id
        in: query
        type: string
        required: false
        description: Filter by flow ID
        example: "flow123"
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status
        enum: ["pending", "running", "success", "failure", "completed"]
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Items per page (max 100)
    responses:
      200:
        description: List of executions
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  flow_id:
                    type: string
                  status:
                    type: string
                  total_tasks_executed:
                    type: integer
                  started_at:
                    type: string
                  completed_at:
                    type: string
            pagination:
              type: object
              properties:
                page:
                  type: integer
                per_page:
                  type: integer
                total:
                  type: integer
                pages:
                  type: integer
      400:
        description: Invalid status parameter
    """
    try:
        flow_id = request.args.get('flow_id')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = FlowExecution.query
        
        if flow_id:
            query = query.filter_by(flow_id=flow_id)
        
        if status:
            from app.models.execution import ExecutionStatus
            try:
                status_enum = ExecutionStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({
                    'error': 'Bad Request',
                    'message': f"Invalid status: {status}"
                }), 400
        
        # Order by most recent first
        query = query.order_by(FlowExecution.started_at.desc())
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        executions = [
            flow_execution_response_schema.dump(execution.to_dict())
            for execution in pagination.items
        ]
        
        return jsonify({
            'data': executions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing executions: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500