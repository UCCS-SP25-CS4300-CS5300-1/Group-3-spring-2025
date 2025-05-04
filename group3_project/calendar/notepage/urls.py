from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list, name='note_list'),
    path('new/', views.create_note, name='create_note'),
    path('<int:pk>/', views.note_detail, name='note_detail'),
    path('<int:pk>/edit/', views.edit_note, name='edit_note'),
    path('<int:pk>/delete/', views.delete_note, name='delete_note'),
    path('autosave/', views.autosave_note, name='autosave_note'),
    path('deletetags/', views.delete_tags, name='delete_tags'),
    path('import/', views.import_file, name='import_file'),
    path('api/notes/<int:pk>/content/', views.get_note_content, name='get_note_content'),
    path('api/summarize/', views.summarize_note, name='summarize_note'),
    path('quiz/', views.multi_note_quiz_page, name='multi_note_quiz_page'),
    path('api/generate_multi_note_quiz/', views.generate_multi_note_quiz, name='generate_multi_note_quiz'),
]
