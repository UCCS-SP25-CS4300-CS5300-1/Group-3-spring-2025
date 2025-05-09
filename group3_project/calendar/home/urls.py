from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    index,
    register,
    fetch_assignments,
    calendar_view,
    clear_calendar,
    courses_list,
    course_detail,
    assignment_detail,
    wipe_saved,
    add_event,
    user_settings,
)

urlpatterns = [
    path('', index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
    path('fetch-assignments/', fetch_assignments, name='fetch_assignments'),
    path('calendar_app/', calendar_view, name='calendar_view'),
    path('clear-calendar/', clear_calendar, name='clear_calendar'),
    path('modules/', courses_list, name='courses_list'),  # List of courses (modules page)
    path("course/<path:course_name>/", course_detail, name="course_detail"),
    path('assignment/<int:assignment_id>/', assignment_detail, name='assignment_detail'),
    path('wipe_saved/', wipe_saved, name='wipe_saved'),
    path('add_event/', add_event, name='add_event'),
    path('settings/', user_settings, name='user_settings'),
    path(
        'settings/password-change/',
        auth_views.PasswordChangeView.as_view(template_name='home/password_change.html'),
        name='password_change'
    ),
    path(
        'settings/password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='home/password_change_done.html'),
        name='password_change_done'
    ),
]
