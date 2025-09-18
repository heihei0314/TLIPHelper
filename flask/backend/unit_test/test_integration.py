import json
import os
import sys
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables and initialize the client ONCE when the script starts.
AZURE_OPENAI_API_KEY = None
AZURE_OPENAI_ENDPOINT = None
AZURE_OPENAI_API_VERSION = None
AZURE_OPENAI_DEPLOYMENT_NAME = None

try:
    script_dir = os.path.dirname(__file__)
    dotenv_path = os.path.join(script_dir, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME]):
        raise ValueError("One or more required Azure environment variables are not set.")
except Exception as e:
    print(f"Configuration Error during main.py init: {e}", file=os.sys.stderr)

# Adjust sys.path to allow importing from the backend directory
# This assumes the current script is in backend/unit_test/ or a similar structure
# and main.py is in backend/
script_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, backend_dir)

# Import generate_mock_user_inputs from simulation.py
# This assumes simulation.py is directly in the 'backend' directory or accessible via sys.path
try:
    from simulation import generate_mock_user_inputs
except ImportError as e:
    print(f"Error importing generate_mock_user_inputs from simulation.py: {e}")
    print("Please ensure simulation.py is in a directory accessible by the Python path.")
    sys.exit(1)

# Import get_openai_reply from main.py
# This assumes main.py is directly in the 'backend' directory
try:
    from main import get_openai_reply
except ImportError as e:
    print(f"Error importing get_openai_reply from main.py: {e}")
    print("Please ensure main.py is in a directory accessible by the Python path (e.g., in 'backend/').")
    sys.exit(1)


def run_main_with_simulated_inputs():
    """
    Generates mock user inputs using simulation.py's function
    and then calls main.py's get_openai_reply with these inputs.
    """
    print("--- Starting Simulation of main.py with AI-Generated User Inputs ---")

    # 1. Generate mock user inputs using the function from simulation.py
    simulated_user_inputs = generate_mock_user_inputs()

    # Initialize a summary array to pass to get_openai_reply
    # This will accumulate summaries as if a real session is progressing
    current_summary_array = {
        "objective": "", "outcomes": "", "pedagogy": "",
        "development": "", "implementation": "", "evaluation": ""
    }

    print("\n--- Calling main.py's get_openai_reply for each simulated input ---")
    print("-" * 70)

    for purpose, user_inputs_list in simulated_user_inputs.items():
        print(f"\nProcessing Step: {purpose.upper()}")
        for i, user_input_single_question in enumerate(user_inputs_list):
            print(f"Simulated User Input {i+1}: '{user_input_single_question}'")
            # Call get_openai_reply with user_input_single_question

            # 2. Call get_openai_reply from main.py
            # Note: get_openai_reply will internally make an Azure OpenAI call.
            try:
                response_json_str, updated_summary_array = get_openai_reply(
                    user_input=user_input_single_question,
                    purpose=purpose,
                    current_summary_array=current_summary_array # Pass the accumulating summary
                )
                
                # Update the current_summary_array with the latest summary from the response
                try:
                    response_data = json.loads(response_json_str)
                    if "summary" in response_data:
                        current_summary_array[purpose] = updated_summary_array[purpose]
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON response for {purpose}: {response_json_str}")

                print(f"Response from main.py (JSON):\n{response_json_str}")
                print(f"Updated Summary Array:\n{json.dumps(current_summary_array[purpose], indent=2)}")
                print("-" * 70)

            except Exception as e:
                print(f"Error calling get_openai_reply for purpose '{purpose}': {e}")
                print("-" * 70)
                
                # --- Evaluate the output from main.py using the evaluator persona ---
            if purpose != "integrator": # Evaluator typically doesn't evaluate the final integration output
                print("\n--- Evaluating Chatbot Output ---")
                eval_result_json_str = evaluate_main(
                    user_input=user_input_single_question,
                    chatbot_response_data=response_data, # Pass the parsed data
                    current_summary_array=current_summary_array,
                    step_name=purpose
                )
                try:
                    eval_result = json.loads(eval_result_json_str)
                    print(f"Evaluator Assessment:\n{json.dumps(eval_result, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode evaluator's JSON response: {eval_result_json_str}")
                print("-" * 70)
            else:
                print("-" * 70) # Just a separator for integrator step
    # Continue to next purpose even if one fails
    # After all steps, call the 'integrator' purpose
    print("\n--- Attempting to call 'integrator' for final proposal ---")
    # The integrator usually takes the full summary_array as its 'user_input'
    # or accesses it from a session/global state.
    # Assuming it takes the full summary_array as user_input for simplicity here.
    try:
        final_proposal_json_str, _ = get_openai_reply(
            user_input=json.dumps(current_summary_array), # Integrator uses the accumulated summary
            purpose="integrator",
            current_summary_array=current_summary_array # Pass for consistency, though integrator might ignore it
        )
        print(f"Final Proposal from main.py:\n{final_proposal_json_str}")
    except Exception as e:
        print(f"Error generating final proposal: {e}")

    print("\n--- Simulation Complete ---")

def evaluate_main(user_input, chatbot_response_data, current_summary_array, step_name):
    """
    Simulates an AI evaluator agent assessing the chatbot's response.
    """
    # Define the evaluator persona
    EVALUATOR_PERSONA = (
        "You are an automated evaluation agent for a chatbot. Your task is to critically assess the chatbot's response "
        "based on the provided user input, the chatbot's output, and the overall conversational context (previous summaries). "
        "Your evaluation MUST be a valid JSON object with the following keys:\n"
        "- 'alignment_with_context' (boolean): Is the chatbot's response consistent with previous summaries and the current step's purpose?\n"
        "- 'relevance_to_input' (boolean): Is the chatbot's response directly relevant to the user's latest input?\n"
        "- 'layman_and_simple' (boolean): Is the chatbot's language easy to understand for a general audience, avoiding excessive jargon?\n"
        "- 'encourages_next_step' (boolean): Does the chatbot's response clearly guide the user towards the next logical step, if applicable?\n"
        "- 'suggested_ideas_present' (boolean): Are 2-3 new suggested questions or ideas provided in the 'suggested_questions' array?\n"
        "- 'overall_feedback' (string): A brief, constructive comment on the chatbot's performance for this turn.\n"
        "Focus on the quality of the chatbot's summary, follow-up question, and suggested_questions."
    )
    # Construct a detailed prompt for the evaluator (though not sent to a real LLM here)
    evaluator_prompt_context = (
        f"Current Step: {step_name}\n"
        f"User Input: {user_input}\n"
        f"Chatbot Output (JSON): {json.dumps(chatbot_response_data, indent=2)}\n"
        f"Previous Summaries: {json.dumps(current_summary_array, indent=2)}\n\n"
        f"Based on the above, please provide your evaluation in JSON format as specified:\n"
    )

    try:
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME]):
            raise ValueError("Azure OpenAI configuration is incomplete. Check environment variables.")

        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        deployment_name = AZURE_OPENAI_DEPLOYMENT_NAME

        completion = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": EVALUATOR_PERSONA},
                {"role": "user", "content": evaluator_prompt_context}
            ],
            max_tokens=1000,
            temperature=0.5,
        )
        eval_response_str = completion.choices[0].message.content

        try:
            parsed_eval_response = json.loads(eval_response_str)
            # The evaluator AI should return a JSON *object*, not a list.
            # The previous check `if not isinstance(parsed_eval_response, list):` was likely a copy-paste error.
            if not isinstance(parsed_eval_response, dict):
                raise ValueError("AI response is not a JSON object (expected for evaluator).")
            return json.dumps(parsed_eval_response) # Return the parsed dict as a JSON string
        except json.JSONDecodeError:
            print(f"Warning: AI response was not valid JSON: {eval_response_str}", file=sys.stderr)
            # If JSON parsing fails, return a default error JSON string
            return json.dumps({"type": "error", "summary": f"Evaluator AI returned invalid JSON: {eval_response_str}"})
        except ValueError as ve:
            print(f"Warning: {ve} Raw AI response: {eval_response_str}", file=sys.stderr)
            return json.dumps({"type": "error", "summary": f"Evaluator AI returned unexpected format: {eval_response_str}"})

    except Exception as e:
        # This is the problematic line from the traceback.
        # It should only return a string, not a tuple.
        return json.dumps({"type": "error", "summary": f"An error occurred during AI processing: {str(e)}"})
if __name__ == "__main__":
    run_main_with_simulated_inputs()
