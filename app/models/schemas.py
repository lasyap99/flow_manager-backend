
"""
Schemas for request/response validation and serialization.
Uses Marshmallow for robust validation and serialization.
"""

from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError, post_load


class TaskSchema(Schema):
    """Schema for validating task definitions within a flow."""
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False, allow_none=True, validate=validate.Length(max=500))
    config = fields.Dict(required=False, allow_none=True)
    
    class Meta:
        """Meta options."""
        ordered = True


class ConditionSchema(Schema):
    """Schema for validating condition definitions within a flow."""
    
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False, allow_none=True, validate=validate.Length(max=500))
    source_task = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    outcome = fields.Str(
        required=True,
        validate=validate.OneOf(['success', 'failure', 'any'])
    )
    target_task_success = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    target_task_failure = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    
    class Meta:
        """Meta options."""
        ordered = True


class FlowDefinitionSchema(Schema):
    """Schema for validating complete flow definitions."""
    
    id = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(required=False, allow_none=True, validate=validate.Length(max=1000))
    start_task = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    tasks = fields.List(fields.Nested(TaskSchema), required=True, validate=validate.Length(min=1))
    conditions = fields.List(fields.Nested(ConditionSchema), required=False, allow_none=True)
    
    @validates('tasks')
    def validate_tasks(self, tasks):
        """Validate that task names are unique."""
        task_names = [task['name'] for task in tasks]
        if len(task_names) != len(set(task_names)):
            raise ValidationError('Task names must be unique within a flow')
    
    @validates_schema
    def validate_flow_structure(self, data, **kwargs):
        """Validate the overall flow structure."""
        tasks = data.get('tasks', [])
        task_names = [task['name'] for task in tasks]
        start_task = data.get('start_task')
        conditions = data.get('conditions', [])
        
        if start_task not in task_names:
            raise ValidationError(
                f"start_task '{start_task}' must be one of the defined tasks",
                field_name='start_task'
            )
        
        for idx, condition in enumerate(conditions):
            source = condition.get('source_task')
            target_success = condition.get('target_task_success')
            target_failure = condition.get('target_task_failure')
            
            if source not in task_names:
                raise ValidationError(
                    f"Condition {idx}: source_task '{source}' not found in tasks",
                    field_name='conditions'
                )
            
            if target_success != 'end' and target_success not in task_names:
                raise ValidationError(
                    f"Condition {idx}: target_task_success '{target_success}' must be 'end' or a valid task",
                    field_name='conditions'
                )
            
            if target_failure != 'end' and target_failure not in task_names:
                raise ValidationError(
                    f"Condition {idx}: target_task_failure '{target_failure}' must be 'end' or a valid task",
                    field_name='conditions'
                )
    
    class Meta:
        """Meta options."""
        ordered = True


class FlowCreateRequestSchema(Schema):
    """Schema for creating a new flow via API."""
    
    flow = fields.Nested(FlowDefinitionSchema, required=True)
    
    class Meta:
        """Meta options."""
        ordered = True


class FlowUpdateRequestSchema(Schema):
    """Schema for updating an existing flow."""
    
    name = fields.Str(required=False, validate=validate.Length(min=1, max=255))
    description = fields.Str(required=False, allow_none=True, validate=validate.Length(max=1000))
    start_task = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    tasks = fields.List(fields.Nested(TaskSchema), required=False)
    conditions = fields.List(fields.Nested(ConditionSchema), required=False)
    is_active = fields.Bool(required=False)
    
    class Meta:
        """Meta options."""
        ordered = True


class FlowResponseSchema(Schema):
    """Schema for flow response data."""
    
    id = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    start_task = fields.Str()
    is_active = fields.Bool()
    version = fields.Int()
    created_at = fields.Str()
    updated_at = fields.Str()
    definition = fields.Dict(required=False)
    
    class Meta:
        """Meta options."""
        ordered = True


class FlowExecutionRequestSchema(Schema):
    """Schema for starting a flow execution."""
    
    input_context = fields.Dict(required=False, allow_none=True)
    
    @validates('input_context')
    def validate_input_context(self, value):
        """Validate input context is a valid dictionary."""
        if value is not None and not isinstance(value, dict):
            raise ValidationError('input_context must be a dictionary')
    
    class Meta:
        """Meta options."""
        ordered = True


class TaskExecutionResponseSchema(Schema):
    """Schema for task execution response."""
    
    id = fields.Int()
    flow_execution_id = fields.Int()
    task_name = fields.Str()
    task_description = fields.Str(allow_none=True)
    sequence_number = fields.Int()
    status = fields.Str()
    input_data = fields.Dict(allow_none=True)
    output_data = fields.Dict(allow_none=True)
    error_message = fields.Str(allow_none=True)
    started_at = fields.Str()
    completed_at = fields.Str(allow_none=True)
    duration_seconds = fields.Float(allow_none=True)
    
    class Meta:
        """Meta options."""
        ordered = True


class FlowExecutionResponseSchema(Schema):
    """Schema for flow execution response."""
    
    id = fields.Int()
    flow_id = fields.Str()
    status = fields.Str()
    input_context = fields.Dict(allow_none=True)
    output_data = fields.Dict(allow_none=True)
    error_message = fields.Str(allow_none=True)
    error_task = fields.Str(allow_none=True)
    total_tasks_executed = fields.Int()
    started_at = fields.Str()
    completed_at = fields.Str(allow_none=True)
    task_executions = fields.List(
        fields.Nested(TaskExecutionResponseSchema),
        required=False
    )
    
    class Meta:
        """Meta options."""
        ordered = True


class PaginationSchema(Schema):
    """Schema for pagination parameters."""
    
    page = fields.Int(required=False, load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(required=False, load_default=20, validate=validate.Range(min=1, max=100))
    
    class Meta:
        """Meta options."""
        ordered = True


class ErrorResponseSchema(Schema):
    """Schema for error responses."""
    
    error = fields.Str(required=True)
    message = fields.Str(required=True)
    details = fields.Dict(required=False, allow_none=True)
    timestamp = fields.Str(required=False)
    
    class Meta:
        """Meta options."""
        ordered = True


class SuccessResponseSchema(Schema):
    """Schema for success responses."""
    
    message = fields.Str(required=True)
    data = fields.Dict(required=False, allow_none=True)
    
    class Meta:
        """Meta options."""
        ordered = True


# Create schema instances for reuse
flow_definition_schema = FlowDefinitionSchema()
flow_create_request_schema = FlowCreateRequestSchema()
flow_update_request_schema = FlowUpdateRequestSchema()
flow_response_schema = FlowResponseSchema()
flow_execution_request_schema = FlowExecutionRequestSchema()
flow_execution_response_schema = FlowExecutionResponseSchema()
task_execution_response_schema = TaskExecutionResponseSchema()
pagination_schema = PaginationSchema()
error_response_schema = ErrorResponseSchema()
success_response_schema = SuccessResponseSchema()
