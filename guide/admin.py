# guide/admin.py
from django.contrib import admin
from .models import ProposalStep

@admin.register(ProposalStep)
class ProposalStepAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)