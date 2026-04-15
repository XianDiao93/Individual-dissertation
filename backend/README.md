# Backend Service

## Overview

This directory contains the backend implementation of the AI-Driven Trade Communication Assistant.

The backend is built using FastAPI and is responsible for handling request processing, LLM interaction, risk analysis, and document generation.

---

## How to Run

### 1. Set OpenAI API Key

In PowerShell:

    $env:OPENAI_API_KEY="yourkey"

---

### 2. Start Backend Server

    python run_backend.py

The backend will run at:

    http://127.0.0.1:8000

---

## Directory Structure

### app/

Core application logic.

- **routers/**
  - Defines API endpoints
  - Handles incoming HTTP requests (e.g., communication, document, risk)

- **services/**
  - Contains core business logic
  - Includes:
    - LLM interaction (`llm_client.py`)
    - trade fact extraction
    - risk analysis modules
    - decision engine
    - communication and document generation

- **models/**
  - Defines data structures and schemas
  - Used for request/response validation

- **database/**
  - Stores configuration and rule-based data
  - Includes:
    - system prompts (LLM prompts)
    - country code mappings
    - risk tag definitions

- **utils/**
  - Helper functions (e.g., file handling)

---

### run_backend.py

Entry point of the backend server.

---

## Testing

Unit tests are implemented using `pytest` to validate core backend logic.

### Test Scope

The tests focus on deterministic and rule-based components:

- **decision_engine.py**
  - Risk scoring and overall decision calculation

- **extraction.py**
  - Trade information post-processing and normalization

- **llm_client.py**
  - Response cleaning and language handling

- **communication.py**
  - Reply generation wrapper and parameter handling

- **risk.py**
  - Risk orchestration and output structure

### Run Tests

Before running tests, set environment variables:

PowerShell:

    $env:PYTHONPATH="backend"
    $env:OPENAI_API_KEY="test-key"

Then run:

    pytest

### Notes

- External LLM calls are mocked where necessary
- Tests focus on core logic rather than full API integration
- This ensures fast and reliable test execution

### requirements.txt

Lists all required Python dependencies.

---

## Notes

- The backend depends on OpenAI API for LLM functionality
- The API key must be set before running the server
- Outputs (e.g., generated documents) are saved in the `output/` directory at the project root