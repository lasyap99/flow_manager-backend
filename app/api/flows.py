"""
API endpoints for flow management.
"""

from flask import Blueprint, request, jsonify
from flasgger import swag_from
from marshmallow import ValidationError
from app.models import db
from app.models.flow import Flow
from app.models.schemas import (
    flow_create_request_schema,
    flow_update_request_schema,
    flow_response_schema
)
from app.core.flow_engine import FlowEngine
import logging

flows_bp = Blueprint('flows', __name__)
logger = logging.getLogger('api.flows')


@flows_bp.route('', methods=['POST'])
def create_flow():
    """
    Create a new flow
    ---
    tags:
      - Flows
    summary: Create a new flow definition
    description: Creates a new flow with tasks and conditions
    parameters:
      - in: body
        name: body
        description: Flow definition
        required: true
        schema:
          type: object
          required:
            - flow
          properties:
            flow:
              type: object
              required:
                - id
                - name
                - start_task
                - tasks
              properties:
                id:
                  type: string
                  example: "flow123"
                name:
                  type: string
                  example: "Data processing flow"
                description:
                  type: string
                  example: "Sample flow for data processing"
                start_task:
                  type: string
                  example: "task1"
                tasks:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      description:
                        type: string
                  example:
                    - name: "task1"
                      description: "Fetch data"
                    - name: "task2"
                      description: "Process data"
                conditions:
                  type: array
                  items:
                    type: object
    responses:
      201:
        description: Flow created successfully
        schema:
          type: object
          properties:
            message:
              type: string
            data:
              type: object
      400:
        description: Validation error
      409:
        description: Flow already exists
    """
    try:
        data = flow_create_request_schema.load(request.json)
        flow_data = data['flow']
        
        existing_flow = Flow.query.filter_by(id=flow_data['id']).first()
        if existing_flow:
            return jsonify({
                'error': 'Conflict',
                'message': f"Flow with id '{flow_data['id']}' already exists"
            }), 409
        
        flow = Flow.create_from_json(flow_data)
        
        flow_engine = FlowEngine()
        is_valid, errors = flow_engine.validate_flow_executable(flow)
        
        if not is_valid:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Flow validation failed',
                'details': errors
            }), 400
        
        db.session.add(flow)
        db.session.commit()
        
        logger.info(f"Created flow: {flow.id}")
        
        return jsonify({
            'message': 'Flow created successfully',
            'data': flow_response_schema.dump(flow.to_dict())
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid request data',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error creating flow: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@flows_bp.route('', methods=['GET'])
def list_flows():
    """
    List all flows
    ---
    tags:
      - Flows
    summary: List all flows
    description: Get a paginated list of all flows
    parameters:
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
      - name: active_only
        in: query
        type: boolean
        default: false
        description: Filter active flows only
    responses:
      200:
        description: List of flows
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
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
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        query = Flow.query
        
        if active_only:
            query = query.filter_by(is_active=1)
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        flows = [flow.to_dict(include_definition=False) for flow in pagination.items]
        
        return jsonify({
            'data': flows,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing flows: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@flows_bp.route('/<flow_id>', methods=['GET'])
def get_flow(flow_id):
    """
    Get a specific flow
    ---
    tags:
      - Flows
    summary: Get flow by ID
    description: Retrieve a specific flow definition by its ID
    parameters:
      - name: flow_id
        in: path
        type: string
        required: true
        description: Flow ID
    responses:
      200:
        description: Flow details
        schema:
          type: object
          properties:
            data:
              type: object
      404:
        description: Flow not found
    """
    try:
        flow = Flow.query.filter_by(id=flow_id).first()
        
        if not flow:
            return jsonify({
                'error': 'Not Found',
                'message': f"Flow '{flow_id}' not found"
            }), 404
        
        return jsonify({
            'data': flow_response_schema.dump(flow.to_dict())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting flow {flow_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@flows_bp.route('/<flow_id>', methods=['PUT'])
def update_flow(flow_id):
    """
    Update a flow
    ---
    tags:
      - Flows
    summary: Update flow
    description: Update an existing flow's properties
    parameters:
      - name: flow_id
        in: path
        type: string
        required: true
        description: Flow ID
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            is_active:
              type: boolean
    responses:
      200:
        description: Flow updated successfully
      404:
        description: Flow not found
    """
    try:
        flow = Flow.query.filter_by(id=flow_id).first()
        
        if not flow:
            return jsonify({
                'error': 'Not Found',
                'message': f"Flow '{flow_id}' not found"
            }), 404
        
        data = flow_update_request_schema.load(request.json)
        
        if 'name' in data:
            flow.name = data['name']
        if 'description' in data:
            flow.description = data['description']
        if 'is_active' in data:
            flow.is_active = 1 if data['is_active'] else 0
        
        flow.version += 1
        
        db.session.commit()
        
        logger.info(f"Updated flow: {flow.id}")
        
        return jsonify({
            'message': 'Flow updated successfully',
            'data': flow_response_schema.dump(flow.to_dict())
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid request data',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error updating flow {flow_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500


@flows_bp.route('/<flow_id>', methods=['DELETE'])
def delete_flow(flow_id):
    """
    Delete a flow
    ---
    tags:
      - Flows
    summary: Delete flow
    description: Delete a flow and all its executions
    parameters:
      - name: flow_id
        in: path
        type: string
        required: true
        description: Flow ID
    responses:
      200:
        description: Flow deleted successfully
      404:
        description: Flow not found
    """
    try:
        flow = Flow.query.filter_by(id=flow_id).first()
        
        if not flow:
            return jsonify({
                'error': 'Not Found',
                'message': f"Flow '{flow_id}' not found"
            }), 404
        
        db.session.delete(flow)
        db.session.commit()
        
        logger.info(f"Deleted flow: {flow.id}")
        
        return jsonify({
            'message': f"Flow '{flow_id}' deleted successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting flow {flow_id}: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e)
        }), 500