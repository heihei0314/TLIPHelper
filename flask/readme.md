# TLIP Helper

This project provides a multi-step chatbot designed to assist users in drafting a preliminary proposal for an educational innovation project. It guides the user through defining objectives, learning outcomes, pedagogy, development, implementation, and evaluation, finally synthesizing all inputs into a cohesive proposal.

The backend is powered by a Flask application that interacts with an Azure OpenAI model, and the frontend is a static HTML/CSS/JS application.

## Table of Contents

1.  [Features](#features)
2.  [Architecture](#architecture)
3.  [Setup Instructions](#setup-instructions)
    * [Prerequisites](#prerequisites)
    * [Environment Variables](#environment-variables)
    * [Installation](#installation)
4.  [Running the Application](#running-the-application)
5.  [Running Tests](#running-tests)
6.  [Project Structure](#project-structure)
7.  [Usage](#usage)
8.  [Future Improvements](#future-improvements)
9.  [License](#license)

## Features

* **Multi-Step Guidance:** Guides users through 6 distinct phases of project planning (Objective, Outcomes, Pedagogy, Development, Implementation, Evaluation).
* **Final Proposal Synthesis:** Integrates all summarized steps into a single, comprehensive project proposal.
* **AI-Powered Responses:** Utilizes Azure OpenAI to generate summaries, follow-up questions, and new options based on user input and predefined personas for each step.
* **Interactive Frontend:** A clean, responsive web interface allows users to input text or select from AI-generated options.
* **Progress Tracking:** A progress bar indicates the completion status of the proposal drafting.


## Architecture

* **Frontend:**
    * `static/index.html`: The main user interface, structured with distinct sections for each project step.
    * `static/css/style.css`: Stylesheets for the application's appearance.
    * `static/js/script.js`: JavaScript logic to handle user interactions, send requests to the Flask backend, and update the UI.
* **Backend:**
    * `backend/app.py`: A Flask application that serves the frontend static files and exposes an API endpoint (`/api/chat`) for handling chatbot interactions. It manages session-specific data for each user's progress.
    * `backend/main.py`: Contains the core AI interaction logic, including persona definitions.
    * `backend/prompts.py`: Defines the system prompts and instructions for the AI model.
    * `backend/unit_test/test_main.py`: Unit tests for the `main.py` functions.
    * `backend/__init__.py` and `unit_test/__init__.py`: Tells Python that this directory should be treated as a Python package.
* **Configuration:**
    * `../../.env`: Stores sensitive API keys and configuration details.
    * `backend/requirements.txt`: Lists all Python dependencies required for the backend.

## Setup Instructions

### Prerequisites
pip install -r /flask/requirements.txt

### Installation

**project structure**
    ```
    .
    ├── backend/
    │   ├── __init__.py  
    │   ├── app.py
    │   ├── main.py
    │   ├── prompts.py
    │   ├── requirements.txt
    │   └── unit_test/
    │       └── __init__.py  
    │       └── test_main.py
    └── static/
        ├── index.html
        ├── css/
        │   └── style.css
        ├── js/
        │   └── script.js
        └── assets/
            └── bot.png (or your bot icon)
    ```


## Running the Application

1.  **Navigate into the `backend` directory:**

    ```bash
    cd flask/backend
    ```

2.  **Run the Flask application:**

    ```bash
    python app.py
    ```

    The application will typically run on `http://127.0.0.1:8001/`.

3.  **Open your web browser** and navigate to `http://127.0.0.1:8001/`.

## Running Tests

To run the unit tests for the backend logic:

1.  **Navigate into the `backend` directory:**

    ```bash
    cd /flask/backend
    ```

2.  **Activate your virtual environment** (if not already active).

3.  **Run the tests:**

    ```bash
    python -m unittest unit_test/test_main.py
    ```

    This will execute all test cases defined in `unit_test/test_main.py` and report the results.


## Usage

1.  Upon loading the page, the first chatbot (Objective) will present an initial question and options.
2.  You can either type your own response in the input field or click on one of the suggested options.
3.  Click the "Send" button (or press Enter) to submit your input.
4.  The AI will process your input, provide a summary, a follow-up question, and new options.
5.  Your progress will be tracked by the progress bar at the top.
6.  Continue through each step (Objective, Outcomes, Pedagogy, Development, Implementation, Evaluation).
7.  Once you have completed all steps, click the "Synthesize" button in the "Final Step!" section to generate a comprehensive project proposal based on all your inputs.

## Future Improvements

* **Robust Session Management:** Implement a more robust session management system (e.g., using Flask-Login with a database like SQLite or PostgreSQL) to persist user progress across browser sessions and handle multiple concurrent users more effectively. The current `user_sessions` dictionary is in-memory and will reset if the server restarts.
* **Error Handling:** Enhance frontend error display for better user feedback (e.g., modal dialogs for critical errors).
* **User Authentication:** Add user authentication to personalize experiences and securely store individual project drafts.
* **Database Integration:** Store project drafts and user data in a database (e.g., PostgreSQL, MongoDB) for persistence and retrieval.
* **Frontend Enhancements:**
    * Add more dynamic loading indicators.
    * Improve accessibility.
    * Consider a more advanced frontend framework (e.g., React, Vue) for complex UI interactions if the project scales.
* **AI Model Flexibility:** Allow users to select different AI models or configurations.
* **Markdown Rendering:** Render the final proposal with Markdown to HTML for better formatting.

## License

This project is open-source.
