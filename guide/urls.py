# guide/urls.py
from django.urls import path
from . import views

app_name = 'guide'

urlpatterns = [
    path('', views.proposal_guide_view, name='proposal_guide'),
    path('toggle-step/<int:step_id>/', views.toggle_step_status, name='toggle_step'),
]