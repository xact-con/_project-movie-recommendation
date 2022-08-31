from django.urls import path
from .views import movies_main, vod, upload_movies, credentials, update_vod, \
    add_genre_like, vod_list, movie_details, change_wts_who, import_update, temp_function, \
    update_recommendation

app_name = 'movies'
urlpatterns = [
    path('', movies_main, name='movies_main'),
    path('vod/', vod, name='vod'),
    path('vod/<who>/<vod_service>/', vod_list, name='vod_list'),
    path('import-update/', import_update, name='import_update'),
    path('genres/', add_genre_like, name='genres'),
    path('credentials/', credentials, name='credentials'),
    path('update_vod:<upload_url>/', update_vod, name='update_vod'),
    path('upload_wts:<upload_url>/', upload_movies, name='upload_wts'),
    path('upload_rated:<upload_url>/', upload_movies, name='upload_rated'),
    path('update_recommendation:<upload_url>/', update_recommendation, name='update_recommendation'),
    path('temp_function:<upload_url>/', temp_function, name='temp_function'),
    path('change_wts_who:<movie_id>/<who>/<vod_service>/', change_wts_who, name='change_wts_who'),
    path('<movie_id>/', movie_details, name='movie_details'),
]
