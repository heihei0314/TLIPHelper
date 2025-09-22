import os
import json
from openai import AzureOpenAI
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# --- Configuration ---
# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(dotenv_path=dotenv_path)

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_EVAL_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), '../rag_db')
DATASET_PATH = os.path.join(os.path.dirname(__file__), 'golden_dataset.json')

# --- Core RAG Logic (Re-used from main.py) ---
class RAG_CONTEXT_MANAGER:
    """Manages the RAG pipeline for retrieving context."""
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
        docs = self.retriever.invoke(query)
        return " ".join([doc.page_content for doc in docs])

# --- Evaluation Functions ---

def run_rag_pipeline(query, rag_manager, client):
    """Simulates the RAG pipeline to get a generated answer."""
    retrieved_context = rag_manager.get_relevant_context(query)
    
    # Prompt the LLM to generate an answer based on the retrieved context
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Only use the provided context to answer the user's question. If the context does not contain the answer, state that you cannot answer based on the information provided."},
        {"role": "user", "content": f"Context: {retrieved_context}\n\nQuestion: {query}"}
    ]
    
    completion = client.chat.completions.create(
        model=AZURE_OPENAI_EVAL_DEPLOYMENT_NAME,
        messages=messages,
        max_tokens=256,
        temperature=0.1
    )
    return completion.choices[0].message.content, retrieved_context

def evaluate_answer(query, generated_answer, retrieved_context, ground_truth, client):
    """Evaluates the generated answer using an LLM as a judge."""
    # This prompt asks the LLM to evaluate the answer's factual accuracy and faithfulness
    eval_prompt = f"""
    You are an expert evaluator. Your task is to rate the quality of a generated answer based on the provided question, ground truth, and context.

    **Question:** {query}
    **Generated Answer:** {generated_answer}
    **Ground Truth:** {ground_truth}
    **Retrieved Context:** {retrieved_context}

    Evaluate the following metrics and provide a score from 0.0 to 1.0 for each:
    1. **Factual Accuracy:** Does the Generated Answer factually agree with the Ground Truth and Retrieved Context?
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

# --- Main Execution ---

if __name__ == "__main__":
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
            golden_dataset = json.load(f)["golden_dataset"]

        total_scores = {"factual_accuracy": 0, "faithfulness": 0, "relevance": 0}
        num_evaluated = 0

        # 3. Run evaluation loop
        print("\n--- Starting RAG Pipeline Evaluation ---")
        for item in golden_dataset:
            query = item["query"]
            ground_truth = item["ground_truth"]

            # Run the RAG pipeline for the given query
            generated_answer, retrieved_context = run_rag_pipeline(query, rag_manager, eval_client)

            # Evaluate the generated answer
            eval_scores = evaluate_answer(query, generated_answer, retrieved_context, ground_truth, eval_client)

            if eval_scores:
                print(f"\nQuery: {query}")
                print(f"  Generated Answer: {generated_answer}")
                print(f"  Factual Accuracy: {eval_scores['factual_accuracy']:.2f}")
                print(f"  Faithfulness: {eval_scores['faithfulness']:.2f}")
                print(f"  Relevance: {eval_scores['relevance']:.2f}")

                total_scores["factual_accuracy"] += eval_scores['factual_accuracy']
                total_scores["faithfulness"] += eval_scores['faithfulness']
                total_scores["relevance"] += eval_scores['relevance']
                num_evaluated += 1
            else:
                print(f"\nSkipping evaluation for query: {query} due to an error.")

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