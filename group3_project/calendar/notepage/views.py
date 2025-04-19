from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import Note
from .forms import NoteForm
from .forms import FileImportForm
from taggit.models import Tag
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import UploadedFile
import os

@csrf_exempt
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

@csrf_exempt
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

@csrf_exempt
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)
    return render(request, 'notepage/note_detail.html', {'note': note})

@csrf_exempt
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

@csrf_exempt
def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    
    if request.method == 'POST':
        note.delete()
        return redirect('note_list')
    
    return render(request, 'notepage/note_confirm_delete.html', {'note': note})

@csrf_exempt
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

@csrf_exempt
def delete_tags(request):
    if request.method == 'POST':
        notes = Note.objects.all()

        for note in notes:
            note.tags.clear()

        Tag.objects.all().delete()

        return redirect('note_list')

@csrf_exempt
def import_file(request):
    if request.method == 'POST':
        form = FileImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            filename = os.path.basename(uploaded_file.name)
            title = os.path.splitext(filename)[0]
            
            content = ""
            if isinstance(uploaded_file, UploadedFile):
                try:                            # Parseable text file
                    content = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:      # Unparseable file
                    content = f"This note was created from file: {filename}\nThe file content could not be displayed as text."
            
            note = Note(title=title, content=content)
            note.save()
            
            tags = form.cleaned_data.get('tags')
            if tags:
                note.tags.add(*tags.split(','))
            
            return redirect('note_detail', pk=note.pk)
    else:
        form = FileImportForm()
    
    return render(request, 'notepage/import_file.html', {'form': form})

@csrf_exempt
def get_note_content(request, pk):
    try:
        note = Note.objects.get(pk=pk)
        return JsonResponse({'content': note.content})
    except Note.DoesNotExist:
        return JsonResponse({'error': 'Note not found'}, status=404)

@csrf_exempt
def summarize_note(request):
    load_dotenv()
    
    if request.method == 'POST':
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            data = json.loads(request.body)
            content = data.get('content', '')

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Summarize this note in 1-2 sentences."},
                    {"role": "user", "content": content}
                ]
            )

            summary = response.choices[0].message.content
            return JsonResponse({'summary': summary})

        except Exception as e:
            return JsonResponse({'summary': 'Error: ' + str(e)}, status=500)

@csrf_exempt
def multi_note_quiz_page(request):
    notes = Note.objects.all()
    return render(request, 'notepage/quiz_page.html', {'notes': notes})

@csrf_exempt
def generate_multi_note_quiz(request):
    
    load_dotenv()
    if request.method == 'POST':
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            data = json.loads(request.body)
            note_ids = data.get('note_ids', [])
            selected_notes = Note.objects.filter(pk__in=note_ids)

            combined_content = "\n\n".join(note.content for note in selected_notes)

            prompt = (
                "Based on the following notes, generate as many multiple-choice quiz questions as you can. "
                "Each question should include 1 correct answer and 3 incorrect answers. "
                "Respond in the following JSON format:\n\n"
                "{\n"
                "  \"questions\": [\n"
                "    {\n"
                "      \"question\": \"...\",\n"
                "      \"choices\": [\"...\", \"...\", \"...\", \"...\"],\n"
                "      \"answer\": \"...\"\n"
                "    },\n"
                "    ...\n"
                "  ]\n"
                "}\n\n"
                f"Notes:\n{combined_content}"
            )

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful quiz generator."},
                    {"role": "user", "content": prompt}
                ]
            )

            quiz = response.choices[0].message.content
            return JsonResponse({'quiz': quiz})

        except Exception as e:
            return JsonResponse({'quiz': f'Error: {str(e)}'}, status=500)