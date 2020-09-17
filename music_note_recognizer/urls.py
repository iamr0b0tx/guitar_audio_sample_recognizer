from django.urls import path
from music_note_recognizer import views

urlpatterns = [
    path('', views.index),
    path('record/<int:user_id>/<str:note>', views.record),
    path('predict', views.predict),
]
