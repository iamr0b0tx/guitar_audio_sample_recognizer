import os
import subprocess

import joblib
from django.core.files.base import ContentFile, File
from django.db import models

# const
from django.db.models.signals import pre_save
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
    status_message = models.TextField(blank=True, null=True)


def get_latest_model():
    # get the latest model
    latest_model = AudioSampleRecognizerModel.objects.exclude(
        model__isnull=True
    ).order_by("-created_at")[:1]

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


@receiver(pre_save, sender=AudioSampleRecognizerModel)
def update_model(sender, instance, **kwargs):
    # run only when model not set
    if bool(instance.model):
        return

    latest_model = get_latest_model()
    x, y = [], []

    for audio_sample_instance in AudioSample.objects.all():
        # get audio file info
        audio_sample_label = audio_sample_instance.audio_sample_label.label
        audio_file_path = audio_sample_instance.audio.name
        print(audio_file_path, audio_sample_label)

        # retrieve audio file from the cloud
        audio_file_object = cloudinary_raw_storage_object.open(audio_file_path)
        audio_local_file_path = os.path.join(
            "media",
            default_storage.save(audio_file_path, ContentFile(audio_file_object.read()))
        )

        x.append(extract_features(audio_local_file_path))
        y.append(audio_sample_label)

    try:
        # fit it to model
        latest_model.fit(x, y)

    except ValueError as e:
        print(e)
        instance.status_message = f"Model update failed: {e}"
        return

    # save model locally
    model_local_file_path = "knn_model.joblib"
    joblib.dump(latest_model, model_local_file_path)

    instance.status_message = "Model Update completed successfully!"

    # move model to the cloud
    with open(model_local_file_path, 'rb') as f:
        instance.model.save("knn_model.joblib", File(f))

