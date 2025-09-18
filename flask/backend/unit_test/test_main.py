# test_my_application.py

import unittest
import json
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI

# Dynamically add the 'backend' directory to sys.path
# This assumes test_main.py is in backend/unit_test
# and main.py is in backend/
script_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, backend_dir) # Add backend directory to path

# Now, import get_openai_reply from main.
try:
    from main import get_openai_reply
except ImportError as e:
    print(f"Error importing get_openai_reply: {e}", file=sys.stderr)
    sys.exit(1) # Exit if the core function cannot be imported

# --- API Test (Azure OpenAI) ---
class TestAzureOpenAIAPI(unittest.TestCase):
    """
    Test suite for Azure OpenAI API calls.
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up class-level resources, like checking for environment variables.
        Loads environment variables from a .env file located in the backend folder.
        """
        script_dir = os.path.dirname(__file__)
        dotenv_path = os.path.join(script_dir, '..', '.env')
        load_dotenv(dotenv_path=dotenv_path)

        cls.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        cls.AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        cls.AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
        cls.AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        # Check for placeholder values, which indicate missing configuration
        if not cls.AZURE_OPENAI_ENDPOINT or "your-resource-name" in cls.AZURE_OPENAI_ENDPOINT:
            cls.endpoint_ok = False
            print("\nWARNING: AZURE_OPENAI_ENDPOINT is not configured correctly. API tests will be skipped.")
        else:
            cls.endpoint_ok = True

    @unittest.skipUnless(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                         "Azure OpenAI API credentials are not fully set in .env. Skipping API tests.")
    def test_01_azure_openai_connection(self):
        """
        Verify a successful chat completion call to Azure OpenAI.
        """
        if not self.endpoint_ok:
            self.skipTest("Azure OpenAI endpoint is not configured correctly.")

        print("\nRunning Azure OpenAI API Test: test_01_azure_openai_connection")
        
        try:
            client = AzureOpenAI(
                api_key=self.AZURE_OPENAI_API_KEY,
                azure_endpoint=self.AZURE_OPENAI_ENDPOINT,
                api_version=self.AZURE_OPENAI_API_VERSION,
            )
            response = client.chat.completions.create(
                model=self.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Test connection"}
                ],
                max_tokens=10,
                temperature=0.6,
            )
            self.assertIsNotNone(response, "Azure OpenAI API call failed.")
            self.assertGreater(len(response.choices), 0, "No choices found in response.")
            print("Azure OpenAI API Test: test_01_azure_openai_connection PASSED")
        except Exception as e:
            self.fail(f"Azure OpenAI connection failed: {str(e)}")

# --- Test suite for get_openai_reply function ---
class TestOpenAIReplyFunction(unittest.TestCase):
    """
    Test suite for the get_openai_reply function's output.
    """
    PURPOSES = [
        "objective", "outcomes", "pedagogy",
        "development", "implementation", "evaluation", "integrator"
    ]

    def setUp(self):
        self.summary_array = {
            "objective": "", "outcomes": "", "pedagogy": "",
            "development": "", "implementation": "", "evaluation": ""
        }

    def test_initial_questions(self):
        """
        Test the initial response for each purpose (with no user input).
        """
        for purpose in self.PURPOSES:
            if purpose == 'integrator':
                # Integrator purpose doesn't have an initial question
                continue
            
            with self.subTest(purpose=purpose):
                print(f"\nRunning Test: test_initial_questions for '{purpose}'")
                response, _ = get_openai_reply("", purpose, self.summary_array)
                try:
                    response_dict = json.loads(response)
                    self.assertEqual(response_dict.get("type"), "question")
                    self.assertIn("question", response_dict)
                    self.assertIsInstance(response_dict.get("options"), list)
                    print(f"Test: test_initial_questions for '{purpose}' PASSED")
                except json.JSONDecodeError:
                    self.fail(f"Response for '{purpose}' is not valid JSON: {response}")

    def test_json_and_keys_for_each_purpose(self):
        """
        Test the full AI-generated JSON response for each purpose.
        """
        for purpose in self.PURPOSES:
            with self.subTest(purpose=purpose):
                print(f"\nRunning Test: test_json_and_keys for '{purpose}'")
                user_input = "My project's goal is to improve student collaboration." if purpose != 'integrator' else "Generate proposal"

                response, updated_summary = get_openai_reply(user_input, purpose, self.summary_array.copy())
                try:
                    response_dict = json.loads(response)
                except json.JSONDecodeError:
                    self.fail(f"Response for '{purpose}' is not valid JSON: {response}")

                if purpose == 'integrator':
                    # Special case for the integrator purpose
                    self.assertEqual(response_dict.get("type"), "summary_only")
                    self.assertIn("summary", response_dict)
                else:
                    # General case for all other purposes
                    self.assertEqual(response_dict.get("type"), "summary_and_options")
                    self.assertIn("explanation", response_dict)
                    self.assertIn("follow_up_question", response_dict)
                    self.assertIsInstance(response_dict.get("options"), list)
                    # The response should also include the full_summary_state, as per app.py logic
                    self.assertIn("full_summary_state", updated_summary) 
                
                print(f"Test: test_json_and_keys for '{purpose}' PASSED")


if __name__ == '__main__':
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    # Add the API connection test first
    suite.addTest(loader.loadTestsFromTestCase(TestAzureOpenAIAPI))
    
    # Add the function-level tests
    suite.addTest(loader.loadTestsFromTestCase(TestOpenAIReplyFunction))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)