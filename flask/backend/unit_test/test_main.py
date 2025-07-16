import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Adjust sys.path to allow importing from the parent directory (backend)
# Now it needs to go up two levels to reach the project root, then down into backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the project python files be tested
from main import get_openai_reply
from prompts import SYSTEM_PROMPTS, JSON_RESPONSE_FORMAT_INSTRUCTION

class TestMain(unittest.TestCase):

    # Define a common mock response for the AI when it returns summary and options
    MOCK_AI_SUMMARY_OPTIONS_RESPONSE = {
        "follow_up_question": "Can you elaborate further?",
        "summary": "This is a summarized response.",
        "new_options": ["Option A", "Option B", "Option C"]
    }

    # Define a common mock response for the AI when it's the integrator
    MOCK_AI_INTEGRATOR_RESPONSE = "This is the final integrated proposal."

    # This method runs before each test
    def setUp(self):
        # Patch os.getenv to control environment variables during tests
        self.getenv_patcher = patch('os.getenv')
        self.mock_getenv = self.getenv_patcher.start()
        self.mock_getenv.side_effect = self._mock_getenv_values

        # Patch AzureOpenAI client and its chat.completions.create method
        self.openai_patcher = patch('main.AzureOpenAI')
        self.mock_openai_client = self.openai_patcher.start()
        self.mock_completion_create = self.mock_openai_client.return_value.chat.completions.create

        # Initialize a fresh summary_array for each test
        self.initial_summary_array = {
            "objective": "", "outcomes": "", "pedagogy": "",
            "development": "", "implementation": "", "evaluation": ""
        }

    # Helper for mocking os.getenv
    def _mock_getenv_values(self, key):
        if key == "AZURE_OPENAI_API_KEY": return "dummy_key"
        if key == "AZURE_OPENAI_ENDPOINT": return "https://dummy.openai.azure.com/"
        if key == "AZURE_OPENAI_API_VERSION": return "2024-02-15-preview"
        if key == "AZURE_OPENAI_DEPLOYMENT_NAME": return "dummy-deployment"
        return None # For other environment variables

    # This method runs after each test
    def tearDown(self):
        self.getenv_patcher.stop()
        self.openai_patcher.stop()

    def _set_mock_ai_response(self, content, is_json=True):
        """Helper to set the mock AI response content."""
        mock_choice = MagicMock()
        if is_json:
            mock_choice.message.content = json.dumps(content)
        else:
            mock_choice.message.content = content
        self.mock_completion_create.return_value.choices = [mock_choice]

    def test_initial_question_retrieval(self):
        """Test that the initial question and options are returned for an empty user input."""
        purpose = "objective"
        user_input = ""
        response_str, updated_summary = get_openai_reply(user_input, purpose, self.initial_summary_array.copy())
        response_data = json.loads(response_str)

        self.assertEqual(response_data["type"], "question")
        self.assertEqual(response_data["question"], SYSTEM_PROMPTS[purpose]["initial_question"])
        self.assertEqual(response_data["options"], SYSTEM_PROMPTS[purpose]["options"])
        self.assertDictEqual(updated_summary, self.initial_summary_array) # Summary should not change

    def test_ai_summary_and_options_response(self):
        """Test parsing of AI response with summary and options."""
        purpose = "outcomes"
        user_input = "I want students to analyze case studies."
        self._set_mock_ai_response(self.MOCK_AI_SUMMARY_OPTIONS_RESPONSE)

        response_str, updated_summary = get_openai_reply(user_input, purpose, self.initial_summary_array.copy())
        response_data = json.loads(response_str)

        self.assertEqual(response_data["type"], "summary_and_options")
        self.assertEqual(response_data["summary"], self.MOCK_AI_SUMMARY_OPTIONS_RESPONSE["summary"])
        self.assertEqual(response_data["follow_up_question"], self.MOCK_AI_SUMMARY_OPTIONS_RESPONSE["follow_up_question"])
        self.assertEqual(response_data["new_options"], self.MOCK_AI_SUMMARY_OPTIONS_RESPONSE["new_options"])
        self.assertEqual(updated_summary[purpose], self.MOCK_AI_SUMMARY_OPTIONS_RESPONSE["summary"]) # Check if summary is stored

    def test_integrator_purpose_response(self):
        """Test AI response for the 'integrator' purpose."""
        purpose = "integrator"
        user_input = json.dumps({"objective": "obj summary", "outcomes": "out summary"}) # Mock previous summaries
        self._set_mock_ai_response(self.MOCK_AI_INTEGRATOR_RESPONSE, is_json=False) # Integrator returns plain text

        response_str, updated_summary = get_openai_reply(user_input, purpose, self.initial_summary_array.copy())
        response_data = json.loads(response_str)

        self.assertEqual(response_data["type"], "summary_only")
        self.assertEqual(response_data["summary"], self.MOCK_AI_INTEGRATOR_RESPONSE)
        self.assertDictEqual(updated_summary, self.initial_summary_array) # Integrator doesn't update its own summary

    def test_invalid_purpose(self):
        """Test handling of an invalid purpose."""
        purpose = "non_existent_purpose"
        user_input = "Some input."
        response_str, updated_summary = get_openai_reply(user_input, purpose, self.initial_summary_array.copy())
        response_data = json.loads(response_str)

        self.assertEqual(response_data["type"], "error")
        self.assertIn("Invalid purpose provided", response_data["summary"])
        self.assertDictEqual(updated_summary, self.initial_summary_array)

    def test_json_decode_error(self):
        """Test error handling when AI returns invalid JSON."""
        purpose = "objective"
        user_input = "Some input."
        # Simulate AI returning non-JSON string when JSON is expected
        self._set_mock_ai_response("This is not JSON.", is_json=False)

        response_str, updated_summary = get_openai_reply(user_input, purpose, self.initial_summary_array.copy())
        response_data = json.loads(response_str)

        self.assertEqual(response_data["type"], "error")
        self.assertIn("AI response was not in the expected format", response_data["summary"])
        self.assertDictEqual(updated_summary, self.initial_summary_array)

    @patch('main.AZURE_OPENAI_API_KEY', None) # Temporarily set API key to None for this test
    @patch('main.AZURE_OPENAI_ENDPOINT', None)
    @patch('main.AZURE_OPENAI_API_VERSION', None)
    @patch('main.AZURE_OPENAI_DEPLOYMENT_NAME', None)
    def test_azure_openai_config_error(self):
        """Test error handling when Azure OpenAI configuration is incomplete."""
        # Ensure os.getenv returns None for these specific keys during this test
        self.mock_getenv.side_effect = lambda key: None if key in [
            "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_VERSION", "AZURE_OPENAI_DEPLOYMENT_NAME"
        ] else self._mock_getenv_values(key)

        purpose = "objective"
        user_input = "Some input."
        response_str, updated_summary = get_openai_reply(user_input, purpose, self.initial_summary_array.copy())
        response_data = json.loads(response_str)

        self.assertEqual(response_data["type"], "error")
        self.assertIn("Azure OpenAI configuration is incomplete", response_data["summary"])
        self.assertDictEqual(updated_summary, self.initial_summary_array)

    def test_summary_array_context_passing(self):
        """Test that current_summary_array is correctly passed and updated."""
        # Simulate some previous steps being completed
        pre_filled_summary = {
            "objective": "To improve student motivation.",
            "outcomes": "Students will complete tasks.",
            "pedagogy": "", "development": "", "implementation": "", "evaluation": ""
        }
        purpose = "pedagogy"
        user_input = "I want an experiential learning approach."
        self._set_mock_ai_response(self.MOCK_AI_SUMMARY_OPTIONS_RESPONSE)

        response_str, updated_summary = get_openai_reply(user_input, purpose, pre_filled_summary.copy())
        response_data = json.loads(response_str)

        self.assertEqual(updated_summary["objective"], "To improve student motivation.")
        self.assertEqual(updated_summary["outcomes"], "Students will complete tasks.")
        self.assertEqual(updated_summary[purpose], self.MOCK_AI_SUMMARY_OPTIONS_RESPONSE["summary"])
        # Verify that the system message sent to OpenAI includes previous summaries
        # This requires inspecting the mock_completion_create call arguments
        call_args = self.mock_completion_create.call_args
        system_message = call_args.kwargs['messages'][0]['content']
        self.assertIn("objective: To improve student motivation.", system_message)
        self.assertIn("outcomes: Students will complete tasks.", system_message)
        self.assertIn(SYSTEM_PROMPTS[purpose]["persona"], system_message)


if __name__ == '__main__':
    unittest.main()
