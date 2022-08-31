from django.urls import path
from .views import events_main

app_name = 'events'
urlpatterns = [
    path('', events_main, name='events_main'),
]
