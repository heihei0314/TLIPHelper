import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

# Import SYSTEM_PROMPTS from the prompts.py file 
from prompts import SYSTEM_PROMPTS, JSON_RESPONSE_FORMAT_INSTRUCTION

# Load environment variables and initialize the client ONCE when the script starts.
AZURE_OPENAI_API_KEY = None
AZURE_OPENAI_ENDPOINT = None
AZURE_OPENAI_API_VERSION = None
AZURE_OPENAI_DEPLOYMENT_NAME = None

try:
    script_dir = os.path.dirname(__file__)
    dotenv_path = os.path.join(script_dir, '.env')
    load_dotenv(dotenv_path=dotenv_path)

    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME]):
        raise ValueError("One or more required Azure environment variables are not set.")
except Exception as e:
    print(f"Configuration Error during main.py init: {e}", file=os.sys.stderr)


def get_openai_reply(user_input, purpose, current_summary_array):
    """
    Generates a reply from the OpenAI model based on user input and purpose.
    Manages the summary_array for conversational context.

    Args:
        user_input (str): The user's current input.
        purpose (str): The current stage/purpose of the conversation.
        current_summary_array (dict): The dictionary containing summaries of previous steps.

    Returns:
        tuple: A tuple containing (json_response_string, updated_summary_array_dict).
               json_response_string is a JSON string of the response data.
               updated_summary_array_dict is the updated summary array.
    """
    config = SYSTEM_PROMPTS.get(purpose)
    if not config:
        return json.dumps({"type": "error", "summary": "Invalid purpose provided."}), current_summary_array

    # --- Mode 1: Initial Question ---
    if not user_input.strip() and purpose != "integrator":
        response_data = {
            "type": "question",
            "question": config["initial_question"],
            "options": config["options"]
        }
        return json.dumps(response_data), current_summary_array

    # Mode 2: Call AI and get a structured response
    try:
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME]):
            raise ValueError("Azure OpenAI configuration is incomplete. Check environment variables.")

        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        deployment_name = AZURE_OPENAI_DEPLOYMENT_NAME

        summary_text = ""
        for key, value in current_summary_array.items():
            if value:
                summary_text += f"{key}: {value}\n"

        system_message = summary_text + config["persona"]

        completion = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            temperature=0.5,
        )
        ai_response_str = completion.choices[0].message.content

        response_data = {}
        if purpose == 'integrator':
             response_data = {
                "type": "summary_only",
                "summary": ai_response_str
             }
        else:
            ai_response_json = json.loads(ai_response_str)
            response_data = {
                "type": "summary_and_options",
                "explanation": ai_response_json.get("explanation", "AI did not provide an explanation."),
                "follow_up_question": ai_response_json.get("follow_up_question", "AI did not provide a follow-up question."),
                "summary": ai_response_json.get("summary", "AI did not provide a summary."),
                "suggested_questions": ai_response_json.get("suggested_questions", [])
            }
            current_summary_array[purpose] = ai_response_json.get("summary", "")

        return json.dumps(response_data), current_summary_array

    except json.JSONDecodeError:
        return json.dumps({"type": "error", "summary": "The AI response was not in the expected format. Please try again."}), current_summary_array
    except Exception as e:
        return json.dumps({"type": "error", "summary": f"An error occurred during AI processing: {str(e)}"}), current_summary_array

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        bot_purpose = sys.argv[1]
        user_text = sys.stdin.read()
        test_summary_array = {
            "objective": "", "outcomes": "", "pedagogy": "",
            "development": "", "implementation": "", "evaluation": ""
        }
        json_output, _ = get_openai_reply(user_text, bot_purpose, test_summary_array)
        print(json_output)
    else:
        error_msg = {"type": "error", "summary": "Internal Server Error: Incorrect number of arguments for standalone script."}
        sys.stderr.write(json.dumps(error_msg))
