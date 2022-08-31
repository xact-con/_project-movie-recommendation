from django.db.models import Q

from movies.models import Vod, Movie


def select_vod(who, vod_service):
    if vod_service == 'netflix':
        movies_vod = [i.movie_id for i in Vod.netflix.all()]
    elif vod_service == 'amazon':
        movies_vod = [i.movie_id for i in Vod.amazon.all()]
    elif vod_service == 'hbo':
        movies_vod = [i.movie_id for i in Vod.hbo.all()]
    elif vod_service == 'disney':
        movies_vod = [i.movie_id for i in Vod.disney.all()]
    elif vod_service == 'canal':
        movies_vod = [i.movie_id for i in Vod.canal.all()]
    elif vod_service == 'apple':
        movies_vod = [i.movie_id for i in Vod.apple.all()]
    elif vod_service == 'other-vod':
        movies_vod = [i.movie_id for i in Vod.other_vod.all()]
    elif vod_service == 'not-on-vod':
        movies_vod = [i.movie_id for i in Movie.objects.all()
                      if i.movie_id not in Vod.objects.all().values_list('movie_id', flat=True)]
    else:
        movies_vod = []

    if who == 'kk':
        movies_in_vod = Movie.wts_kk.filter(movie_id__in=movies_vod)
    elif who == 'kz':
        movies_in_vod = Movie.wts_kz.filter(movie_id__in=movies_vod)
    else:
        movies_in_vod = Movie.wts.filter(movie_id__in=movies_vod)
    movies_in_vod = movies_in_vod.order_by('-wtss__rate', '-wtss__rate_recommended')

    vod_service_name = vod_service.replace('-', ' ').capitalize()
    return movies_in_vod, vod_service_name


def select_movies(cleaned_data):
    movie_objs = cleaned_data['movies_set']
    if movie_objs == 'wts':
        wts_rate = 1
        wts_bool = False
    elif movie_objs == 'rated':
        wts_rate = 999999999
        wts_bool = True
    else:
        wts_rate = 1
        wts_bool = True

    rate_count = cleaned_data['votes_from']

    box_office_min = cleaned_data['box_office_min']
    if box_office_min == 0:
        box_office_null = None
    else:
        box_office_null = box_office_min

    oscar_award = cleaned_data['oscar_award']
    if oscar_award == 'all':
        award_oscar = 0
    else:
        award_oscar = 1

    vod_input = cleaned_data['vod_set']
    vod_have = ['netflix', 'amazon', 'disney', 'canal_plus_manual', 'hbo_max', 'apple_tv']
    if vod_input == 'yes':
        vod_set = vod_have
        vod_bool = False
    elif vod_input == 'other':
        vod_list = Vod.objects.all().values_list('vod', flat=True)
        vod_set = [vod for vod in vod_list if vod not in vod_have]
        vod_bool = False
    elif vod_input == 'all':
        vod_set = Vod.objects.all().values_list('vod', flat=True)
        vod_bool = True
    else:
        vod_set = []
        vod_bool = True

    year_from = cleaned_data['year_from']
    year_to = cleaned_data['year_to']

    # vod_query_set = Movie.objects.all().annotate(
    #     vod_fr=FilteredRelation(
    #         'vods', condition=Q(vods__vod__in=vod_set), ), ).filter(vod_fr__vod__in=vod_set)

    query_set = Movie.objects.filter(
        Q(wtss__rate__gte=wts_rate) | Q(wtss__rate__isnull=wts_bool)).filter(
        rate_count__gte=rate_count).filter(
        Q(box_office__gte=box_office_min) | Q(box_office__exact=box_office_null)).filter(
        award_oscar__gte=award_oscar).filter(
        Q(year__gte=year_from) & Q(year__lte=year_to)).filter(
        Q(vods__vod__in=vod_set) | Q(vods__vod__isnull=vod_bool)).distinct().order_by(
        '-wtss__rate', '-wtss__rate_recommended', '-rate')

    kind = cleaned_data['movies_set']
    return query_set, kind
