# JARVIS Architecture Documentation

## 1. Executive Summary & Context

JARVIS is a modular, personal AI workspace designed for Windows 10 (64-bit) running on Python 3.12+.
It transforms traditional conversational assistant launchers into a structured, controllable AI workspace capable of multi-step task planning, project management, controlled tool execution, and persistent local memory.

---

## 2. Current State vs Target Architecture

### 2.1 Current State
- **Files**: Repository initially contained only `README.md` and standard repository files.
- **Environment**: Python 3.12+ runtime on x86_64 Linux/Windows. Standard Python library packages (including Tkinter version 8.6) available.
- **Debt & Gaps**: Lack of foundational modules (`config`, `ai`, `tools`, `memory`, `brain`, `gui`).

### 2.2 Target Architecture Overview
JARVIS follows a decoupled, layered architecture to isolate intelligence, control, capabilities, memory, and user interface.

```
                    +--------------------------------+
                    |           GUI Layer            |
                    | (Workspace / Chat / Explorer)  |
                    +---------------+----------------+
                                    |
                                    v
                    +--------------------------------+
                    |           JARVIS Core          |
                    |    (Agent Brain & Planner)     |
                    +---------------+----------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
+-----------------------+ +-------------------+ +-----------------------+
|       AI Layer        | |    Memory Layer   | |      Tool Layer       |
| (NVIDIA NIM Client)   | | (SQLite Repositories)| (Validation/Permission)|
+-----------------------+ +-------------------+ +-----------+-----------+
                                                            |
                                                            v
                                                +-----------------------+
                                                |     OS Operations     |
                                                | (Files, Apps, System) |
                                                +-----------------------+
```

---

## 3. Core Modules & Responsibilities

### 3.1 Configuration Layer (`config/`)
- **Responsibilities**: Load environment variables (`.env`), manage application settings, secure API keys (NVIDIA NIM key), model parameters, safety toggles, and local storage paths.
- **Secrets Management**: Secrets are never hardcoded. Fallback gracefully when keys are missing.

### 3.2 AI Layer (`ai/`)
- **Responsibilities**: Isolated client for LLM providers (defaulting to NVIDIA NIM API). Handles prompt formatting, message history formatting, response schema parsing, structured action extraction, and mock client implementations for offline testing.

### 3.3 Security & Tool Protocol Layer (`tools/`)
- **Strict Execution Control**: The LLM NEVER receives unrestricted direct access to the operating system or system shell.
- **Tool Protocol**:
  - `name`: Unique identifier (e.g. `filesystem.read_file`).
  - `description`: Purpose and usage instructions for the LLM.
  - `parameters`: JSON Schema for input validation.
  - `permission_level`: `READ_ONLY`, `CONFIRMATION_REQUIRED`, or `DANGEROUS`.
  - `validate()`: Validates arguments before execution.
  - `execute()`: Runs tool action safely and returns structured output.
- **Confirmation Workflow**: Destructive or high-impact actions (deleting files, overwriting files, running system commands) trigger explicit user confirmation in the UI layer before execution.

### 3.4 Persistent Local Memory Layer (`memory/`)
- **Storage Engine**: Local SQLite database (`jarvis_memory.db`).
- **Repositories**:
  - `ConversationsRepository`: Message history, turn metadata, context tags.
  - `ProjectsRepository`: Project records, workspace root paths, meta tags.
  - `TasksRepository`: Task hierarchy, status, plan steps.
  - `ToolActivityRepository`: Execution audit log (tool name, input, output, permission granted, timestamp).
  - `PreferencesRepository`: User settings and key-value persistent storage.

### 3.5 Agent Brain & Reasoning Layer (`brain/`)
- **Responsibilities**:
  - `ContextManager`: Assembles prompt context (relevant memory, project status, system environment).
  - `Planner`: Decomposes user goals into structured sub-tasks.
  - `Agent`: Manages the reasoning loop (User request -> Context assembly -> LLM response -> Action parsing -> Tool validation -> User confirmation if needed -> Tool execution -> Result processing -> GUI update).

### 3.6 GUI Workspace Layer (`gui/`)
- **Framework**: Desktop GUI built with standard Python Tkinter / CustomTkinter architecture.
- **Components**:
  - **Chat Panel**: Conversational interaction & reasoning history.
  - **Current Task / Plan Panel**: Active goals, multi-step sub-tasks, execution status.
  - **Project Explorer**: Project view, file tree navigation.
  - **Tool Activity & Log View**: Audit logs of requested and executed tools.
  - **Settings Panel**: Model selection, API keys, safety policy configurations.
- **Decoupling**: Complete UI/Core separation. Core agent functions in headless mode when GUI is disabled or during automated testing.

---

## 4. Execution Pipeline & Safety Pipeline

```
[User Request]
      │
      ▼
[GUI / Interface] ──► [Agent Brain] ──► [Context Manager] ──► Assemble Context
                                                                    │
                                                                    ▼
[Structured Output] ◄── [NVIDIA NIM Client] ◄───────────────────────┘
      │
      ▼
[Tool Validator] ──► Check Schema & Arguments
      │
      ├── Permission: READ_ONLY ──► [Tool Execution Engine]
      │
      └── Permission: CONFIRMATION_REQUIRED ──► Request User Confirmation in GUI
                                                          │
                                                    [User Approved]
                                                          │
                                                          ▼
                                              [Tool Execution Engine]
                                                          │
                                                          ▼
                                                 [Result to Agent]
                                                          │
                                                          ▼
                                                  [Update GUI View]
```

---

## 5. Migration Strategy & Phased Development

1. **Phase 1: Reconnaissance & Architecture Documentation** (Completed)
2. **Phase 2: Configuration & AI Provider Infrastructure** (`config/`, `ai/`)
3. **Phase 3: Secure Tool System & Safety Protocol** (`tools/`)
4. **Phase 4: SQLite Persistent Memory Repositories** (`memory/`)
5. **Phase 5: Agent Core, Planner, & Reasoning Loop** (`brain/`)
6. **Phase 6: Modular GUI Desktop Workspace** (`gui/` & `main.py`)
7. **Phase 7: End-to-End Integration & Comprehensive Testing**
