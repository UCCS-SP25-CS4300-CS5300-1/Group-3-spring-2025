from django.urls import path
from .views import index, fetch_assignments, calendar_view, clear_calendar

urlpatterns = [
    path('', index, name='index'),
    path('fetch-assignments/', fetch_assignments, name='fetch_assignments'),
    path('calendar_app/', calendar_view, name='calendar_view'), 
    path('clear-calendar/', clear_calendar, name='clear_calendar'),
]

