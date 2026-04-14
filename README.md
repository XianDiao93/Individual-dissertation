# AI-Driven Trade Communication Assistant

## Project Overview

This project develops an AI-driven trade communication assistant to support SMEs in handling international business enquiries.

The system integrates natural language processing, risk analysis, and document generation into a unified workflow:

User Input → Extraction → Risk Analysis → Decision → Response / Document Generation

## Main Functional Modules

### 1. Communication Module
- Generates professional business email replies
- Automatically adapts language and tone
- Adjusts response strategy based on risk level

### 2. Risk Analysis Module
- Identifies potential trade and compliance risks
- Assigns risk levels such as low, medium, and high
- Provides interpretable risk tags

### 3. Document Generation Module
- Generates trade-related documents such as quotations and contracts
- Outputs standardised PDF files

## Project Structure

    backend/
      ├── app/
      │   ├── routers/
      │   ├── services/
      │   ├── models/
      │   └── database/
      ├── run_backend.py

    frontend/
      └── src/
          ├── index.html
          ├── main.js
          ├── api.js
          └── styles.css

    user_data/
    output/

## How to Run the System

### 1. Set the OpenAI API Key

Go to backend/ directory, open PowerShell to set key:

    $env:OPENAI_API_KEY="yourkey"

### 2. Run the Backend

    python run_backend.py

Backend address:

    http://127.0.0.1:8000

### 3. Run the Frontend

Open `frontend/src/index.html` using VS Code Live Server.

Frontend address:

    http://127.0.0.1:5500

## Notes

- This system relies on the OpenAI API
- The API key is required but is not included in this repository
- Output quality depends on model behaviour and input quality

## Author

Xian Diao
20513832
scyxd6@nottingham.ac.uk
BSc Computer Science with Artificial Intelligence  
University of Nottingham