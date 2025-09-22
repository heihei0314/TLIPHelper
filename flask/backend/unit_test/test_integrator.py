import unittest
import json
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI
from unittest.mock import patch, MagicMock
from pathlib import Path

# Dynamically add the 'backend' directory to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, backend_dir)

try:
    from main import get_openai_reply, RAG_CONTEXT_MANAGER, generate_summary
    from prompts import SYSTEM_PROMPTS
except ImportError as e:
    print(f"Error importing functions from main.py: {e}", file=sys.stderr)
    sys.exit(1)




# --- Configuration ---
dotenv_path = os.path.join(script_dir, '../.env')
load_dotenv(dotenv_path=dotenv_path)

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_EVAL_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

VECTOR_DB_PATH = os.path.join(script_dir, '../rag_db')
DATASET_PATH = os.path.join(script_dir, 'integrator_dataset.json')

# --- Evaluation Functions ---

def run_evaluation():
    try:
        # 1. Initialize RAG and OpenAI Client
        rag_manager = RAG_CONTEXT_MANAGER(VECTOR_DB_PATH)
        eval_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
        )

        # 2. Load the golden dataset
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            integrator_dataset = json.load(f)["integrator_dataset"]

        total_scores = {"factual_accuracy": 0, "faithfulness": 0, "relevance": 0}
        num_evaluated = 0

        # 3. Run evaluation loop
        print("\n--- Starting Evaluation ---")
        
        for test_case in integrator_dataset:
            query = test_case["query"]
            purpose = "integrator"
            ground_truth_keywords = test_case["ground_truth_keywords"]
            
            # The summary array contains a full or partial proposal
            current_summary_array = test_case["full_summary_state"]

            # Call main.py's get_openai_reply function
            response_data_str, updated_summary_array = get_openai_reply(query, purpose, current_summary_array.copy())
            
            # --- Printing for Debugging ---
            print(f"\n[DEBUG] --- Test Case: {purpose} | Query: '{query}' ---")
            print("[DEBUG] Response JSON String:")
            print(response_data_str)
            print("[DEBUG] Updated Summary Array:")
            print(json.dumps(updated_summary_array, indent=2))
            print("------------------------------------------")

            try:
                response_json = json.loads(response_data_str)
                generated_answer = response_json.get("summary") or response_json.get("explanation")
                
                # Use the evaluation client to score the answer
                eval_scores = evaluate_answer(current_summary_array, generated_answer, "", ground_truth_keywords, eval_client)

                if eval_scores:
                    print(f"  Factual Accuracy: {eval_scores['factual_accuracy']:.2f}")
                    print(f"  Faithfulness: {eval_scores['faithfulness']:.2f}")
                    print(f"  Relevance: {eval_scores['relevance']:.2f}")

                    total_scores["factual_accuracy"] += eval_scores['factual_accuracy']
                    total_scores["faithfulness"] += eval_scores['faithfulness']
                    total_scores["relevance"] += eval_scores['relevance']
                    num_evaluated += 1
                else:
                    print(f"  Skipping evaluation for query: {query} due to an error.")

            except json.JSONDecodeError:
                print(f"  ERROR: AI response was not valid JSON.")
            except Exception as e:
                print(f"  ERROR: An unexpected error occurred: {e}")

        # 4. Print final results
        if num_evaluated > 0:
            avg_scores = {k: v / num_evaluated for k, v in total_scores.items()}
            print("\n--- Final Average Scores ---")
            print(f"  Average Factual Accuracy: {avg_scores['factual_accuracy']:.2f}")
            print(f"  Average Faithfulness: {avg_scores['faithfulness']:.2f}")
            print(f"  Average Relevance: {avg_scores['relevance']:.2f}")
        else:
            print("\nNo queries were evaluated successfully.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Please ensure you have run rag_builder.py and the dataset file exists.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def evaluate_answer(query, generated_answer, retrieved_context, ground_truth, client):
    """Evaluates the generated answer using an LLM as a judge."""
    # This prompt asks the LLM to evaluate the answer's factual accuracy and faithfulness
    eval_prompt = f"""
    You are an expert evaluator. Your task is to rate the quality of a generated answer based on the provided summary array, ground truth keywords, and context.

    **Question:** {query}
    **Generated Answer:** {generated_answer}
    **Ground Truth Keyords:** {ground_truth}
    **Retrieved Context:** {retrieved_context}

    Evaluate the following metrics and provide a score from 0.0 to 1.0 for each:
    1. **Factual Accuracy:** Does the Generated Answer factually agree with the Ground Truth Keyords and Retrieved Context?
    2. **Faithfulness:** Is the Generated Answer strictly based on the Retrieved Context? (Score 0.0 if any part of the answer is not supported by the context).
    3. **Relevance:** Is the Generated Answer relevant to the initial Question?

    Provide your response as a JSON object with keys "factual_accuracy", "faithfulness", and "relevance". Each value should be a float.
    """
    
    eval_messages = [
        {"role": "system", "content": eval_prompt},
        {"role": "user", "content": f"Evaluate the answer for the question: {query}"}
    ]
    
    try:
        completion = client.chat.completions.create(
            model=AZURE_OPENAI_EVAL_DEPLOYMENT_NAME,
            messages=eval_messages,
            max_tokens=200,
            temperature=0, # Use low temperature for predictable output
            response_format={"type": "json_object"}
        )
        eval_result = json.loads(completion.choices[0].message.content)
        return eval_result
    except json.JSONDecodeError:
        print(f"Warning: Evaluation LLM returned non-JSON response for query: {query}")
        return None
    except Exception as e:
        print(f"Error during evaluation for query '{query}': {e}")
        return None

if __name__ == "__main__":
    run_evaluation()