# Milu Finance

Milu Finance is a comprehensive personal finance management web application designed to help users track their income, monitor expenses, manage recurring fixed bills, and receive intelligent financial insights. Built with Python and Flask, the application integrates with Google's Gemini AI to act as a virtual, context-aware financial assistant.

## Features

*   **User Authentication & Profiles:** Secure registration and login system with customizable user profiles (age, average salary, and transaction categories).
*   **Dashboard Overview:** A centralized view of the user's current financial status, including total income, total expenses, remaining balance, and a breakdown of expenses by category.
*   **Transaction Management:** Easily log general expenses and income. Users can view, edit, and delete their transaction history.
*   **Fixed Expenses Tracker:** Dedicated management for recurring monthly bills, allowing users to track due dates, base amounts, and log payments for specific months.
*   **AI Financial Assistant (Milu):** An integrated chat interface utilizing the Gemini AI model. "Milu" is provided with the user's financial context (balance, recent transactions, pending fixed expenses) to offer personalized and relevant financial advice.

## Technology Stack

*   **Backend:** Python 3, Flask framework
*   **Database:** SQLite, Flask-SQLAlchemy (ORM)
*   **Authentication:** Flask-Login, Flask-Bcrypt (password hashing)
*   **AI Integration:** Google Generative AI (Gemini 2.5 Flash API)
*   **Frontend:** HTML5, Jinja2 templating

## Prerequisites

Before running the application, ensure you have the following installed:
*   Python 3.8 or higher
*   pip (Python package manager)

You will also need an API key from Google Generative AI to use the chatbot feature.

## Installation

1.  **Clone the repository (or navigate to the project directory):**
    ```bash
    cd "milu finance"
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate  # On Windows
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add the following variables:
    ```env
    SECRET_KEY=your_secure_secret_key_here
    GEMINI_API_KEY=your_google_gemini_api_key_here
    ```

## Running the Application

To start the development server, run:

```bash
python run.py
```

The application will be accessible at `http://127.0.0.1:5000/`.

## Deployment

The application is configured to be deployed on platforms that support Python WSGI applications (like PythonAnywhere, Heroku, or Render). The necessary files (`wsgi.py` and `Procfile`) are included in the project structure. Ensure environment variables are properly set in your hosting environment.

## Directory Structure

*   `app/`: Main application package containing routes, models, and initialization logic.
    *   `templates/`: HTML templates for the frontend views.
    *   `static/`: Static assets (CSS, JS, images).
*   `instance/`: Contains the SQLite database file (`site.db`).
*   `.env`: Environment variables configuration file.
*   `requirements.txt`: List of Python dependencies.
*   `run.py`: Script to launch the Flask development server.
*   `wsgi.py`: WSGI entry point for production deployment.
