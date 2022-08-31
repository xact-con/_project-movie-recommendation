from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class RatedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(my_rates__isnull=False)
        # return super().get_queryset().filter(user_rate__isnull=False)


class WtsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(wtss__isnull=False)
        # return super().get_queryset().filter(wts_rate__isnull=False)


class WtsKkManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(wtss__who='kk')
        # return super().get_queryset().filter(wts_rate__isnull=False).filter(wts_who='kk')


class WtsKzManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(wtss__who='kz')


class Movie(models.Model):
    movie_id = models.PositiveIntegerField(primary_key=True, verbose_name='#')
    link = models.URLField(verbose_name='Link')
    title = models.CharField(max_length=100, verbose_name='Title')
    title_original = models.CharField(max_length=100, verbose_name='Original title')
    year = models.PositiveSmallIntegerField(verbose_name='Year')
    rate = models.FloatField(verbose_name='Movie rate', validators=[MinValueValidator(1), MaxValueValidator(10)])
    rate_count = models.PositiveIntegerField(verbose_name='Movie rate count')
    critic_rate = models.FloatField(
        null=True, blank=True, verbose_name='Critic rate', validators=[MinValueValidator(1), MaxValueValidator(10)])
    award_oscar = models.PositiveSmallIntegerField(verbose_name='Oscars')
    award = models.PositiveSmallIntegerField(verbose_name='Awards')
    nomination = models.PositiveSmallIntegerField(verbose_name='Nominations')
    box_office = models.FloatField(null=True, blank=True, verbose_name='Box office')
    box_office_usa = models.FloatField(null=True, blank=True, verbose_name='Box office (USA)')
    box_office_outside_usa = models.FloatField(null=True, blank=True, verbose_name='Box office (outside USA)')
    budget = models.FloatField(null=True, blank=True, verbose_name='Budget')
    director = models.CharField(max_length=40, verbose_name='Director')

    objects = models.Manager()
    wts = WtsManager()
    wts_kz = WtsKzManager()
    wts_kk = WtsKkManager()
    rated = RatedManager()

    def __str__(self):
        return f"{self.title} - {self.movie_id} ({self.year})"

    @property
    def on_vod(self):
        vod_have = ['netflix', 'amazon', 'disney', 'canal_plus_manual', 'hbo_max', 'apple_tv']
        movie_obj = Movie.objects.get(pk=self.movie_id)
        vods = movie_obj.vods.all().values_list('vod', flat=True)
        if not vods:
            on_vod_mark = 'N'
        elif any(item in vod_have for item in vods):
            on_vod_mark = 'Y'
        else:
            on_vod_mark = 'O'
        return on_vod_mark

    @property
    def cool(self):
        if self.rate_count < 1000:
            cool = 1
        elif self.rate_count < 10000:
            cool = 2
        elif self.rate_count < 35000:
            cool = 3
        elif self.rate_count < 100000:
            cool = 4
        else:
            cool = 5
        return cool

    @property
    def box_office_all(self):
        def rounded(arg):
            return '' if arg is None else round(arg)
        box_office_list = [self.box_office, self.box_office_usa, self.box_office_outside_usa]
        return '/'.join(str(rounded(i)) for i in box_office_list) if any(box_office_list) else ''

    @property
    def awards_all(self):
        awards_list = [self.award_oscar, self.award, self.nomination]
        return '/'.join(str(i or '') for i in awards_list) if any(awards_list) else ''


class MyRate(models.Model):
    movie = models.OneToOneField(Movie, primary_key=True, related_name='my_rates', on_delete=models.CASCADE)
    rate = models.PositiveSmallIntegerField(
        verbose_name='My movie rate', validators=[MinValueValidator(0), MaxValueValidator(10)])
    rate_var = models.FloatField()

    def __str__(self):
        return f"Rated - {str(self.movie)}"


class WTS(models.Model):
    movie = models.OneToOneField(Movie, primary_key=True, related_name='wtss', on_delete=models.CASCADE)
    who = models.CharField(max_length=2, verbose_name='Who WTS', choices=[('kz', 'kk'), ('kz', 'kk')])
    rate = models.PositiveSmallIntegerField(
        verbose_name='WTS rate', validators=[MinValueValidator(1), MaxValueValidator(5)])
    rate_recommended = models.FloatField(null=True, validators=[MinValueValidator(1), MaxValueValidator(10)])

    def __str__(self):
        return f"WTS - {str(self.movie)}"


class Actor(models.Model):
    movie = models.ManyToManyField(Movie, through='Role', related_name='actors')
    actor_id = models.PositiveIntegerField(primary_key=True)
    actor_name = models.CharField(max_length=40, verbose_name='Actor name')
    gender = models.CharField(blank=True, max_length=1, verbose_name='Gender', choices=[('M', 'male'), ('F', 'female')])
    rate = models.FloatField(
        null=True, blank=True, verbose_name='Actor rate', validators=[MinValueValidator(1), MaxValueValidator(10)])
    role_count = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Roles count')
    user_rate = models.FloatField(
        null=True, blank=True, verbose_name='My actor rate', validators=[MinValueValidator(1), MaxValueValidator(10)])
    link = models.URLField()

    def __str__(self):
        return self.actor_name


class Role(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='roles')
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, related_name='roles')
    role_id = models.PositiveIntegerField(primary_key=True)
    rate = models.FloatField(
        verbose_name='Role rate', validators=[MinValueValidator(1), MaxValueValidator(10)])
    rate_count = models.PositiveIntegerField(verbose_name='Role rate count')
    top = models.PositiveIntegerField(null=True, blank=True, verbose_name='TOP actors')
    user_rate = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='My role rate', validators=[MinValueValidator(1), MaxValueValidator(10)])

    def __str__(self):
        return f"{self.actor} in {self.movie}"


class Country(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='countries')
    country = models.CharField(max_length=30, verbose_name='Country')
    code = models.CharField(max_length=2, verbose_name='County code')

    def __str__(self):
        return self.country

    def country_codes(self):
        countries = sorted(
            Country.objects.filter(movie=self.movie), key=lambda x: x.code not in ['PL', 'US', 'FR'])[:3]
        return '/'.join(country.code for country in countries)


class Genre(models.Model):
    movie = models.ManyToManyField(Movie, related_name='genres')
    genre = models.CharField(primary_key=True, max_length=30, verbose_name='Genre')
    like = models.PositiveSmallIntegerField(
        null=True, verbose_name='Genre like', validators=[MinValueValidator(1), MaxValueValidator(5)])
    short = models.CharField(max_length=5, verbose_name='Genre abbrev.')

    def __str__(self):
        return self.genre


class NetflixManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(vod='netflix')


class HboManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(vod='hbo_max')


class AmazonManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(vod='amazon')


class DisneyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(vod='disney')


class CanalManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(vod='canal_plus_manual')


class AppleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(vod='apple_tv')


class OtherVodManager(models.Manager):
    def get_queryset(self):
        vods_main = super().get_queryset().filter(
            vod__in=['netflix', 'hbo_max', 'amazon', 'disney', 'apple_tv', 'canal_plus_manual']
        ).values_list('movie_id', flat=True)
        return super().get_queryset().exclude(
            movie_id__in=vods_main)


class Vod(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='vods')
    vod = models.CharField(max_length=20, verbose_name='VOD')

    objects = models.Manager()
    netflix = NetflixManager()
    hbo = HboManager()
    amazon = AmazonManager()
    disney = DisneyManager()
    apple = AppleManager()
    canal = CanalManager()
    other_vod = OtherVodManager()

    def __str__(self):
        return self.vod

    @property
    def vod_list_comma(self):
        vod_names = {
            'hbo_max': 'HBO',
            'apple_tv': 'apple',
            'canal_plus_manual': 'canal+',
            'player_plus': 'player',
            'play_now': 'play',
        }
        vod_list = Vod.objects.filter(movie=self.movie)
        return ', '.join([vod_names[vod.vod] if vod.vod in vod_names.keys() else vod.vod for vod in vod_list])


class FilmwebCredentials(models.Model):
    user = models.OneToOneField('auth.User', primary_key=True, on_delete=models.CASCADE)
    user_name = models.CharField(blank=True, max_length=20)
    cookie = models.CharField(blank=True, max_length=3000)
    user_agent = models.CharField(
        max_length=200,
        default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/102.0.0.0 Safari/537.36'
    )

    def __str__(self):
        return self.user_name
