document.addEventListener('DOMContentLoaded', function() {
    const chatForms = document.querySelectorAll('.chatForm');
    const integrateBtn = document.getElementById('integrateBtn');
    const finalResponseArea = document.getElementById('finalResponseArea');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const nextStepArrows = document.querySelectorAll('.next-step-arrow'); // Select all next step arrows

    // Store the current summaries for each purpose
    // This will be sent with each request to the backend to maintain context
    let currentSummaries = {
        "objective": "",
        "outcomes": "",
        "pedagogy": "",
        "development": "",
        "implementation": "",
        "evaluation": ""
    };

    // Function to update progress bar
    function updateProgressBar() {
        const completedSteps = Object.values(currentSummaries).filter(summary => summary !== "").length;
        const totalSteps = Object.keys(currentSummaries).length;
        const progress = (completedSteps / totalSteps) * 100;
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}% Complete`;
    }

    // Function to display messages (guiding question or summary)
    function displayMessage(formElement, data) {
        // Determine the correct elements based on whether it's a form or the final integration section
        let guidingQuestionDiv, optionsArea, responseArea, userInputField;

        if (formElement.classList.contains('chatForm')) {
            guidingQuestionDiv = formElement.querySelector('.guiding-question');
            optionsArea = formElement.querySelector('.options-area');
            responseArea = formElement.parentElement.querySelector('.response-area');
            userInputField = formElement.querySelector('.userInput');
        } else { // This is for the final integration section
            guidingQuestionDiv = null; // No guiding question for final summary
            optionsArea = null; // No options for final summary
            responseArea = formElement.querySelector('#finalResponseArea'); // Directly target finalResponseArea
            userInputField = null; // No user input for final summary
        }


        if (data.type === 'question') {
            if (guidingQuestionDiv) guidingQuestionDiv.textContent = data.question;
            if (optionsArea) {
                optionsArea.innerHTML = ''; // Clear previous options
                optionsArea.classList.remove('hidden-dynamic');
                data.options.forEach(optionText => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.classList.add('option-button');
                    button.textContent = optionText;
                    button.addEventListener('click', () => {
                        if (userInputField) userInputField.value = optionText;
                        formElement.requestSubmit(); // Programmatically submit the form
                    });
                    optionsArea.appendChild(button);
                });
            }
            if (responseArea) responseArea.textContent = ''; // Clear previous summary
        } else if (data.type === 'summary_and_options') {
            if (guidingQuestionDiv) guidingQuestionDiv.textContent = data.follow_up_question;
            if (responseArea) responseArea.textContent = data.summary;
            if (optionsArea) {
                optionsArea.innerHTML = ''; // Clear previous options
                optionsArea.classList.remove('hidden-dynamic');
                data.new_options.forEach(optionText => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.classList.add('option-button');
                    button.textContent = optionText;
                    button.addEventListener('click', () => {
                        if (userInputField) userInputField.value = optionText;
                        formElement.requestSubmit(); // Programmatically submit the form
                    });
                    optionsArea.appendChild(button);
                });
            }
            if (userInputField) userInputField.value = ''; // Clear input field after submission
            currentSummaries[formElement.dataset.purpose] = data.summary; // Store summary
            updateProgressBar();
        } else if (data.type === 'summary_only') {
            if (finalResponseArea) finalResponseArea.textContent = data.summary;
            // No options or guiding question for integrator
        } else if (data.type === 'error') {
            if (responseArea) responseArea.textContent = `Error: ${data.summary}`;
            console.error('API Error:', data.summary);
        }
    }

    // Function to handle form submission
    async function handleSubmit(event) {
        event.preventDefault();
        const form = event.target;
        const userInputField = form.querySelector('.userInput');
        const purpose = form.dataset.purpose;
        const userInput = userInputField.value;
        const submitBtn = form.querySelector('.submitBtn');

        submitBtn.disabled = true; // Disable button to prevent multiple submissions
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>'; // Show loading spinner

        try {
            const response = await fetch('/api/chat', { // New Flask endpoint
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    userInput: userInput,
                    purpose: purpose
                }),
            });

            const data = await response.json();
            displayMessage(form, data);

            // If it's a summary and options, clear the input field
            if (data.type === 'summary_and_options') {
                userInputField.value = '';
            }

        } catch (error) {
            console.error('Fetch error:', error);
            const responseArea = form.parentElement.querySelector('.response-area');
            responseArea.textContent = `Network Error: Could not connect to the server. ${error.message}`;
        } finally {
            submitBtn.disabled = false; // Re-enable button
            submitBtn.innerHTML = '<i data-lucide="send">Send</i>'; // Restore icon
            lucide.createIcons(); // Re-render lucide icons after content change
        }
    }

    // Attach event listeners to all chat forms
    chatForms.forEach(form => {
        form.addEventListener('submit', handleSubmit);
        // Trigger initial question load for each form on page load
        handleSubmit({ preventDefault: () => {}, target: form });
    });

    // Handle the final integration button click
    integrateBtn.addEventListener('click', async () => {
        finalResponseArea.textContent = 'Generating final proposal...';
        integrateBtn.disabled = true;
        integrateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Synthesizing...';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    userInput: JSON.stringify(currentSummaries), // Send all collected summaries
                    purpose: 'integrator'
                }),
            });

            const data = await response.json();
            // Pass the integration-section element to displayMessage
            displayMessage(document.getElementById('integration-section'), data);

        } catch (error) {
            console.error('Integration fetch error:', error);
            finalResponseArea.textContent = `Network Error during integration: ${error.message}`;
        } finally {
            integrateBtn.disabled = false;
            integrateBtn.innerHTML = '<i data-lucide="file-check-2"></i>Synthesize';
            lucide.createIcons();
        }
    });

    // Add event listeners for the next step arrows
    nextStepArrows.forEach(arrow => {
        arrow.addEventListener('click', () => {
            const nextStepId = arrow.dataset.nextStep;
            if (nextStepId) {
                const nextElement = document.getElementById(nextStepId);
                if (nextElement) {
                    nextElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });

    // Initial progress bar update
    updateProgressBar();
});
