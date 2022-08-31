# from django.db import IntegrityError
# from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg
from django.contrib import messages
from django.shortcuts import redirect

from .models import Movie, Role, Actor, Vod, Genre, Country, MyRate, WTS
from .service_parse import get_movies_rated, get_movies_wts, parse_vod
import json
# import numpy as np
import pandas as pd
# import logging
# logging.basicConfig(level=logging.DEBUG)


def movies_db_save(source: str, user: str):
    """
    parsing movie date from filmweb and save into db

    :param source: part of actor_name of get_ function e.g. 'movies_rated', 'movies_wts'
    :param user: actor_name of user from filmweb
    :return: list of saved and not saved movies
    """

    movies_not_saved = []
    movies_saved = []
    new_genre = []

    if source == 'movies_rated':
        movies = get_movies_rated(user)
    elif source == 'movies_wts':
        movies = get_movies_wts(user)
    else:
        return movies_saved, movies_not_saved, new_genre

    for movie_id, movie in movies.items():
        movie_id = int(movie_id)
        title = movie['title']
        wts_rate = movie['wts_rate']

        if Movie.objects.filter(pk=movie_id).exists():
            movies_not_saved.append([movie_id, title])
            if WTS.objects.filter(movie_id=movie_id).exists():
                wts_obj = WTS.objects.get(movie_id=movie_id)
                wts_obj.rate = wts_rate
                wts_obj.save()
            continue
        else:
            movie_obj = Movie(
                movie_id=movie_id,
                link=movie['link'],
                title=title,
                title_original=movie['title_original'],
                year=movie['year'],
                rate=movie['rate'],
                rate_count=movie['rate_count'],
                critic_rate=movie['critic_rate'],
                award_oscar=movie['award_oscar'],
                award=movie['award'],
                nomination=movie['nomination'],
                box_office=movie['box_office'],
                box_office_usa=movie['box_office_usa'],
                box_office_outside_usa=movie['box_office_outside_usa'],
                budget=movie['budget'],
                director=movie['director']
            )

            movie_obj.save()

            for actor in movie['actors']:
                actor_id = actor['actor_id']

                actor_obj, _ = Actor.objects.get_or_create(
                    actor_id=actor_id,
                    defaults={
                        'actor_name': actor['actor_name'],
                        'link': actor['actor_link'],
                        'gender': actor['gender']
                    }
                )

                role_obj = Role(
                    movie=movie_obj,
                    actor=actor_obj,
                    role_id=actor['role_id'],
                    rate=actor['role_rate'],
                    rate_count=actor['role_rate_count'],
                    top=actor['role_top']
                )

                role_obj.save()
                actor_obj.roles.add(role_obj)

            with open(r"movies\service_countries.json", 'r', encoding='utf-8') as f:
                countries = json.load(f)

            for country in movie['country']:
                code = countries.get(country, 'NN')
                country_obj = Country(
                    movie=movie_obj,
                    country=country,
                    code=code
                )
                country_obj.save()

            for genre in movie['genre']:
                genre_obj, created = Genre.objects.get_or_create(genre=genre, defaults={'short': ''})
                if created:
                    new_genre.append([movie_obj, genre_obj])
                genre_obj.movie.add(movie_obj)

            avg_genre = round(movie_obj.genres.all().aggregate(Avg('like')).get('like__avg'), 3)
            if avg_genre is None or (avg_genre > 3.6 and 'Thriller' not in movie['genre']):
                wts_who = 'kk'
            else:
                wts_who = 'kz'

            if wts_rate is not None:
                WTS.objects.create(movie=movie_obj, who=wts_who, rate=wts_rate)
            else:
                user_rate = movie['user_rate']
                if user_rate is not None:
                    rate_var = round(user_rate - movie['rate'], 3)
                else:
                    user_rate = rate_var = 0
                MyRate.objects.create(movie=movie_obj, rate=user_rate, rate_var=rate_var)

            for vod in movie['vod']:
                vod_obj = Vod(
                    movie=movie_obj,
                    vod=vod
                )
                vod_obj.save()
            movies_saved.append([movie_id, title])
    return movies_saved, movies_not_saved, new_genre


def vod_db_update():
    log_vod = {}
    wts_movie = Movie.wts.all()
    for movie in wts_movie:
        add_vod = []
        del_vod = []
        url = movie.link
        vod = parse_vod(url)
        act_vods = movie.vods.all()
        for movie_vod in act_vods:
            if movie_vod.vod not in vod:
                movie_vod.delete()
                del_vod.append(movie_vod.vod)
            else:
                vod.remove(movie_vod.vod)
        for vod_import in vod:
            vod_obj = Vod(
                movie=movie,
                vod=vod_import
            )
            vod_obj.save()
            add_vod.append(vod_obj.vod)
        if add_vod or del_vod:
            log_vod.update({f"{movie.movie_id}: {movie.title}": {'add': add_vod, 'del': del_vod}})
    return log_vod


def my_rate_db_update(movie, my_rate):
    rate_var = round(my_rate - movie.rate, 3)
    MyRate.objects.create(movie=movie, rate=my_rate, rate_var=rate_var)
    WTS.objects.get(movie=movie).delete()


def wts_who_db_change(movie_id, who):
    movie = WTS.objects.get(movie_id=movie_id)
    if who == 'kz':
        wts_who = 'kk'
    elif who == 'kk':
        wts_who = 'kz'
    else:
        wts_who = movie.who
    movie.who = wts_who
    movie.save()


def set_recommendation():
    rated, wts, genres, country, actor, role = create_pd_df()

    rated.index.name = 'movie_id'
    rated.columns = ['movie_id', 'title', 'rate', 'my_rate', 'rate_var', 'rate_count', 'critic_rate', 'year',
                     'award_oscar',
                     'award', 'nomination', 'bo', 'bo_usa', 'bo_no_usa', 'budget', 'director']
    wts.index.name = 'movie_id'
    wts.columns = ['movie_id', 'title', 'rate', 'wts_rate', 'rate_count', 'critic_rate', 'year', 'award_oscar',
                   'award', 'nomination', 'bo', 'bo_usa', 'bo_no_usa', 'budget', 'director']
    role.index.name = 'role_id'
    actor.index.name = 'actor_id'
    genres.columns = ['movie_id', 'genre', 'short', 'like']
    rated.insert(5, 'genre_avg', genres.groupby('movie_id').mean().loc[rated.index])

    rate_var_mean = rated.rate_var.mean()
    rate_role_mean = role.rate.mean()
    confidence_lvl_country = 75  # less cause results tending more to mean
    confidence_lvl_genres = 75
    confidence_lvl_role = 99
    confidence_lvl_director = 70

    country_mean = pd.DataFrame({
        'country': country.groupby('movie_id')['code'].apply(tuple)[rated.movie_id],
        'rate_var': rated.rate_var
    }).groupby('country').agg(
        rate_var_mean=('rate_var', 'mean'),
        rate_var_count=('rate_var', 'count')).sort_values('rate_var_count', ascending=False)
    # country_mean.count value where exceeds 80%
    country_mean_count_confidence = country_mean.rate_var_count[
        (country_mean.rate_var_count.cumsum() / country_mean.rate_var_count.sum() * 100) > confidence_lvl_country].max()
    country_mean_confidence = country_mean.rate_var_count / (
                country_mean.rate_var_count + country_mean_count_confidence)
    country_mean['rate_var_adj'] = country_mean.rate_var_mean * country_mean_confidence + rate_var_mean * (
                1 - country_mean_confidence)

    genres_mean = pd.DataFrame({
        'genres': genres.groupby('movie_id')['short'].apply(tuple)[rated.movie_id],
        'rate_var': rated.rate_var
    }).groupby('genres').agg(
        rate_var_mean=('rate_var', 'mean'),
        rate_var_count=('rate_var', 'count')).sort_values('rate_var_count', ascending=False)
    genres_mean_count_confidence = genres_mean.rate_var_count[
        (genres_mean.rate_var_count.cumsum() / genres_mean.rate_var_count.sum() * 100) > confidence_lvl_genres].max()
    genres_mean_confidence = genres_mean.rate_var_count / (
            genres_mean.rate_var_count + genres_mean_count_confidence)
    genres_mean['rate_var_adj'] = genres_mean.rate_var_mean * genres_mean_confidence + rate_var_mean * (
            1 - genres_mean_confidence)

    director_mean = rated[['director', 'rate_var']].groupby('director').agg(
        rate_var_mean=('rate_var', 'mean'),
        rate_var_count=('rate_var', 'count')).sort_values('rate_var_count', ascending=False)
    director_mean_count_confidence = director_mean.rate_var_count[
        (director_mean.rate_var_count.cumsum() / director_mean.rate_var_count.sum() * 100) > confidence_lvl_director
        ].max()
    director_mean_confidence = director_mean.rate_var_count / (
            director_mean.rate_var_count + director_mean_count_confidence)
    director_mean['rate_var_adj'] = director_mean.rate_var_mean * director_mean_confidence + rate_var_mean * (
            1 - director_mean_confidence)

    role.sort_values('rate_count', ascending=False, inplace=True)
    role_mean_count_confidence = role.rate_count[
        (role.rate_count.cumsum() / role.rate_count.sum() * 100) > confidence_lvl_role].max()
    role_mean_confidence = role.rate_count / (role.rate_count + role_mean_count_confidence)
    role['rate_adj'] = role.rate * role_mean_confidence + rate_role_mean * (1 - role_mean_confidence)

    actor = actor.merge(role.groupby('actor_id').agg(['mean', 'count']).rate_adj, how='left', left_index=True,
                        right_index=True)
    actor.dropna(inplace=True)

    rated_recommend = rated[['title', 'rate', 'my_rate', 'rate_var', 'director']].merge(
        director_mean[['rate_var_adj']].rename(columns={'rate_var_adj': 'director_var'}), left_on='director',
        right_index=True).merge(
        genres.groupby('movie_id')['short'].apply(tuple).to_frame().rename(columns={'short': 'genre'}), left_index=True,
        right_index=True).merge(
        genres_mean[['rate_var_adj']].rename(columns={'rate_var_adj': 'genres_var'}), left_on='genre',
        right_index=True).merge(
        country.groupby('movie_id')['code'].apply(tuple).to_frame().rename(columns={'code': 'country'}),
        left_index=True, right_index=True).merge(
        country_mean[['rate_var_adj']].rename(columns={'rate_var_adj': 'country_var'}), left_on='country',
        right_index=True)

    country_weight = rated_recommend.corr().rate_var['country_var'] * 2
    genres_weight = rated_recommend.corr().rate_var['genres_var'] * 2
    director_weight = rated_recommend.corr().rate_var['director_var'] * 2

    wts_recommend = wts[['title', 'rate', 'director']].merge(
        director_mean[['rate_var_adj']].rename(columns={'rate_var_adj': 'director_var'}), left_on='director',
        right_index=True, how='left').merge(
        genres.groupby('movie_id')['short'].apply(tuple).to_frame().rename(columns={'short': 'genre'}), left_index=True,
        right_index=True).merge(
        genres_mean[['rate_var_adj']].rename(columns={'rate_var_adj': 'genres_var'}), left_on='genre', right_index=True,
        how='left').merge(
        country.groupby('movie_id')['code'].apply(tuple).to_frame().rename(columns={'code': 'country'}),
        left_index=True, right_index=True).merge(
        country_mean[['rate_var_adj']].rename(columns={'rate_var_adj': 'country_var'}), left_on='country',
        right_index=True, how='left').fillna(
        {'director_var': rate_var_mean, 'genres_var': rate_var_mean, 'country_var': rate_var_mean})

    wts_recommend.insert(
        2,
        'rate_var_recommend',
        wts_recommend.director_var * director_weight + wts_recommend.genres_var * genres_weight +
        wts_recommend.country_var * country_weight - 0.4)
    wts_recommend.insert(2, 'rate_recommended', wts_recommend.rate + wts_recommend.rate_var_recommend)

    cnt = 0
    movies = WTS.objects.all()
    for movie in movies:
        movie.rate_recommended = round(wts_recommend.rate_recommended.loc[movie.movie_id], 3)
        movie.save()
        cnt += 1

    actors = Actor.objects.filter(actor_id__in=list(actor.index))
    for actor_db in actors:
        actor_db.rate = round(actor['mean'].loc[actor_db.actor_id], 3)
        actor_db.role_count = int(actor['count'].loc[actor_db.actor_id])
        actor_db.save()

    log_info = f"Recommendation rate has been updated in {cnt} WTS movies"
    return log_info


def temp_db():
    first = 0
    second = 0

    log = {
        'What': '',
        'a': first,
        'b': second,
    }
    return log


def create_pd_df(to_json=False):
    rated = pd.DataFrame(list(Movie.objects.filter(my_rates__isnull=False).values(
        'movie_id', 'title', 'rate', 'my_rates__rate', 'my_rates__rate_var', 'rate_count', 'critic_rate', 'year',
        'award_oscar', 'award', 'nomination', 'box_office', 'box_office_usa', 'box_office_outside_usa',
        'budget', 'director',
    )), index=Movie.objects.filter(my_rates__isnull=False).values_list(
        'movie_id', flat=True))

    wts = pd.DataFrame(list(Movie.objects.filter(wtss__isnull=False).values(
        'movie_id', 'title', 'rate', 'wtss__rate', 'rate_count', 'critic_rate', 'year', 'award_oscar', 'award',
        'nomination', 'box_office', 'box_office_usa', 'box_office_outside_usa', 'budget', 'director'
    )), index=Movie.objects.filter(wtss__isnull=False).values_list(
        'movie_id', flat=True))

    genres = pd.DataFrame(list(Movie.objects.all().values(
        'movie_id', 'genres__genre', 'genres__short', 'genres__like'))).sort_values(
        ['movie_id', 'genres__short'])

    country = pd.DataFrame(list(Country.objects.all().values(
        'movie_id', 'country', 'code'
    )), index=Country.objects.all().values_list('pk', flat=True))

    actor = pd.DataFrame(list(Actor.objects.all().values(
        'actor_name'
    )), index=Actor.objects.all().values_list('actor_id', flat=True))

    role = pd.DataFrame(list(Role.objects.all().values(
        'movie_id', 'actor_id', 'rate', 'rate_count', 'top'
    )), index=Role.objects.all().values_list('role_id', flat=True)).sort_values(
        ['movie_id', 'rate'], ascending=[True, False])

    if to_json:
        genre = pd.DataFrame(list(Genre.objects.all().values()), index=Genre.objects.all().values_list(
            'genre', flat=True))

        rated.to_json(r"movies\resources\df\rated.json")
        wts.to_json(r"movies\resources\df\wts.json")
        genre.to_json(r"movies\resources\df\genre.json")
        genres.to_json(r"movies\resources\df\genres.json")
        actor.to_json(r"movies\resources\df\actor.json")
        role.to_json(r"movies\resources\df\role.json")
        country.to_json(r"movies\resources\df\country.json")
    else:
        return rated, wts, genres, country, actor, role


def check_authentication_decorator(func):
    def wrapper(request, upload_url='', movie_id=None, who='', vod_service=''):
        if not check_authentication(request):
            if upload_url:
                return redirect('movies:import_update')
            elif who and vod_service:
                return redirect('movies:vod_list', who=who, vod_service=vod_service)
            else:
                return redirect('movies:movies_main')
        else:
            if upload_url:
                return func(request, upload_url)
            elif who and vod_service:
                return func(request, movie_id, who, vod_service)
            else:
                return func(request)
    return wrapper


def check_authentication(request):
    if request.user.is_authenticated:
        return True
    else:
        messages.add_message(request, messages.ERROR, "Log in first to alter data")
        return False
