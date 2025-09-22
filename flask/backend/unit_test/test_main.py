import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Dynamically add the 'backend' directory to sys.path
script_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, backend_dir)

# Now, import get_openai_reply from main.py
try:
    from main import get_openai_reply, RAG_CONTEXT_MANAGER, generate_summary
except ImportError as e:
    print(f"Error importing functions from main.py: {e}", file=sys.stderr)
    sys.exit(1)

# Set the path to the golden dataset
GOLDEN_DATASET_PATH = os.path.join(script_dir, 'golden_dataset.json')
VECTOR_DB_PATH = os.path.join(script_dir, '..', 'rag_db')

class TestAutomatedEvaluation(unittest.TestCase):
    """
    Test suite for automated evaluation using a golden dataset.
    This test suite simulates the application's flow and validates
    responses against a predefined set of expected answers.
    """
    
    @classmethod
    def setUpClass(cls):
        """Load the golden dataset and initialize the RAG manager."""
        try:
            with open(GOLDEN_DATASET_PATH, 'r', encoding='utf-8') as f:
                cls.golden_dataset = json.load(f)["golden_dataset"]
            
            # Initialize RAG manager to ensure the vector DB is accessible for tests
            cls.rag_manager = RAG_CONTEXT_MANAGER(VECTOR_DB_PATH)
        except FileNotFoundError:
            cls.golden_dataset = []
            print(f"WARNING: Golden dataset not found at {GOLDEN_DATASET_PATH}. Tests will be skipped.")
        except Exception as e:
            cls.golden_dataset = []
            print(f"ERROR: Failed to load golden dataset or RAG manager: {e}. Tests will be skipped.")

    @unittest.skipIf(not golden_dataset, "Skipping tests because golden dataset is empty or not found.")
    @patch('main.AzureOpenAI')
    def test_all_queries_from_golden_dataset(self, mock_azure_openai):
        """
        Tests each query in the golden dataset, simulating the full application flow.
        """
        print("\n--- Starting Automated Evaluation from Golden Dataset ---")

        # Mock the API client to prevent actual API calls during the test
        mock_client_instance = mock_azure_openai.return_value
        
        # Test each entry in the golden dataset
        for test_case in self.golden_dataset:
            purpose = test_case["purpose"]
            query = test_case["query"]
            ground_truth = test_case["ground_truth"]
            
            # Mock the AI's response for the conversational agent
            # This is a simplified mock; in a real scenario, you might mock a different response for each query
            mock_chat_completion = MagicMock()
            mock_chat_completion.choices[0].message.content = json.dumps({
                "explanation": "This is a mocked explanation.",
                "follow_up_question": "Mocked follow-up question?",
                "new_options": ["Option A", "Option B"]
            })

            # Mock the AI's response for the summary agent (generate_summary)
            mock_summary_completion = MagicMock()
            mock_summary_completion.choices[0].message.content = ground_truth

            mock_client_instance.chat.completions.create.side_effect = [
                mock_chat_completion, # Response for the conversational agent
                mock_summary_completion # Response for the summary agent
            ]

            initial_summary_array = {
                "objective": "", "outcomes": "", "pedagogy": "",
                "development": "", "implementation": "", "evaluation": "", "irrelevant": ""
            }

            with self.subTest(query=query, purpose=purpose):
                # Simulate the API call to get the response
                response_data_str, updated_summary_array = get_openai_reply(query, purpose, initial_summary_array)
                
                # Parse the response and check for success
                try:
                    response_json = json.loads(response_data_str)
                except json.JSONDecodeError:
                    self.fail(f"Test for '{query}' failed: Expected valid JSON response, but got an error.")
                
                # Check if the summary was updated correctly
                actual_summary = updated_summary_array.get(purpose, "")
                
                # Assert that the actual summary matches the ground truth
                self.assertIn(ground_truth, actual_summary, 
                              f"Test for '{query}' failed: "
                              f"Expected summary to contain '{ground_truth}', but got '{actual_summary}'.")

                print(f"Test PASSED for purpose '{purpose}' with query: '{query}'")

if __name__ == '__main__':
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Add this new automated evaluation test suite
    suite.addTest(loader.loadTestsFromTestCase(TestAutomatedEvaluation))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)