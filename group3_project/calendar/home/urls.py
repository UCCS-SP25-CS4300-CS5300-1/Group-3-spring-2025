from django.urls import path, include
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from .views import index, fetch_assignments, calendar_view, clear_calendar, courses_list, course_detail, assignment_detail, wipe_saved
=======
from .views import index, fetch_assignments, calendar_view, clear_calendar, courses_list, course_detail, assignment_detail
>>>>>>> a53e999 (Updated tests and added modules)
=======
from .views import index, fetch_assignments, calendar_view, clear_calendar, courses_list, course_detail, assignment_detail, wipe_saved
>>>>>>> 41308aa (Added a full clear button)
=======
from .views import index, fetch_assignments, calendar_view, clear_calendar, courses_list, course_detail, assignment_detail, wipe_saved
>>>>>>> refs/remotes/origin/NoteUploading

urlpatterns = [
    path('', index, name='index'),
    path('fetch-assignments/', fetch_assignments, name='fetch_assignments'),
    path('calendar_app/', calendar_view, name='calendar_view'), 
    path('clear-calendar/', clear_calendar, name='clear_calendar'),
    path('modules/', courses_list, name='courses_list'),  # List of courses (modules page)
    path('course/<str:course_name>/', course_detail, name='course_detail'),
    path('assignment/<int:assignment_id>/', assignment_detail, name='assignment_detail'),
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    path('wipe_saved/', wipe_saved, name='wipe_saved'),
=======
>>>>>>> a53e999 (Updated tests and added modules)
=======
    path('wipe_saved/', wipe_saved, name='wipe_saved'),
>>>>>>> 41308aa (Added a full clear button)
=======
    path('wipe_saved/', wipe_saved, name='wipe_saved'),
>>>>>>> refs/remotes/origin/NoteUploading
]

