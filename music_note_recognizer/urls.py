from django.urls import path
from music_note_recognizer import views

urlpatterns = [
    path('', views.index),
]
