
# FinanceTracker AI

A full-stack personal finance management web application
built with Python, FastAPI, SQLite, and JavaScript.

## Overview

FinanceTracker AI helps users manage their income and
expenses, monitor their balance, and analyze spending
patterns through an interactive dashboard.

## Features

- Create, view, update, and delete transactions
- Track total income, expenses, and balance
- Analyze spending by category
- Interactive charts using Chart.js
- Responsive financial dashboard
- REST API with automatic Swagger documentation
- SQLite database for persistent storage
- Input validation using Pydantic

## Tech Stack

### Backend
- Python
- FastAPI
- SQLite
- Pydantic
- Uvicorn

### Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js

### Development Tools
- Git
- GitHub
- VS Code

## Project Structure

FinanceTracker-AI/
    frontend/
        index.html
        style.css
        script.js
    main.py
    database.py
    requirements.txt
    .gitignore
    README.md

## Installation

### 1. Clone the repository

git clone https://github.com/Nurzhikko/FinanceTracker-AI.git

cd FinanceTracker-AI

### 2. Create a virtual environment

python -m venv .venv

### 3. Activate the environment (Windows)

.venv\Scripts\activate

### 4. Install dependencies

python -m pip install -r requirements.txt

### 5. Initialize the database

python database.py

### 6. Start the server

python -m uvicorn main:app --reload

## Usage

Open the dashboard:

http://127.0.0.1:8000/dashboard/

API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /transactions | Get all transactions |
| POST | /transactions | Create a transaction |
| PUT | /transactions/{id} | Update a transaction |
| DELETE | /transactions/{id} | Delete a transaction |
| GET | /analytics/summary | Financial summary |
| GET | /analytics/categories | Spending by category |

## Future Improvements

- User authentication
- PostgreSQL integration
- Budget management
- Monthly reports
- AI-powered spending predictions
- Multi-currency support
- Automated testing

## Author

Nurzhigit Zhumabek

GitHub: https://github.com/Nurzhikko

## Project Status

Active development
