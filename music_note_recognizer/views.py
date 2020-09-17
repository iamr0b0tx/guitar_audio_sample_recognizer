import os
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

import tensorflow as tf
from .train import get_model

# load the model, and pass in the custom metric function
models = {
    "A": get_model().load_weights('staticfiles/models/A_weights.h5'),
    "B": get_model().load_weights('staticfiles/models/B_weights.h5'),
}

# Create your views here.
def index(request, user_id=None):
    return render(request, 'index.html')

# Create your views here.
def record(request, user_id=None, note=None):
    return render(request, 'record.html')

# Create your views here.
@csrf_exempt
def predict(request):
    if request.method == "POST":
        data = request.FILES['audio_data'] # or self.files['image'] in your form

        path = default_storage.save('tmp/sample.wav', ContentFile(data.read()))
        tmp_file = os.path.join(settings.MEDIA_ROOT, path)
        
        return JsonResponse({
            "message": "Nice"
            },
            content_type="application/json"
        )

    return JsonResponse(
        {
            "error": "Something went wrong!"
        },
        content_type="application/json", 
        status_code=400
    )
