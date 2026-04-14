# Frontend

## Overview

This directory contains the frontend implementation of the system.

The frontend is a lightweight web interface built using HTML, CSS, and JavaScript. It allows users to interact with the backend services for communication generation, risk analysis, and document generation.

---

## How to Run

Open `index.html` using **VS Code Live Server**.

The frontend will typically run at:

    http://127.0.0.1:5500

Ensure that the backend server is already running before using the frontend.

---

## File Structure

- **index.html**
  - Main user interface
  - Provides input fields and displays system outputs

- **main.js**
  - Handles frontend logic
  - Manages user interactions and UI updates

- **api.js**
  - Handles communication with backend APIs
  - Sends requests and processes responses

- **styles.css**
  - Defines the visual style of the interface

---

## Notes

- The frontend communicates with the backend via HTTP APIs
- No build tools or frameworks are required
- Designed to be simple and easy to use