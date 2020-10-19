import os
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, Http404
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from .tuner import detect_note

# load the model, and pass in the custom metric function
notes = ["A", "B", "D", "EL", "EH", "G"]


# Create your views here.
def index(request, user_id=None):
    return render(request, 'index.html', {"notes": notes})


# Create your views here.
def record(request, user_id, note):
    if note not in notes:
        raise Http404

    return render(request, 'record.html', {"note": note.upper()})


# Create your views here.
def predict(request, user_id, note):
    if note not in notes:
        raise Http404

    if request.method == "POST":
        data = request.FILES.get('audio_data') # or self.files['image'] in your form
        if data is None:
            return JsonResponse({
                    "error": "audio_data can not be empty!"
                },
                content_type="application/json", 
                status_code=400
            )

        filepath = f'{str(user_id)}/sample.wav'
        if default_storage.exists(filepath):
            default_storage.delete(filepath)

        path = default_storage.save(filepath, ContentFile(data.read()))
        tmp_file = os.path.join(settings.MEDIA_ROOT, path)
        
        predicted = detect_note(tmp_file) == note
        
        return JsonResponse({
            "result": predicted
            },
            content_type="application/json"
        )

    return JsonResponse({
            "error": "Something went wrong!"
        },
        content_type="application/json", 
        status_code=400
    )
