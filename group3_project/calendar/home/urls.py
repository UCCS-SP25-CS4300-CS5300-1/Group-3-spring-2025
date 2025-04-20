from django.urls import path, include
from .views import *
from django.contrib.auth import views as auth_views
from . import views as home_views

urlpatterns = [
    path('', index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', home_views.register, name='register'),
    path('fetch-assignments/', fetch_assignments, name='fetch_assignments'),
    path('calendar_app/', calendar_view, name='calendar_view'), 
    path('clear-calendar/', clear_calendar, name='clear_calendar'),
    path('modules/', courses_list, name='courses_list'),  # List of courses (modules page)
    path('course/<str:course_name>/', course_detail, name='course_detail'),
    path('assignment/<int:assignment_id>/', assignment_detail, name='assignment_detail'),
    path('wipe_saved/', wipe_saved, name='wipe_saved'),
    path('home_settings/', home_settings, name='home_settings'),
]

