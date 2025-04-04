from django.urls import path, include
from .views import index, fetch_assignments, calendar_view, clear_calendar, courses_list, course_detail, assignment_detail

urlpatterns = [
    path('', index, name='index'),
    path('fetch-assignments/', fetch_assignments, name='fetch_assignments'),
    path('calendar_app/', calendar_view, name='calendar_view'), 
    path('clear-calendar/', clear_calendar, name='clear_calendar'),
    path('modules/', courses_list, name='courses_list'),  # List of courses (modules page)
    path('course/<str:course_name>/', course_detail, name='course_detail'),
    path('assignment/<int:assignment_id>/', assignment_detail, name='assignment_detail'),
]

