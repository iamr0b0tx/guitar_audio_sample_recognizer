from django.urls import path
from music_note_recognizer import views

urlpatterns = [
    path('record/<int:user_id>/<str:note>/predict', views.predict),
    path('record/<int:user_id>/<str:note>/', views.record),
    path('', views.index),
]
