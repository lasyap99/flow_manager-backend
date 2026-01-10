┌─────────────────────────────────────────────────────────────────┐
│                            FLOWS                                 │
├─────────────────────────────────────────────────────────────────┤
│ PK │ id                  VARCHAR(100)                           │
│    │ name                VARCHAR(255)         NOT NULL, INDEXED │
│    │ description         TEXT                 NULL              │
│    │ start_task          VARCHAR(100)         NOT NULL          │
│    │ definition          JSON                 NOT NULL          │
│    │ is_active           INTEGER              DEFAULT 1         │
│    │ version             INTEGER              DEFAULT 1         │
│    │ created_at          DATETIME             NOT NULL          │
│    │ updated_at          DATETIME             NOT NULL          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ 1:N
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FLOW_EXECUTIONS                           │
├─────────────────────────────────────────────────────────────────┤
│ PK │ id                  INTEGER              AUTO_INCREMENT    │
│ FK │ flow_id             VARCHAR(100)         NOT NULL, INDEXED │
│    │ status              ENUM                 NOT NULL, INDEXED │
│    │                     (PENDING, RUNNING, SUCCESS,            │
│    │                      FAILURE, COMPLETED)                   │
│    │ input_context       JSON                 NULL              │
│    │ output_data         JSON                 NULL              │
│    │ error_message       TEXT                 NULL              │
│    │ error_task          VARCHAR(100)         NULL              │
│    │ total_tasks_executed INTEGER             DEFAULT 0         │
│    │ started_at          DATETIME             NOT NULL, INDEXED │
│    │ completed_at        DATETIME             NULL              │
│    │                                                             │
│    │ FOREIGN KEY (flow_id) REFERENCES flows(id)                │
│    │   ON DELETE CASCADE                                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ 1:N
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TASK_EXECUTIONS                             │
├─────────────────────────────────────────────────────────────────┤
│ PK │ id                  INTEGER              AUTO_INCREMENT    │
│ FK │ flow_execution_id   INTEGER              NOT NULL, INDEXED │
│    │ task_name           VARCHAR(100)         NOT NULL, INDEXED │
│    │ task_description    VARCHAR(500)         NULL              │
│    │ sequence_number     INTEGER              NOT NULL          │
│    │ status              ENUM                 NOT NULL, INDEXED │
│    │                     (PENDING, RUNNING, SUCCESS, FAILURE)   │
│    │ input_data          JSON                 NULL              │
│    │ output_data         JSON                 NULL              │
│    │ error_message       TEXT                 NULL              │
│    │ error_traceback     TEXT                 NULL              │
│    │ started_at          DATETIME             NOT NULL          │
│    │ completed_at        DATETIME             NULL              │
│    │                                                             │
│    │ FOREIGN KEY (flow_execution_id)                            │
│    │   REFERENCES flow_executions(id)                           │
│    │   ON DELETE CASCADE                                        │
└─────────────────────────────────────────────────────────────────┘