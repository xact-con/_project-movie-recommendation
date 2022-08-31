# from crispy_forms.bootstrap import FormActions
from django import forms
# from django.forms import modelformset_factory, inlineformset_factory
from .models import FilmwebCredentials, Genre
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Field, Submit
import datetime as dt


class CredentialsForm(forms.ModelForm):

    class Meta:
        model = FilmwebCredentials
        fields = ['user_name', 'cookie', 'user_agent']


class GenreForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GenreForm, self).__init__(*args, **kwargs)
        self.fields['genre'].widget.attrs['readonly'] = True

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = "col-md-3"
        helper.layout = Layout(
            Field('genre', readonly=True, style="background-color: rgb(240 ,240, 240);"),
            'like',
        )
        helper.add_input(Submit('save', 'Save', css_class='mb-3 btn-primary btn-lg rounded-pill'))
        helper.form_method = "POST"
        helper.template = 'bootstrap/table_inline_formset.html'
        return helper

    class Meta:
        model = Genre
        fields = ['genre', 'like', 'short']


class MyRateForm(forms.Form):
    my_rate = forms.IntegerField(min_value=1, max_value=10)


class MoviesSearch(forms.Form):
    year_now = dt.datetime.now().year

    movies_set_choices = (('wts', 'WTS'), ('rated', 'rated'), ('all', 'all'))
    movies_set = forms.ChoiceField(label="Set of movies", choices=movies_set_choices, initial='WTS')
    votes_from = forms.IntegerField(label="Votes No. from", initial=0, min_value=0)
    box_office_min = forms.IntegerField(label="Box office from", initial=0, min_value=0)
    oscar_award = forms.ChoiceField(label="Oscars", choices=(('all', 'all'), ('yes', 'yes')), initial='all')
    vod_set_choices = (('all', 'all'), ('yes', 'yes'), ('other', 'other'), ('no', 'no'))
    vod_set = forms.ChoiceField(label="on VOD", choices=vod_set_choices, initial='yes')
    year_from = forms.IntegerField(label="Year from", initial=1940, min_value=1940, max_value=year_now)
    year_to = forms.IntegerField(label="Year to", initial=year_now, min_value=1940, max_value=year_now)
