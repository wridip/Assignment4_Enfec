from django.urls import path
from . import views

urlpatterns = [
    path('ask', views.ask_question, name='ask'),
    path('metrics', views.get_metrics, name='metrics'),
]
