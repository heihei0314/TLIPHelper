import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv

#library for RAG
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma



# Import SYSTEM_PROMPTS from the prompts.py file 
from prompts import SYSTEM_PROMPTS, SUMMARY_AGENT_SYSTEM_MESSAGE, SUGGESTIONS_AGENT_SYSTEM_MESSAGE


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




# --- RAG Context Manager ---
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), 'rag_db')
class RAG_CONTEXT_MANAGER:
    """
    Manages the RAG pipeline by loading the vector store and retrieving relevant
    documents based on a user query.
    """
    def __init__(self, vector_db_path, embedding_model_name="all-MiniLM-L6-v2"):
        if not os.path.exists(vector_db_path):
            raise FileNotFoundError(f"Vector database not found at {vector_db_path}. Please run rag_builder.py first.")
        
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name=embedding_model_name
        )
        self.vector_store = Chroma(
            persist_directory=vector_db_path,
            embedding_function=self.embeddings_model
        )
        self.retriever = self.vector_store.as_retriever()

    def get_relevant_context(self, query):
        """Retrieves relevant document chunks for a given query."""
        # Retrieve the most relevant documents (chunks)
        docs = self.retriever.invoke(query)
        # Concatenate the content of the documents into a single string
        context = " ".join([doc.page_content for doc in docs])
        return context

# Instantiate the RAG manager once at the start of the application

# Instantiate the RAG manager once at the start of the application
try:
    rag_manager = RAG_CONTEXT_MANAGER(VECTOR_DB_PATH)
except FileNotFoundError as e:
    print(f"RAG Initialization Error: {e}", file=os.sys.stderr)
    rag_manager = None

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
        
        # --- RAG Integration: Retrieve context from the document ---
        retrieved_context = ""
        if rag_manager:
            retrieved_context = rag_manager.get_relevant_context(user_input)
            
        # Add a note to the system prompt to instruct the AI to use the retrieved context
        system_prompt_with_rag = f"""
        {config["persona"]}
        
        **Reference Material**
        Use the following information as reference to improve your output.
        If the information does not directly help, you can ignore it.
        
        Reference:
        {retrieved_context}
        """
        

        #Call multi-agents for integrator 
        if purpose == 'integrator':
            # Step 1: Prepare the context for both agents
            full_summary_text = ""
            for key, value in current_summary_array.items():
                if value:
                    full_summary_text += f"**{key.capitalize()}**:\n{value}\n\n"

            # Step 2: Call the primary 'integrator' agent to synthesize the proposal
            proposal_messages = [
                {"role": "system", "content": SYSTEM_PROMPTS['integrator']['persona']},
                {"role": "assistant", "content": full_summary_text},
                {"role": "user", "content": user_input}
            ]
            
            proposal_completion = client.chat.completions.create(
                model=deployment_name,
                messages=proposal_messages,
                max_tokens=2000,
                temperature=0.5,
            )
            proposal_output = proposal_completion.choices[0].message.content

            # Step 3: Call the separate 'suggestions' agent
            # We use the same summary as context but with a new prompt
            suggestions_messages = [
                {"role": "system", "content": SUGGESTIONS_AGENT_SYSTEM_MESSAGE},
                {"role": "user", "content": full_summary_text} # The user input for this agent is the summary itself
            ]
            
            suggestions_completion = client.chat.completions.create(
                model=deployment_name,
                messages=suggestions_messages,
                max_tokens=500,
                temperature=0.5,
            )
            suggestions_output = suggestions_completion.choices[0].message.content

            # Step 4: Combine the outputs and return to the user
            final_combined_output = f"{proposal_output}\n\n# Suggestions\n{suggestions_output}"
            
            response_data = {
                "type": "summary_only",
                "summary": final_combined_output
            }
            return json.dumps(response_data), current_summary_array

        #Call agent for general purpose (steps)
        else:
            # For all general purposes, we only provide the summary for the current purpose.
            current_purpose_summary = current_summary_array.get(purpose, "")
            
            messages = [
                {"role": "system", "content": system_prompt_with_rag},
                {"role": "assistant", "content": current_purpose_summary},
                {"role": "user", "content": user_input}
            ]
        
            # Use a retry loop to handle JSON errors
            max_retries = 2
            for i in range(max_retries):
                try:
                    completion = client.chat.completions.create(
                        model=deployment_name,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.5,
                    )
                    ai_response_str = completion.choices[0].message.content

                    # Parse the AI's JSON response for the conversation.
                    ai_response_json = json.loads(ai_response_str)
                    # If JSON parsing is successful, break the loop and proceed
                    break
                except json.JSONDecodeError:
                    # If JSON parsing fails, update the chat history with a correction message
                    correction_prompt = "The previous response was not a valid JSON. Please provide a valid JSON object without any additional text. Strictly adhere to the format."
                    # Append the correction to the messages list
                    messages.append({"role": "assistant", "content": ai_response_str}) # The invalid response
                    messages.append({"role": "user", "content": correction_prompt}) # The instruction to correct
                
                    if i == max_retries - 1:
                        # If this is the last retry, return a failure message
                        return json.dumps({"type": "error", "summary": f"Failed to get a valid JSON response after {max_retries} attempts. The AI did not adhere to the format."}), current_summary_array

            # After getting the JSON response, we call a separate function to generate the summary.
            summary_response = generate_summary(purpose, user_input, current_purpose_summary)
            current_summary_array[purpose] = summary_response

            response_data = {
                "type": "summary_and_options",
                "explanation": ai_response_json.get("explanation", "AI did not provide an explanation."),
                "follow_up_question": ai_response_json.get("follow_up_question", "AI did not provide a follow-up question."),
                "options": ai_response_json.get("new_options", [])
            }
            return json.dumps(response_data), current_summary_array

    except json.JSONDecodeError:
        return json.dumps({"type": "error", "summary": f"The AI response for '{purpose}' was not in the expected JSON format. Please try again."}), current_summary_array
    except Exception as e:
        return json.dumps({"type": "error", "summary": f"An error occurred during AI processing for '{purpose}': {str(e)}"}), current_summary_array


def generate_summary(purpose, user_input, current_summary_purpose):
    """
    Generates a new summary by incorporating the latest user input into the existing summary.
    This prevents the summary from growing with repetitive content.
    """
    try:
        if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME]):
            raise ValueError("Azure OpenAI configuration is incomplete.")

        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        deployment_name = AZURE_OPENAI_DEPLOYMENT_NAME

        # The system message should instruct the AI to update the list, not create a new one.
        summary_system_message = SUMMARY_AGENT_SYSTEM_MESSAGE[purpose]
        
        # We provide the current summary and the new input as context.
        messages = [
            {"role": "system", "content": summary_system_message},
            {"role": "assistant", "content": current_summary_purpose},
            {"role": "user", "content": user_input}
        ]

        completion = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            max_tokens=500,
            temperature=0,
        )
        ai_response = completion.choices[0].message.content
        return ai_response

    except Exception as e:
        return f"Error generating summary: {str(e)}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        bot_purpose = sys.argv[1]
        user_text = sys.stdin.read()
        test_summary_array = {
            "objective": "", "outcomes": "", "pedagogy": "",
            "development": "", "implementation": "", "evaluation": ""
        }
        json_output, test_summary_array = get_openai_reply(user_text, bot_purpose, test_summary_array)
        print(json_output)
        print(test_summary_array)
    else:
        error_msg = {"type": "error", "summary": "Internal Server Error: Incorrect number of arguments for standalone script."}
        sys.stderr.write(json.dumps(error_msg))
