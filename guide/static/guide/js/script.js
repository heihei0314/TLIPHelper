document.addEventListener('DOMContentLoaded', () => {

    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const totalSteps = document.querySelectorAll('.card').length;
    // Get CSRF token from the meta tag in the HTML head
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    /**
     * Updates the progress bar display.
     * @param {number} completedCount - The number of steps currently completed.
     */
    function updateProgress(completedCount) {
        const percentage = totalSteps > 0 ? (completedCount / totalSteps) * 100 : 0;
        
        progressBar.style.width = percentage + '%';
        progressText.textContent = `${Math.round(percentage)}% Complete (${completedCount} of ${totalSteps} steps)`;
    }

    /**
     * Handles the click event on a "complete" button.
     * @param {Event} event - The click event.
     */
    async function handleToggleClick(event) {
        const button = event.target;
        const card = button.closest('.card');
        if (!card) return;

        const stepId = card.dataset.stepId;
        const url = `/toggle-step/${stepId}/`; // The URL for our Django view

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // If the server confirms the action, update the UI
            if (data.status === 'ok') {
                // Toggle visual state of the card
                card.classList.toggle('completed');

                // Update the button text
                if (card.classList.contains('completed')) {
                    button.textContent = 'Mark as Incomplete';
                } else {
                    button.textContent = 'Mark as Complete';
                }

                // Update the progress bar using the count from the server
                updateProgress(data.completed_count);
            }

        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
            alert('Could not update step status. Please try again.');
        }
    }

    // Attach event listeners to all complete buttons
    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', handleToggleClick);
    });
});