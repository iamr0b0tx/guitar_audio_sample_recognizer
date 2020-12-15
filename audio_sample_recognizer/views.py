import os

from cloudinary_storage.storage import RawMediaCloudinaryStorage
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, Http404
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from .models import AudioSampleLabel, AudioSample, AUDIO_SAMPLES_DIR, AudioSampleRecognizerModel, get_latest_model
from .recognizer import recognize, get_model, extract_features, initialize_model
cloudinary_raw_storage_object = RawMediaCloudinaryStorage()


# Create your views here.
def index(request, user_id=None):
    audio_sample_labels = AudioSampleLabel.objects.all().values_list("label", flat=True)
    return render(request, 'index.html', {"audio_sample_labels": audio_sample_labels})


# Create your views here.
def record(request, user_id, audio_sample_label):
    audio_sample_labels = AudioSampleLabel.objects.all().values_list("label", flat=True)
    if audio_sample_label not in audio_sample_labels:
        raise Http404

    return render(request, 'record.html', {"audio_sample_label": audio_sample_label})


# Create your views here.
def predict(request, user_id, audio_sample_label):
    # the ml model
    model = get_latest_model()

    audio_sample_labels = AudioSampleLabel.objects.all().values_list("label", flat=True)
    if audio_sample_label not in audio_sample_labels:
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

        # get the audio sample path
        path = default_storage.save(filepath, ContentFile(data.read()))
        tmp_file = os.path.join(settings.MEDIA_ROOT, path)

        # check if it is equal
        predicted = recognize(model, tmp_file)
        prediction = predicted == audio_sample_label
        print(predicted, prediction)

        return JsonResponse({
            "result": prediction
            },
            content_type="application/json"
        )

    return JsonResponse({
            "error": "Something went wrong!"
        },
        content_type="application/json",
        status_code=400
    )
