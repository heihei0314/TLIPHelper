import os
import json
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from dotenv import load_dotenv

# Add the backend directory to the Python path to allow importing main
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the get_openai_reply function from your main.py script
from main import get_openai_reply
from prompts import SYSTEM_PROMPTS # SYSTEM_PROMPTS is imported for validation

# Initialize Flask app, specifying the root directory for static files
# The static_folder is now relative to the project root, not app.py's location
app = Flask(__name__, static_folder='../static', static_url_path='/static')
CORS(app) # Enable CORS for all routes

# Load environment variables from .env file
# The .env file is now in the backend directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Set a secret key for session management (important for production)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_key_for_dev")

# In a real multi-user application, summary_array should be stored per user session
# For this example, we'll use a simple dictionary to store summaries per session ID.
# This is a simplification; a robust solution would involve user authentication and a database.
user_sessions = {}

@app.route('/')
def serve_index():
    """Serve the main index.html file from the static folder."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images) from the static folder."""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handles chat requests, processes user input using the AI model,
    and returns a JSON response.
    """
    try:
        data = request.get_json()

        if not data or 'userInput' not in data or 'purpose' not in data:
            return jsonify({"type": "error", "summary": "Invalid input. 'userInput' and 'purpose' are required."}), 400

        user_input = data['userInput']
        purpose = data['purpose']

        # Get or create a session ID for the current user
        # IMPORTANT FIX: Ensure user_sessions[session_id] is initialized if session_id exists but not in user_sessions
        session_id = session.get('session_id')
        if not session_id or session_id not in user_sessions:
            session_id = os.urandom(16).hex()
            session['session_id'] = session_id
            user_sessions[session_id] = {
                "objective": "", "outcomes": "", "pedagogy": "",
                "development": "", "implementation": "", "evaluation": ""
            }
        
        # Now, current_summary_array can be safely accessed
        current_summary_array = user_sessions[session_id]

        # Validate the purpose against the SYSTEM_PROMPTS keys
        if purpose not in SYSTEM_PROMPTS:
            return jsonify({"type": "error", "summary": f"Invalid 'purpose' provided: {purpose}"}), 400

        # Call the get_openai_reply function from main.py
        response_data_str, updated_summary_array = get_openai_reply(user_input, purpose, current_summary_array)
        response_json_from_main = json.loads(response_data_str)
        
        # Update the session's summary array
        user_sessions[session_id] = updated_summary_array
        response_json_from_main['full_summary_state'] = user_sessions[session_id]
        
        # Parse the JSON string from main.py and return as Flask JSON response
        return jsonify(response_json_from_main), 200

    except json.JSONDecodeError:
        return jsonify({"type": "error", "summary": "Invalid JSON in request body."}), 400
    except Exception as e:
        app.logger.error(f"An error occurred in /api/chat: {e}", exc_info=True)
        return jsonify({"type": "error", "summary": f"An internal server error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    # Ensure the static directory exists relative to the project root
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        os.makedirs(os.path.join(static_dir, 'css'))
        os.makedirs(os.path.join(static_dir, 'js'))
        os.makedirs(os.path.join(static_dir, 'assets'))

    app.run(debug=True, port=8002) # Run on port 8001 in debug mode
