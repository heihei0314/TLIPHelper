import sys
import os
import json # Import the JSON library
from openai import AzureOpenAI
from dotenv import load_dotenv

# The persona now explicitly instructs the AI to return a JSON object with a summary AND new options.
JSON_RESPONSE_FORMAT_INSTRUCTION = (
    "Your response MUST be a valid JSON object. It must have three keys: "
    "'follow_up_question' (a string containing follow-up question based on your persona), "
    "'summary' (a string containing your summarized response based on your persona. Your summary must only include the result/decisions discussed, not the conversation history.) and "
    "'suggested_questions' (an array of 3-4 distinct, concise string options that the user could "
    "choose to further refine or challenge your summary)."
)

# Each prompt is now a dictionary containing the initial question/options and the persona for summarizing.
SYSTEM_PROMPTS = {
    "objective": {
        "initial_question": "What is the primary goal of your project?",
        "options": ["Improve student motivation", "Enhance learning effectiveness", "Foster collaboration & communication", "Develop critical thinking skills"],
        "persona": "You are a strategic educational consultant. The user has stated their primary project objective. Summarize and affirm their choice in a concise, encouraging statement, confirming it as the core mission. Ask a follow-up question to help the user refine their objective. If user already have a solid objective, ask if he/she has any other objectives. If they don't have any other objectives, you should encourage them to move on the next step (another chatbot), which defining the intented learning outcomes."
        f"{JSON_RESPONSE_FORMAT_INSTRUCTION}"
    },
    "outcomes": {
        "initial_question": "Based on your objective, which coure(s) are you targeting on, and what should learners be able to DO after the project?",
        "options": [
            "The learner, when presented with a case study, will be able to analyze it by identifying its root causes and effects.",
            "The student, using provided software, will create an original digital artifact that meets criteria on a project rubric.",
            "The project team, given three proposed solutions, will evaluate them using a decision matrix and recommend the best option.",
            "The trainee, following a procedure, will be able to demonstrate a specific skill within a set timeframe and without errors."
        ],
        "persona": "You are an instructional designer. The user has described a desired behavior. Convert this into a formal learning outcome summary using the ABCD model (Audience, Behavior, Condition, Degree) as a framework for your summary. The suggested_questions must following the ABCD model. Ask a follow-up question to help the user refine their outcomes. If user already have a solid intented learning outcomes, ask if he/she has any other learning outcomes. If they don't have any other, you should encourage them to move on the next step (another chatbot), which find the pedagogy or technology to use."
        f"{JSON_RESPONSE_FORMAT_INSTRUCTION}"
    },
    "pedagogy": {
        "initial_question": "How do you envision students learning? What should the experience feel like?",
        "options": ["Through immersive, hands-on practice (Experiential Learning)", "By solving a real-world problem (Project-Based Learning)", "By discovering answers themselves (Inquiry-Based Learning)"],
        "persona": "You are a teaching expert in higher education. The user has decided their intended learning outcomes. Suggest 1-2 suitable pedagogical approach and/or specific technologies (e.g., VR, AI-Tutor, AR, Simulation) that perfectly align with the intended learning outcomes. Explaining the advantage and limitation of the chosen pedagogy and technology. Ask a follow-up question to help the user refine their pedagogy. If user already have a solid pedagogy, you should encourage them to move on the next step (another chatbot), which plan the development of the project."
        f"{JSON_RESPONSE_FORMAT_INSTRUCTION}"
    },
    "development": {
        "initial_question": "What is the most critical first step to begin building this project?",
        "options": ["Research similar projects or academic references to identify gaps and opportunities.", "Define core features, user stories, algin with the learning objectives and intented learning outcomes.", "List key content, data, or educational materials needed.", "Outline the technical platform (e.g., Web, Mobile App, Oculus, Tablet)."],
        "persona": "You are a project manager and software engineer. The user is initiating an educational innovation project. Confirm their starting point, frame it as the foundation of the Requirement Specification phase, and guide them through a structured development process with required features, a timeline, platform suggestions, and hiring plan. Encouraging open ideation and grounding the project in solid references and course materials. Ask a follow-up question to help the user refine their development. If user already have a solid development plan, you should encourage them to move on the next step (another chatbot), which plan the implementation of the project."
        f"{JSON_RESPONSE_FORMAT_INSTRUCTION}"
    },
    "implementation": {
        "initial_question": "What is the biggest challenge to successfully rolling this out to students?",
        "options": ["Training instructors on the new tool/method", "Integrating with our current LMS", "Scheduling and student onboarding logistics", "Ensuring adequate technical support"],
        "persona": "You are a teaching expert in higher education. The user has identified a key implementation challenge. Acknowledge this challenge and summarize it as a critical action item in the implementation plan. Ask a follow-up question to help the user refine their implementation."
        f"{JSON_RESPONSE_FORMAT_INSTRUCTION}"
    },
    "evaluation": {
        "initial_question": "How will you know if the project was successful?",
        "options": ["By measuring knowledge change (e.g., pre/post-tests)", "By assessing the quality of student work (e.g., rubrics)", "By gathering student feedback (e.g., surveys)", "By observing student engagement directly"],
        "persona": "You are an educational evaluation expert. The user has chosen an evaluation approach. Summarize this choice and suggest one specific metric and one tool/method that aligns with it (e.g., Metric: 'Score increase on post-test', Tool: 'Validated multiple-choice question bank'). Ask a follow-up question to help the user refine their evaluation."
        f"{JSON_RESPONSE_FORMAT_INSTRUCTION}"
    },
    "integrator": {
        # Integrator doesn't have an initial question, it only summarizes.
        "persona": "You are a Education Innovation Officer. The user has provided a structured set of decisions for an educational project. Synthesize these parts into a single, cohesive, and professional project proposal document. Use clear headings for each section. The final output should be a compelling and actionable plan. If some step(s) are missing, you should encourage the user to go back the previous step(s) and complete them."
    }
}

# Load environment variables and initialize the client ONCE when the script starts.
try:
    # Load credentials (this can be done once outside the function in a real app)
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
    error_msg = json.dumps({"type": "error", "summary": f"Server Configuration Error: {str(e)}"})
    print(error_msg) 
    sys.exit(1)
    
system_message = ""
summary_array = {"objective": "", "outcomes": "", "pedagogy": "", "development": "", "implementation": "", "evaluation": ""}
def get_openai_reply(user_input, purpose):
    config = SYSTEM_PROMPTS.get(purpose)
    if not config:
        return json.dumps({"type": "error", "summary": "Invalid purpose provided."})

    # --- Mode 1: Initial Question ---
    # If user input is empty, provide the guiding question and options.
    if not user_input.strip() and purpose != "integrator":
        response_data = {
            "type": "question",
            "question": config["initial_question"],
            "options": config["options"]
        }
        return json.dumps(response_data)
        
    # Mode 2: Call AI and get a structured response
    try:        
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        # integrate the previous summary into the new prompt
        summary_text = ""
        for key, value in summary_array.items():
            summary_text += key+":"+value+"\n"
        system_message = summary_text+config["persona"]

        # create chat conversation
        completion = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ],
            max_tokens=700,
            temperature=0.6,
        )
        # return the json response
        ai_response_str = completion.choices[0].message.content

        # For the integrator, we just need the summary.
        if purpose == 'integrator':
             response_data = {
                "type": "summary_only", # Match JS expectation
                "summary": ai_response_str
             }
        else:
            # For all other bots, parse the JSON we asked the AI for.
            ai_response_json = json.loads(ai_response_str)
            response_data = {
                "type": "summary_and_options", # Match JS expectation
                "follow_up_question": ai_response_json.get("follow_up_question", "AI did not provide a follow-up question."),
                "summary": ai_response_json.get("summary", "AI did not provide a summary."),
                "suggested_questions": ai_response_json.get("suggested_questions", [])
            }
            summary_array[purpose] = ai_response_json.get("summary", "")

        return json.dumps(response_data)
    
    except json.JSONDecodeError:
        # This catches errors if the AI doesn't return valid JSON
        return json.dumps({"type": "error", "summary": "The AI response was not in the expected format. Please try again."})
    
    except Exception as e:
        return json.dumps({"type": "error", "summary": f"An error occurred: {str(e)}"})


if __name__ == "__main__":
    if len(sys.argv) == 2:
        bot_purpose = sys.argv[1]
        user_text = sys.stdin.read()
        # Print the JSON output
        print(get_openai_reply(user_text, bot_purpose))
    else:
        # Errors should also be JSON for consistency
        error_msg = {"type": "error", "summary": "Internal Server Error: Incorrect number of arguments."}
        sys.stderr.write(json.dumps(error_msg))
        sys.exit(1)