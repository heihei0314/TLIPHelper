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
# This assumes main.py is directly in the 'backend' directory.
try:
    from main import get_openai_reply
except ImportError as e:
    print(f"Error importing get_openai_reply: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Attempted to import 'main' from: {backend_dir}")
    # This print statement will help in debugging if the import still fails.


# --- API Test (Azure OpenAI) ---
class TestAzureOpenAIAPI(unittest.TestCase):
    """
    Test suite for Azure OpenAI API calls.
    This test is placed first to ensure core API functionality is verified early.
    """
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource-name.openai.azure.com/openai/deployments/your-deployment-name/chat/completions?api-version=2024-02-15-preview")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "YOUR_DEFAULT_API_KEY_IF_NOT_SET")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "your-deployment-name")

    @classmethod
    def setUpClass(cls):
        """
        Set up class-level resources, like checking for environment variables.
        Loads environment variables from a .env file located in the backend folder.
        Assumes test_my_application.py is in /backend/unit_test and .env is in /backend.
        """
        script_dir = os.path.dirname(__file__)
        dotenv_path = os.path.join(script_dir, '..', '.env')
        
        load_dotenv(dotenv_path=dotenv_path)
        print(f"\nAttempting to load .env from: {dotenv_path}")

        cls.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", cls.AZURE_OPENAI_ENDPOINT)
        cls.AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", cls.AZURE_OPENAI_API_KEY)
        cls.AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", cls.AZURE_OPENAI_API_VERSION)
        cls.AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", cls.AZURE_OPENAI_DEPLOYMENT_NAME)

        if not cls.AZURE_OPENAI_ENDPOINT or "your-resource-name" in cls.AZURE_OPENAI_ENDPOINT:
            print("\nWARNING: AZURE_OPENAI_ENDPOINT environment variable not set or still default. API tests may fail.")
            print("Please set AZURE_OPENAI_ENDPOINT to your Azure OpenAI chat completions endpoint in your .env file.")
        if not cls.AZURE_OPENAI_API_KEY or "YOUR_DEFAULT_API_KEY_IF_NOT_SET" in cls.AZURE_OPENAI_API_KEY:
            print("WARNING: AZURE_OPENAI_API_KEY environment variable not set or still default. API tests may fail.")
            print("Please set AZURE_OPENAI_API_KEY to your Azure OpenAI API key in your .env file.")
        if not cls.AZURE_OPENAI_API_VERSION:
            print("WARNING: AZURE_OPENAI_API_VERSION environment variable not set. API tests may fail.")
        if not cls.AZURE_OPENAI_DEPLOYMENT_NAME:
            print("WARNING: AZURE_OPENAI_DEPLOYMENT_NAME environment variable not set. API tests may fail.")

    def test_01_azure_openai_connection(self):
        """
        Verify a successful chat completion call to Azure OpenAI.
        This test name is chosen to match your original test_main.py's connection test.
        """
        print("\nRunning Azure OpenAI API Test: test_01_azure_openai_connection")

        self.assertTrue(self.AZURE_OPENAI_API_KEY, "AZURE_OPENAI_API_KEY is not set")
        self.assertTrue(self.AZURE_OPENAI_ENDPOINT, "AZURE_OPENAI_ENDPOINT is not set")
        self.assertTrue(self.AZURE_OPENAI_API_VERSION, "AZURE_OPENAI_API_VERSION is not set")
        self.assertTrue(self.AZURE_OPENAI_DEPLOYMENT_NAME, "AZURE_OPENAI_DEPLOYMENT_NAME is not set")

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
            self.assertIsNotNone(response, "Azure OpenAI API call failed")
            self.assertTrue(hasattr(response, 'choices'), "Response does not contain choices")
            self.assertGreater(len(response.choices), 0, "No choices found in response")
            self.assertIsNotNone(response.choices[0].message, "First choice message is None")
            self.assertIsNotNone(response.choices[0].message.content, "First choice message content is None")
            self.assertIsInstance(response.choices[0].message.content, str, "Content is not a string")

            print("Azure OpenAI API Test: test_01_azure_openai_connection PASSED")

        except Exception as e:
            self.fail(f"Azure OpenAI connection failed: {str(e)}")

# --- Test suite for get_openai_reply function ---
class TestOpenAIReplyFunction(unittest.TestCase):
    """
    Test suite for the get_openai_reply function's output.
    Dynamically generates tests for each purpose in summary_array.
    """
    # Define the purposes (keys of summary_array) for which to run tests
    PURPOSES = [
        "objective", "outcomes", "pedagogy",
        "development", "implementation", "evaluation"
    ]

    def setUp(self):
        # These values would typically be passed to get_openai_reply
        self.summary_array = {
            "objective": "", "outcomes": "", "pedagogy": "",
            "development": "", "implementation": "", "evaluation": ""
        }
        self.user_input = "Improve student motivation" # A generic input for testing

    # Helper method for testing JSON format
    def _test_json_format(self, purpose):
        print(f"\nRunning get_openai_reply Test: test_output_json_format for purpose '{purpose}'")
        if 'get_openai_reply' not in globals() and 'get_openai_reply' not in locals():
            self.fail("get_openai_reply function not found. Check import path.")
        
        response, _ = get_openai_reply(self.user_input, purpose, self.summary_array)
        try:
            json.loads(response)
            self.assertTrue(True)
            print(f"get_openai_reply Test: test_output_json_format for '{purpose}' PASSED")
        except json.JSONDecodeError:
            self.fail(f"Response for purpose '{purpose}' is not in valid JSON format: {response}")

    # Helper method for testing missing keys
    def _test_missing_keys(self, purpose):
        print(f"Running get_openai_reply Test: test_missing_keys_in_output for purpose '{purpose}'")
        if 'get_openai_reply' not in globals() and 'get_openai_reply' not in locals():
            self.fail("get_openai_reply function not found. Check import path.")

        response, _ = get_openai_reply(self.user_input, purpose, self.summary_array)
        try:
            response_dict = json.loads(response)
            print(response_dict)
        except json.JSONDecodeError:
            self.fail(f"Could not parse JSON for purpose '{purpose}' in missing keys test. Response: {response}")
            
        expected_keys = {"type", "explanation", "follow_up_question", "summary", "suggested_questions"}
        missing_keys = expected_keys - set(response_dict.keys())
        self.assertFalse(missing_keys, f"Missing keys in response for purpose '{purpose}': {missing_keys}")
        print(f"get_openai_reply Test: test_missing_keys_in_output for '{purpose}' PASSED")

# Dynamically create test methods for each purpose
for p in TestOpenAIReplyFunction.PURPOSES:
    # Create test for JSON format
    def create_json_test(purpose_name):
        def test_method(self):
            self._test_json_format(purpose_name)
        return test_method
    setattr(TestOpenAIReplyFunction, f'test_output_json_format_{p}', create_json_test(p))

    # Create test for missing keys
    def create_missing_keys_test(purpose_name):
        def test_method(self):
            self._test_missing_keys(purpose_name)
        return test_method
    setattr(TestOpenAIReplyFunction, f'test_missing_keys_in_output_{p}', create_missing_keys_test(p))


if __name__ == '__main__':
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTest(loader.loadTestsFromTestCase(TestAzureOpenAIAPI))
    suite.addTest(loader.loadTestsFromTestCase(TestOpenAIReplyFunction))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
