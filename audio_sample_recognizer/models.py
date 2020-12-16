import os
import subprocess

import cloudinary
import joblib
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.db import models

# const
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.files.storage import default_storage
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from audio_sample_recognizer.recognizer import initialize_model, extract_features

cloudinary_raw_storage_object = RawMediaCloudinaryStorage()

AUDIO_SAMPLES_DIR = "audio_samples"
MODEL_DIR = "models"


def audio_sample_label_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/audio_samples/<filename>
    return f'{AUDIO_SAMPLES_DIR}/{instance.audio_sample_label.label}/{filename}'


def audio_sample_model_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/models/<filename>
    return f'{MODEL_DIR}/{filename}'


class AudioSampleLabel(models.Model):
    label = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label


class AudioSample(models.Model):
    audio_sample_label = models.ForeignKey(AudioSampleLabel, on_delete=models.CASCADE)
    audio = models.FileField(upload_to=audio_sample_label_directory_path, storage=RawMediaCloudinaryStorage())
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.audio_sample_label.label


class AudioSampleRecognizerModel(models.Model):
    tag = models.CharField(max_length=128)
    model = models.FileField(
        blank=True,
        null=True,
        upload_to=audio_sample_model_directory_path,
        storage=RawMediaCloudinaryStorage()
    )
    created_at = models.DateTimeField(auto_now_add=True)


def get_latest_model():
    # get the latest model
    latest_model = AudioSampleRecognizerModel.objects.all().order_by("-created_at")[:1]

    # pick latest model if it exist else create a new one
    if latest_model.count():
        latest_model = latest_model[0]
        model_file_path = latest_model.model.name

        print("using old_model", model_file_path)

        # check if model already local
        model_local_file_path = os.path.join("media", model_file_path)
        if not os.path.exists(model_local_file_path):
            # get model file from cloud
            model_file_object = cloudinary_raw_storage_object.open(model_file_path)
            model_local_file_path = os.path.join(
                "media",
                default_storage.save(model_file_path, ContentFile(model_file_object.read()))
            )

        # get model instance locally
        latest_model = joblib.load(model_local_file_path)

    else:
        print("creating new model")
        latest_model = initialize_model()

    return latest_model


@receiver(post_save, sender=AudioSampleRecognizerModel)
def update_model(sender, instance, **kwargs):
    process = subprocess.Popen(
        ['python', 'update_audio_sample_recognizer_model.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

