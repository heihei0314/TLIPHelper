# guide/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ProposalStep

def proposal_guide_view(request):
    """
    Renders the main proposal guide page.
    """
    steps = ProposalStep.objects.all()
    # Get completed steps from the user's session, default to an empty list
    completed_step_ids = request.session.get('completed_steps', [])

    context = {
        'steps': steps,
        'completed_step_ids': completed_step_ids,
    }
    return render(request, 'guide/proposal_guide.html', context)

@require_POST
def toggle_step_status(request, step_id):
    """
    Toggles the completion status of a step in the user's session.
    This view is intended to be called via AJAX.
    """
    # Get the list of completed steps from the session
    completed_ids = request.session.get('completed_steps', [])
    
    # Check if the step is already completed
    if step_id in completed_ids:
        # If yes, remove it (mark as incomplete)
        completed_ids.remove(step_id)
    else:
        # If no, add it (mark as complete)
        completed_ids.append(step_id)
    
    # Save the updated list back to the session
    request.session['completed_steps'] = completed_ids
    
    # Respond with JSON indicating success and the new count
    return JsonResponse({
        'status': 'ok',
        'completed_count': len(completed_ids)
    })