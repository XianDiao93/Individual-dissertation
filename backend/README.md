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

### tests/

Contains test scripts for backend components.

---

### requirements.txt

Lists all required Python dependencies.

---

## Notes

- The backend depends on OpenAI API for LLM functionality
- The API key must be set before running the server
- Outputs (e.g., generated documents) are saved in the `output/` directory at the project root