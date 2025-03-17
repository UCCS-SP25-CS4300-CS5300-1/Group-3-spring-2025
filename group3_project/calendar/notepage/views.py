# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import Note
from .forms import NoteForm
from taggit.models import Tag
import json

def note_list(request):
    tags = Tag.objects.all()
    search_query = request.GET.get('search', '')
    tag_query = request.GET.get('tag', '')
    
    if search_query:
        notes = Note.objects.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        ).order_by('-updated_at')
    elif tag_query:
        notes = Note.objects.filter(tags__name__in=[tag_query]).order_by('-updated_at')
    else:
        notes = Note.objects.all().order_by('-updated_at')
    
    return render(request, 'notepage/note_list.html', {'notes': notes, 'tags': tags})

def create_note(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        print("Form submitted!")
        if form.is_valid():
            note = form.save(commit=False)
            note.save()
            form.save_m2m()
            print(f"Note saved with ID: {note.pk}")
            return redirect('note_detail', pk=note.pk)
        else:
            print("Form errors:", form.errors)
    else:
        form = NoteForm()
    
    return render(request, 'notepage/note_form.html', {'form': form, 'action': 'Create'})


def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)
    return render(request, 'notepage/note_detail.html', {'note': note})

def edit_note(request, pk):
    note = get_object_or_404(Note, pk=pk)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)

        if form.is_valid():
            note = form.save(commit=False)
            note.save()
            return redirect('note_detail', pk=note.pk)

    else:
        form = NoteForm(instance=note)


    return render(request, 'notepage/note_form.html', {'form': form, 'note': note, 'action': 'Edit'})

def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    
    if request.method == 'POST':
        note.delete()
        return redirect('note_list')
    
    return render(request, 'notepage/note_confirm_delete.html', {'note': note})

def autosave_note(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        note_id = data.get('note_id')
        title = data.get('title')
        content = data.get('content')
        
        if note_id:
            note = get_object_or_404(Note, pk=note_id)
            note.title = title
            note.content = content
            note.save()
            return JsonResponse({'success': True, 'saved_at': note.updated_at.strftime("%H:%M:%S")})
        else:
            new_note = Note(title=title, content=content)
            new_note.save()
            return JsonResponse({'success': True, 'note_id': new_note.id, 'saved_at': new_note.updated_at.strftime("%H:%M:%S")})
    
    return JsonResponse({'success': False})

def delete_tags(request):
    if request.method == 'POST':
        notes = Note.objects.all()

        for note in notes:
            note.tags.clear()

        Tag.objects.all().delete()

        return redirect('note_list')
