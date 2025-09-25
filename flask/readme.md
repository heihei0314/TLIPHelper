# TLIP Helper

This project provides a multi-step chatbot designed to assist users in drafting a preliminary proposal for an educational innovation project. It guides the user through defining objectives, learning outcomes, pedagogy, development, implementation, and evaluation, finally synthesizing all inputs into a cohesive proposal.

The backend is powered by a Flask application that interacts with an Azure OpenAI model, and the frontend is a static HTML/CSS/JS application.

## Table of Contents

1.  [Objectives](#objectives)
2.  [Features](#features)
3.  [Architecture](#architecture)
4.  [Setup Instructions](#setup-instructions)
    * [Prerequisites](#prerequisites)
    * [Environment Variables](#environment-variables)
    * [Installation](#installation)
5.  [Running the Application](#running-the-application)
6.  [Running Tests](#running-tests)
7.  [Project Structure](#project-structure)
8.  [Usage](#usage)
9.  [Future Improvements](#future-improvements)
10.  [License](#license)

## Objectives
* 1. Ask Follow-up question to inspire user 
* 2. Provide related options for user to consider 
* 3. Explain and Answer User's question on Education and Innovational Development
* 4. Summary User's idea and plan 

## Features

* **Multi-Step Guidance:** Guides users through 6 distinct phases of project planning (Objective, Outcomes, Pedagogy, Development, Implementation, Evaluation).
* **Final Proposal Synthesis:** Integrates all summarized steps into a single, comprehensive project proposal.
* **AI-Powered Responses:** Utilizes Azure OpenAI to generate summaries, follow-up questions, and new options based on user input and predefined personas for each step.
* **Contextual AI Grounding (RAG):** The AI's responses are grounded in a knowledge base.
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
    * `backend/rag_builder.py`: A utility script to process `.docx` files, create vector embeddings, and store them in a local vector database.
    * `backend/rag_db/`: A directory that stores the vector database (ChromaDB) created by `rag_builder.py`.
    * `backend/unit_test/test_main.py`: Unit tests for the `main.py` functions.
    * `backend/unit_test/evaluate_rag.py`: Unit tests for the result of `rag_db/` from `rag_builder.py` Accuracy and Relevance.
    * `backend/__init__.py` and `unit_test/__init__.py`: Tells Python that this directory should be treated as a Python package.
* **Data:**
    * `xx.docx`: storing the relevance document for reference, including proposal template, faq and guideline.
* **Configuration:**
    * `../../.env`: Stores sensitive API keys and configuration details.
    * `backend/requirements.txt`: Lists all Python dependencies required for the backend.

## Setup Instructions

### Prerequisites
pip3 install -r /flask/requirements.txt

### Installation

**project structure**
    ```
    .
    ├── backend/
    │   ├── __init__.py  
    │   ├── .env 
    │   ├── app.py
    │   ├── main.py
    │   ├── prompts.py
    │   ├── rag_builder.py
    │   ├── requirements.txt
    │   ├── rag_db/
    │   └── unit_test/
    │       ├── __init__.py  
    │       ├── test_main.py
    │       ├── evaluate_rag.py
    │       └── golden_dataset.json
    ├── data/
    │   ├── application form.docx/
    │   ├── practical guideline.docx/
    │   └── FAQ.docx/
    └── static/
        ├── index.html
        ├── css/
        │   └── style.css
        ├── js/
        │   └── script.js
        └── assets/
            └── bot.png (or your bot icon)
    ```


## Build the RAG Knowledge Base
1. Place `.docx` reference files into the `backend/data` directory.

2.  **Navigate into the `backend` directory:**

    ```bash
    cd /var/www/html/TLIPHelper/backend
    ```

    or

    [debug mode]```bash
    cd flask/backend
    ```

3. Run the `rag_builder.py` script.
    
    ```bash
    python3 rag_builder.py
    ```
    This will create the `rag_db` directory containing vector database.



## Running the Application

1.  **Navigate into the `backend` directory:**

    ```bash
    cd /var/www/html/TLIPHelper/backend
    ```

    or

    [debug mode]```bash
    cd flask/backend
    ```

2.  **Run the Flask application:**
    Using gunicorn to run the application in daemon mode.
    ```bash
    gunicorn --workers 3 --bind 127.0.0.1:8002 app:app --daemon --pid /tmp/tlip_helper_gunicorn.pid
    ```
    If the python files are updated, to restart the service, stop it first:
    
    ```bash
    PID=$(cat /tmp/tlip_helper_gunicorn.pid)
    kill $PID
    gunicorn --workers 3 --bind 127.0.0.1:8002 app:app --daemon --pid /tmp/tlip_helper_gunicorn.pid
    ```

    or

    [debug mode]```bash
    python3 app.py
    ```

3.  **Open your web browser** and navigate to [debug mode]`http://127.0.0.1:8001/` or `https://pdev6800z-ai.ust.hk/tlip-helper/`.

## Running Tests

To run the unit tests for the backend logic:

1.  **Navigate into the `backend` directory:**

    ```bash
    cd /flask/backend
    ```

2.  **Activate your virtual environment** (if not already active).

3.  **Run the tests:**

    ```bash
    python3 -m unittest unit_test/test_main.py
    ```

    This will execute all test cases defined in `unit_test/test_main.py` and report the results.

## Testing
This section describes the testing strategy and the purpose of the main test files.

### RAG Pipeline Evaluation
To evaluate the RAG pipeline's performance, run the `evaluate_rag.py` script.

1. Navigate to the backend directory.

    ```bash
    cd /var/www/html/TLIPHelper/backend
    ```

    or

    [debug mode]```bash
    cd flask/backend
    ```
2. Run the script.

    ```bash
    python3 evaluate_rag.py
    ```
    This script uses the `golden_dataset.json` file to test if the RAG system retrieves the correct information and provides factually accurate answers.

### Main Function Evaluation
    
The `golden_dataset.json` file contains a comprehensive suite of tests for the backend application, focusing on the core AI functionality and the RAG pipeline. It includes:

    1. Azure OpenAI API Connection Test: This is the primary test that runs first to ensure a stable connection and an expected response from the configured Azure OpenAI endpoint. It verifies that the API key, endpoint, API version, and deployment name are correctly loaded, and that a basic chat completion call succeeds.

    2. Automated Evaluation with Golden Dataset: This suite of tests validates the end-to-end performance of the RAG pipeline. It automatically runs a set of predefined queries from the golden_dataset.json file to check the following:
        - Factual Accuracy: It verifies that the AI's generated response is factually correct and aligns with the ground truth answer in the dataset.
        - Faithfulness: It measures whether the AI's answer is strictly based on the retrieved context from your application form documents. This is a crucial test for detecting "hallucinations."
        - Relevance: It ensures that the AI's response directly addresses the user's question.

    3. General Unit Tests: These tests focus on the output of the get_openai_reply function. They validate that the function's response is in a valid JSON format and contains all the expected keys (type, explanation, follow_up_question, options, etc.), ensuring the API's contract with the frontend is met.

    4. Navigate to the backend directory.

        ```bash
        cd /var/www/html/TLIPHelper/backend
        ```

        or

        [debug mode]```bash
        cd flask/backend
        ```
    5. Run the script.
        ```bash
        python3 evaluate_rag.py
        ```

## Usage

1.  Upon loading the page, the first chatbot (Objective) will present an initial question and options.
2.  You can either type your own response in the input field or click on one of the suggested options.
3.  Click the "Send" button (or press Enter) to submit your input.
4.  The AI will process your input, provide a summary, a follow-up question, and new options.
5.  Your progress will be tracked by the progress bar at the top.
6.  Continue through each step (Objective, Outcomes, Pedagogy, Development, Implementation, Evaluation).
7.  Once you have completed all steps, click the "Synthesize" button in the "Final Step!" section to generate a comprehensive project proposal based on all your inputs.


## License
This project is open-source.
