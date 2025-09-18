import json
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI


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

def simulate_openai_chat_completion(system_prompt, user_query):
    """
    Simulates a call to Azure OpenAI's chat.completions.create method.
    This function now expects and attempts to parse a JSON array from the AI response.
    """
    try:
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME]):
            raise ValueError("Azure OpenAI configuration is incomplete. Check environment variables.")

        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        deployment_name = AZURE_OPENAI_DEPLOYMENT_NAME

        # Simulate the call that would normally be made
        response = client.chat.completions.create(
            model=deployment_name, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=100, 
            temperature=1, 
        )
        # Attempt to parse the response content as JSON
        ai_response_content = response.choices[0].message.content
        # This handles cases where the AI might wrap JSON in ```json ... ```
        if ai_response_content.startswith("```json"):
            ai_response_content = ai_response_content[len("```json"):].strip()
        if ai_response_content.endswith("```"):
            ai_response_content = ai_response_content[:-len("```")].strip()
        try:
            parsed_content = json.loads(ai_response_content)
            if not isinstance(parsed_content, list):
                raise ValueError("AI response is not a JSON list.")
            return parsed_content # Return the parsed list
        except json.JSONDecodeError:
            print(f"Warning: AI response was not valid JSON: {ai_response_content}", file=sys.stderr)
            # Fallback to splitting by newline if JSON parsing fails
            return [q.strip() for q in ai_response_content.split('\n') if q.strip()]
        except ValueError as ve:
            print(f"Warning: {ve} Raw AI response: {ai_response_content}", file=sys.stderr)
            return [q.strip() for q in ai_response_content.split('\n') if q.strip()]

    except Exception as e:
        print(f"Error during AI processing in simulate_openai_chat_completion: {str(e)}", file=sys.stderr)
        return [{"error": f"AI generation failed: {str(e)}"}] # Return an error list

def generate_mock_user_inputs():
    """
    Generates mock user inputs for each project step, simulating
    an AI generating questions/statements from a specific persona.
    The output for each purpose is a list of 3 questions/statements.
    """
    #PURPOSES = [
    #    "objective", "outcomes", "pedagogy", "development", "implementation", "evaluation"
    #]
    PURPOSES = [        
        "development"
    ]
    # Background persona for the AI generating user inputs
    background_persona = (
        "You are a faculty in HKUST, teaching math courses. "
        "You are applying for an education innovation project, but you know nothing "
        "in teaching and learning, and edTech. Ultimately you would like to adopt VR in your math course. "
        "Generate 5 sentences (3 questions and 2 decisions) that you, as this faculty, would ask or say to initiate discussion for the following project step."
        "Keep the 5 generated sentece short and concise." 
        "Focus on your limited knowledge in edTech and T&L, and your desire for VR. You must not mentioned your limited knowledge in edTech and T&L."
        "Return the questions as a JSON array of strings."
        "Steps (purpose):"
        "objective - Project Ojectives"
        "outcomes - intented learning outcomes, you don't have a course in mind, until the you are told to do so."
        "pedagogy - the teaching method"
        "development - frequent questions of development plan"
        "implementation - how to adopt in the class"
        "evaluation - evaluation plans"      
    )

    generated_user_inputs = {}

    for purpose in PURPOSES:
        user_query_for_ai = f"Generate 5 user inputs for the purpose: '{purpose}' based on the persona. You must not generate other purposes. Your response MUST be a valid Array object."

        # simulate_openai_chat_completion already returns a parsed list
        simulated_input_list = simulate_openai_chat_completion(
            system_prompt=background_persona,
            user_query=user_query_for_ai
        )
        generated_user_inputs[purpose] = simulated_input_list

    return generated_user_inputs

if __name__ == "__main__":
    # Run the simulation
    generated_inputs = generate_mock_user_inputs()
    print("\nAll simulated AI-generated user inputs (JSON format):")
    print(json.dumps(generated_inputs, indent=2))

