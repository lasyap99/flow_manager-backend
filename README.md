# Flow Manager - Task Execution Microservice

A Flask-based microservice for managing and executing sequential task flows with conditional logic.

## Features

-  **Generic Flow Definition**: Support any number of tasks and conditions
-  **Sequential Execution**: Tasks execute one after another with condition evaluation
-  **Conditional Routing**: Determine next task based on success/failure outcomes
-  **Persistent Storage**: All flows and executions stored in database
-  **REST API**: Complete CRUD operations and execution endpoints
-  **Detailed Logging**: Comprehensive execution tracking and error logging

### Installation

# Clone the repository
git clone <repository-url>
cd flow-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python run.py

The application will start on `http://localhost:5001`

## Project Structure
```
flow-manager/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration
│   ├── models/
│   │   ├── __init__.py          # SQLAlchemy setup
│   │   ├── flow.py              # Flow model
│   │   ├── execution.py         # Execution models
│   │   └── schemas.py           # Validation schemas
│   ├── core/
│   │   ├── __init__.py
│   │   ├── flow_engine.py       # Flow execution engine
│   │   ├── task_registry.py     # Task management
│   │   └── condition_evaluator.py
│   ├── tasks/
│   │   ├── __init__.py          # Task implementations
│   │   └── base_task.py         # Base task class
│   └── api/
│       ├── __init__.py
│       ├── flows.py             # Flow endpoints
│       ├── executions.py        # Execution endpoints
│       └── tasks.py             # Task endpoints
├── requirements.txt
├── run.py                        # Application entry point
├── .env.example                  # Environment template
└── README.md
```
## API Endpoints

#### Create Flow
```http
POST /api/flows
Content-Type: application/json

{
  "flow": {
    "id": "flow123",
    "name": "Data processing flow",
    "start_task": "task1",
    "tasks": [
      {"name": "task1", "description": "Fetch data"},
      {"name": "task2", "description": "Process data"},
      {"name": "task3", "description": "Store data"}
    ],
    "conditions": [
      {
        "name": "condition_task1_result",
        "source_task": "task1",
        "outcome": "success",
        "target_task_success": "task2",
        "target_task_failure": "end"
      }
    ]
  }
}
```

#### List Flows
```http
GET /api/flows?page=1&per_page=20&active_only=true
```

#### Get Flow
```http
GET /api/flows/{flow_id}
```

#### Update Flow
```http
PUT /api/flows/{flow_id}
Content-Type: application/json

{
  "name": "Updated flow name",
  "is_active": true
}
```

#### Delete Flow
```http
DELETE /api/flows/{flow_id}
```

#### Execute Flow
```http
POST /api/tasks/flows/{flow_id}/execute
Content-Type: application/json

{
  "input_context": {
    "source_url": "https://api.example.com/data"
  }
}
```

#### Get Execution Status
```http
GET /api/executions/{execution_id}?include_tasks=true
```

#### Get Execution Logs
```http
GET /api/executions/{execution_id}/logs
```

#### List Executions
```http
GET /api/executions?flow_id=flow123&status=completed&page=1
```

#### List Available Tasks
```http
GET /api/tasks
```

#### Get Task Details
```http
GET /api/tasks/{task_name}
```


```json
{
  "id": "unique_flow_id",
  "name": "Human readable name",
  "description": "Optional description",
  "start_task": "first_task_name",
  "tasks": [
    {
      "name": "task_name",
      "description": "Task description"
    }
  ],
  "conditions": [
    {
      "name": "condition_name",
      "description": "Condition description",
      "source_task": "task_name",
      "outcome": "success|failure|any",
      "target_task_success": "next_task_or_end",
      "target_task_failure": "error_task_or_end"
    }
  ]
}
```

## Built-in Tasks

The system comes with three example tasks:

### task1: FetchDataTask
- Simulates fetching data from a source
- Returns structured data with records
- 10% random failure rate for testing

### task2: ProcessDataTask
- Processes data from task1
- Performs calculations and transformations
- 5% random failure rate for testing

### task3: StoreDataTask
- Stores processed data
- Simulates database/file storage
- Returns storage confirmation

## Creating Custom Tasks

1. Create a new class inheriting from `BaseTask`:

```python
from app.tasks.base_task import BaseTask
from typing import Dict, Any

class MyCustomTask(BaseTask):
    def __init__(self):
        super().__init__("my_task", "My custom task description")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Your task logic here
        
        # Access data from previous tasks
        previous_data = context.get('previous_task_name', {})
        
        # Do your work
        result = do_something(previous_data)
        
        # Return result
        return {
            'status': 'success',  # or 'failure'
            'data': result,
            'error': None  # or error message if failed
        }
```

2. Register the task:

```python
from app.core.task_registry import task_registry

task_registry.register_task(MyCustomTask())
```

## Environment Configuration

Create a `.env` file:

```bash
# Flask Environment
FLASK_ENV=development
FLASK_APP=run.py
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# Secret Key
SECRET_KEY=your-secret-key-here

# Database (Development uses SQLite by default)
# DEV_DATABASE_URL=sqlite:///flow_manager_dev.db

# For Production (PostgreSQL)
# DATABASE_URL=postgresql://username:password@localhost:5432/flow_manager

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=flow_manager.log

# Execution Settings
MAX_FLOW_EXECUTION_TIME=3600
TASK_TIMEOUT=300
```

## Database Setup

The application automatically creates tables on first run. For production:

```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

## Example Usage

### 1. Create a Flow

```bash
curl -X POST http://localhost:5001/api/flows \
  -H "Content-Type: application/json" \
  -d '{
    "flow": {
      "id": "data-pipeline-001",
      "name": "Data Processing Pipeline",
      "start_task": "task1",
      "tasks": [
        {"name": "task1", "description": "Fetch data"},
        {"name": "task2", "description": "Process data"},
        {"name": "task3", "description": "Store data"}
      ],
      "conditions": [
        {
          "name": "after_fetch",
          "source_task": "task1",
          "outcome": "success",
          "target_task_success": "task2",
          "target_task_failure": "end"
        },
        {
          "name": "after_process",
          "source_task": "task2",
          "outcome": "success",
          "target_task_success": "task3",
          "target_task_failure": "end"
        }
      ]
    }
  }'
```

### 2. Execute the Flow

```bash
curl -X POST http://localhost:5001/api/tasks/flows/data-pipeline-001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_context": {
      "batch_id": "batch_001"
    }
  }'
```

### 3. Check Execution Status

```bash
curl http://localhost:5001/api/executions/1?include_tasks=true
```

## Response Examples

### Successful Flow Execution

```json
{
  "message": "Flow execution completed",
  "data": {
    "id": 1,
    "flow_id": "data-pipeline-001",
    "status": "completed",
    "total_tasks_executed": 3,
    "started_at": "2025-01-10T10:00:00",
    "completed_at": "2025-01-10T10:00:05",
    "task_executions": [
      {
        "task_name": "task1",
        "status": "success",
        "sequence_number": 1,
        "duration_seconds": 0.5
      },
      {
        "task_name": "task2",
        "status": "success",
        "sequence_number": 2,
        "duration_seconds": 0.3
      },
      {
        "task_name": "task3",
        "status": "success",
        "sequence_number": 3,
        "duration_seconds": 0.2
      }
    ]
  }
}
```

### Failed Flow Execution

```json
{
  "message": "Flow execution completed",
  "data": {
    "id": 2,
    "flow_id": "data-pipeline-001",
    "status": "failure",
    "error_message": "Failed to connect to data source",
    "error_task": "task1",
    "total_tasks_executed": 1,
    "started_at": "2025-01-10T10:05:00",
    "completed_at": "2025-01-10T10:05:01"
  }
}
```

## Testing

```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 run:app
```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5001
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "run:app"]
```

## Logging

Logs are written to:
- Console (development)
- File: `flow_manager.log` (production)

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `404`: Not Found
- `409`: Conflict (duplicate)
- `500`: Internal Server Error

### Flow Execution Process

1. User submits flow definition → Validate → Store in DB
2. User triggers execution → Create FlowExecution record
3. Flow Engine starts:
   a. Get start_task
   b. Execute task → Create TaskExecution record
   c. Evaluate condition → Determine next task
   d. Repeat until 'end' or failure
4. Mark FlowExecution as completed/failed

### Key Components

- **FlowEngine**: Orchestrates flow execution
- **TaskRegistry**: Manages available tasks
- **ConditionEvaluator**: Determines execution path
- **BaseTask**: Abstract class for all tasks


## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request


**Built with Flask, SQLAlchemy
