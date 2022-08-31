import random
import string

# from django.core.paginator import Paginator
from django.shortcuts import render, redirect
# from django.contrib.auth import login, authenticate, logout
# from django.contrib.auth.forms import AuthenticationForm
# from django.contrib.auth.models import User
from django.contrib import messages
from django.forms import modelformset_factory

from .service_db import movies_db_save, vod_db_update, wts_who_db_change, temp_db, my_rate_db_update, \
    set_recommendation, check_authentication_decorator, check_authentication
from .service_select import select_vod, select_movies
from .forms import CredentialsForm, GenreForm, MyRateForm, MoviesSearch
from .models import FilmwebCredentials, Movie, Genre

# import logging
# logging.basicConfig(level=logging.DEBUG)


def main(request):
    return render(request, "main.html", {'main': 'main'})


def movies_main(request):
    if request.method == "GET":
        form = MoviesSearch(request.GET)
        if form.is_valid():
            movies_listing, kind = select_movies(form.cleaned_data)
            context = {
                'movies': True,
                'movies_lists': True,
                'kind': kind,
                'movies_listing': movies_listing,
            }
            return render(request, "movies/listing_kind.html", context)

    form = MoviesSearch()
    context = {
        'movies': True,
        'movies_list': True,
        'form': form,
    }
    return render(request, "movies/main.html", context)


def vod(request):
    vod_services = ['Netflix', 'HBO', 'Amazon', 'Disney', 'Canal+', 'Apple', 'Other VOD', 'Not on VOD']
    who_list = ['kk', 'kz', 'all']
    context = {
        'movies': True,
        'movies_vod': True,
        'vod_services': vod_services,
        'who_list': who_list,
    }

    return render(request, "movies/vod.html", context)


def vod_list(request, who, vod_service):
    movies_listing, vod_service_name = select_vod(who, vod_service)
    context = {
        'movies': True,
        'movies_vod': True,
        'who': who,
        'vod_service_name': vod_service_name,
        'movies_listing': movies_listing,
    }
    return render(request, "movies/listing_vod.html", context)


def movie_details(request, movie_id):
    movie = Movie.objects.get(movie_id=movie_id)
    if request.method == "POST":
        form = MyRateForm(data=request.POST)
        if form.is_valid() and check_authentication(request):
            my_rate = form.cleaned_data.get('my_rate')
            my_rate_db_update(movie, my_rate)
            messages.success(request, "My rate has been saved")
        return redirect(request.path)
    else:
        form = MyRateForm
    context = {
        'movies': True,
        'movie': movie,
        'form': form,
    }
    return render(request, "movies/movie_details.html", context)


def import_update(request):
    upload_url = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    context = {
        'movies': True,
        'import_update': True,
        'upload_url': upload_url,
    }
    return render(request, "movies/import_update.html", context)


def add_genre_like(request):
    GenreFormSet = modelformset_factory(Genre, form=GenreForm, extra=0)
    helper = GenreForm().helper
    if request.method == 'POST':
        form = GenreFormSet(data=request.POST)
        if check_authentication(request):
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Data has been saved')
        return redirect("movies:movies_main")
    form = GenreFormSet()

    context = {
        'movies': True,
        'genre': True,
        'form': form,
        'helper': helper,
    }
    return render(request, "movies/genres.html", context)


def credentials(request):
    if check_authentication(request):
        user_obj = FilmwebCredentials.objects.get(user=request.user)
        if request.method == 'POST':
            form = CredentialsForm(data=request.POST)
            if form.is_valid():
                FilmwebCredentials.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'user_name': form.cleaned_data.get('user_name'),
                        'cookie': form.cleaned_data.get('cookie'),
                        'user_agent': form.cleaned_data.get('user_agent')
                    }
                )
                messages.add_message(request, messages.SUCCESS, 'Data has been saved')
            return redirect("movies:movies_main")
        else:
            form = CredentialsForm(data={
                'user_name': user_obj.user_name,
                'cookie': user_obj.cookie,
                'user_agent': user_obj.user_agent
            })
    else:
        form = CredentialsForm
    context = {
        'movies': True,
        'credentials': True,
        'form': form,
    }
    return render(request, "movies/credentials.html", context)


@check_authentication_decorator
def update_vod(request, upload_url):
    log_vod = vod_db_update()
    context = {
        'movies': True,
        'movies_upload': True,
        'log_vod': log_vod,
    }
    return render(request, "movies/import_update_result.html", context)


@check_authentication_decorator
def upload_movies(request, upload_url):
    user = FilmwebCredentials.objects.get(user=request.user).user_name

    log_info = ''
    kind = ''
    if 'upload_rated' in request.path:
        movies_saved, movies_not_saved, new_genre = movies_db_save('movies_rated', user)
    elif 'upload_wts' in request.path:
        movies_saved, movies_not_saved, new_genre = movies_db_save('movies_wts', user)
        log_info = set_recommendation()
        kind = 'wts'
    else:
        movies_saved, movies_not_saved, new_genre = [], [], []
    context = {
        'movies': True,
        'movies_upload': True,
        'movies_saved': movies_saved,
        'movies_not_saved': movies_not_saved,
        'new_genre': new_genre,
        'log_info': log_info,
        'kind': kind,
    }
    return render(request, "movies/import_update_result.html", context)


@check_authentication_decorator
def update_recommendation(request, upload_url):
    log_info = set_recommendation()
    context = {
        'movies': True,
        'movies_upload': True,
        'log_info': log_info,
    }
    return render(request, "movies/import_update_result.html", context)


@check_authentication_decorator
def change_wts_who(request, movie_id, who, vod_service):
    wts_who_db_change(movie_id, who)
    return redirect('movies:vod_list', who=who, vod_service=vod_service)


@check_authentication_decorator
def temp_function(request, upload_url):
    log = temp_db()
    context = {
        'log': log,
    }
    return render(request, "movies/import_update_result.html", context)
