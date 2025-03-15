from django.urls import path
from .views import index, calendar_view
urlpatterns = [
    path('', index, name='index'),
     path('calendar/', calendar_view, name='calendar'),
]