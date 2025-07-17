document.addEventListener('DOMContentLoaded', () => {
    // Keep references
    const allForms = document.querySelectorAll('.chatForm');
    const integrateBtn = document.getElementById('integrateBtn');
    const finalResponseArea = document.getElementById('finalResponseArea');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const botResponseAreas = document.querySelectorAll('.bots-grid .response-area');
    const totalBots = botResponseAreas.length;
    
    // Store initial messages to check for completion
    const initialMessages = Array.from(botResponseAreas).map(el => el.innerHTML);

    // --- Core API function ---
    async function callApi(purpose, userInput = '') {
        const response = await fetch('api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userInput, purpose })
        });
        if (!response.ok) throw new Error(`Server error: ${response.statusText}`);
        return await response.json();
    }

    // --- Function to render options ---
    function renderOptions(optionsAreaEl, options) {
        optionsAreaEl.innerHTML = '';
        if (options && options.length > 0) {
            options.forEach(optionText => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'option-btn';
                button.textContent = optionText;
                optionsAreaEl.appendChild(button);
            });
        }
    }

    // --- NEW: Main function to handle UI updates for a bot ---
    function updateBotUI(form, data) {
        //console.log(data);
        const guidingQuestionEl = form.querySelector('.guiding-question');
        const optionsAreaEl = form.querySelector('.options-area');
        const responseAreaEl = form.nextElementSibling;
        const userInputEl = form.querySelector('.userInput');

        switch (data.type) {
            case 'question':
                typeAnimationCSS(guidingQuestionEl, data.question);
                renderOptions(optionsAreaEl, data.options);
                break;
            case 'summary_and_options':
                typeAnimationCSS(guidingQuestionEl, data.follow_up_question.replace(/\n/g, '<br>'));
            case 'summary_only':                
                responseAreaEl.innerHTML = data.summary.replace(/\n/g, '<br>');
                responseAreaEl.classList.add('completed');
                renderOptions(optionsAreaEl, data.suggested_questions);
                userInputEl.value = ''; // Clear input for next refinement
                userInputEl.focus();
                break;
            case 'error':
                responseAreaEl.textContent = data.summary;
                responseAreaEl.classList.remove('completed');
                break;
        }
    }
    
    // --- Initialize each bot ---
    allForms.forEach((form, index) => {
        const purpose = form.dataset.purpose;
        const responseAreaEl = form.nextElementSibling;

        callApi(purpose)
            .then(data => updateBotUI(form, data))
            .catch(error => {
                console.error('Initialization Error:', error);
                responseAreaEl.textContent = 'Could not load initial question.';
            });

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const userInput = form.querySelector('.userInput').value.trim();
            if (userInput === '') return;
            
            form.querySelector('.submitBtn').disabled = true;
            responseAreaEl.textContent = 'Thinking...';
            responseAreaEl.classList.remove('completed');

            try {
                const data = await callApi(purpose, userInput);
                updateBotUI(form, data);
                updateProgressBar();               
                //console.log('Submission Processing');
            } catch (error) {
                console.error('Submission Error:', error);
                responseAreaEl.textContent = 'An error occurred during submission.';                
                responseAreaEl.classList.remove('completed');
            } finally {
                form.querySelector('.submitBtn').disabled = false;                
                //console.log('Submission Completed');
            }
        });
    });

    // --- Event Delegation for option buttons ---
    document.querySelector('.bots-grid').addEventListener('click', (event) => {
        if (event.target.classList.contains('option-btn')) {
            const form = event.target.closest('form');
            if (form) {
                form.querySelector('.userInput').value = event.target.textContent;
                form.querySelector('.userInput').focus();
            }
        }
    });

    // --- NEW: Updated Progress Bar Logic ---
    function updateProgressBar() {
        let completedCount = 0;
        botResponseAreas.forEach((area, index) => {
            // A step is complete if its content is not the initial default message.
            if (area.innerHTML !== initialMessages[index] && !area.textContent.includes('Thinking...')) {
                completedCount++;
            }
        });
        const percentage = totalBots > 0 ? (completedCount / totalBots) * 100 : 0;
        progressBar.style.width = percentage + '%';
        progressText.textContent = Math.round(percentage) + '% Complete';
    }
    updateProgressBar(); // Initial call

    // --- Integrator Logic (updated to use the new completion check) ---
    integrateBtn.addEventListener('click', async () => {
        const allResponses = [];
        const botTitles = document.querySelectorAll('.bots-grid .container h2');

        botResponseAreas.forEach((area, index) => {
            if (area.innerHTML !== initialMessages[index] && !area.textContent.includes('Thinking...')) {
                const title = botTitles[index].textContent;
                allResponses.push(`--- ${title} ---\n${area.innerText}`);
            }
        });

        if (allResponses.length === 0) {
            finalResponseArea.textContent = "Please complete some steps first.";
            return;
        }

        finalResponseArea.textContent = 'Synthesizing...';
        integrateBtn.disabled = true;

        try {
            const data = await callApi('integrator', allResponses.join('\n\n'));
            if(data.type.startsWith('summary')) {
                finalResponseArea.innerHTML = data.summary.replace(/\n/g, '<br>');
            } else {
                throw new Error(data.summary || 'Integration failed');
            }
        } catch (error) {
            console.error('Integration Error:', error);
            finalResponseArea.textContent = 'Sorry, an error occurred during integration.';
        } finally {
            integrateBtn.disabled = false;
        }
    });
});


/**
 * Triggers a CSS-based typing animation on an element.
 * @param {HTMLElement} element - The HTML element to type into.
 * @param {string} text - The text to display.
 */
function typeAnimationCSS(element, text) {
    // 1. Set the text content all at once. It will be hidden by the animation's initial state.
    element.textContent = text;
    element.classList.remove('is-typing-css'); // Reset in case of quick re-triggering

    // 2. "Tell" CSS how many characters there are and calculate a dynamic duration.
    const charCount = text.length;
    // Set a dynamic speed, e.g., 50ms per character.
    const durationInSeconds = charCount * 0.05; 

    element.style.setProperty('--char-count', charCount);
    // Ensure a minimum duration so very short text is still readable.
    element.style.setProperty('--typing-duration', `${Math.max(durationInSeconds, 0.5)}s`);

    // 3. Add the class to start the animation.
    // Use a tiny delay to ensure the browser has time to apply the new text and styles.
    requestAnimationFrame(() => {
        element.classList.add('is-typing-css');
    });

    // 4. IMPORTANT: Clean up after the animation is done.
    // We listen for the 'animationend' event to remove the class, which stops the blinking.
    element.addEventListener('animationend', (e) => {
        // Make sure we're responding to the 'typing' animation, not 'blink'
        if (e.animationName === 'typing') {
            element.classList.remove('is-typing-css');
            // Remove the temporary styles so they don't affect future animations
            element.style.removeProperty('--char-count');
            element.style.removeProperty('--typing-duration');
        }
    }, { once: true }); // The { once: true } option is crucial for cleanup!
}