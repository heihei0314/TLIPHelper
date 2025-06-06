# guide/models.py
from django.db import models

class ProposalStep(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(
        help_text="A brief explanation of what the user needs to do in this step."
    )
    guidance_points = models.TextField(
        help_text="Provide bullet points for guidance. Enter one point per line."
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="The order in which the step should appear (e.g., 1, 2, 3)."
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.title}"