import requests
from bs4 import BeautifulSoup
# import html5lib
import json
from datetime import datetime
import re

# import logging
# logging.basicConfig(level=logging.DEBUG)
from movies.models import FilmwebCredentials, WTS


def extract_numbers(text: str, pl=True, thousand_sep=' ', all_numbers=False):
    """
    Extracting one or all number from a given string

    :param text: str with number(s) to be extracted from
    :param pl: True - , comma as decimal separator; False - . dot
    :param thousand_sep: str used as a thousand separator
    :param all_numbers: False - returns only 1st found number; True - returns list of all found numbers
    :return: extracted number or list of numbers (int or float)
    """
    def convert(number):
        try:
            return int(number)
        except ValueError:
            return float(number)
    if pl:
        text = re.sub('(?<=[0-9]),(?=[0-9])', '.', text)
    text = re.sub('(?<=[0-9])' + re.escape(thousand_sep) + '(?=[0-9]{3})', '', text)
    pattern = re.compile(r'-?\d+\.?\d*')
    result = [convert(number) for number in re.findall(pattern, text)]
    if all_numbers:
        return result
    else:
        return result[0]


def extract_award(awards):
    award_oscar = 0
    award = 0
    nomination = 0
    award_pattern = re.compile(r'\d+(?= inn)')
    award_search = re.search(award_pattern, awards)
    if award_search:
        award += int(award_search.group())
        oscar_one_pattern = re.compile(r'(?!<=\d+)(?:[\sa-zóęą]*)(Oscar|BAFTA|Satelita|Independent)')
        oscar_pattern = re.compile(r'(\d+)(?:[\sa-zóęą]*)(Oscar|BAFTA|Satelita|Independent)')
        oscar_one_search = re.search(oscar_one_pattern, awards)
        oscar_search = re.search(oscar_pattern, awards)
        if oscar_one_search and not oscar_search:
            if oscar_one_search.group(1) == 'Oscar':
                award_oscar += 1
            else:
                award += 1
        if oscar_search:
            if oscar_search.group(2) == 'Oscar':
                award_oscar += int(oscar_search.group(1))
            else:
                award += int(oscar_search.group(1))
    else:
        award_2_pattern = re.compile(r'\d{1,3}(?= nagr)')
        award_2_search = re.search(award_2_pattern, awards)
        if award_2_search:
            award += int(award_2_search.group(0))
    nomination_pattern = re.compile(r'\d{1,3}(?= nomi)')
    nomination_search = re.search(nomination_pattern, awards)
    if nomination_search:
        nomination += int(nomination_search.group())
    return award_oscar, award, nomination


def get_header(user_agent, cookie):
    headers = {
        # 'Host': 'www.filmweb.pl',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'cash-control': 'max-age=0',
        'cookie': cookie,
        # 'Origin': 'https://www.filmweb.pl',
        'dnt': '1',
        # 'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        # 'sec-ch-mobile': '?0',
        # 'sec-ch-platform': '"Windows"',
        # 'sec-fetch-dest': 'document',
        # 'sec-fetch-mode': 'navigate',
        # 'sec-fetch-site': 'none',
        # 'sec-fetch-user': '?1',
        # 'Connection': 'keep-alive',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
    }
    return headers


def get_url(url, user=False):

    if user:
        user_obj = FilmwebCredentials.objects.get(user=user)
        user_agent = user_obj.user_agent
        cookie = user_obj.cookie
        response = requests.get(url, headers=get_header(user_agent, cookie))
        # response = requests.get(url, headers={**HEADERS})
    else:
        response = requests.get(url)
    # if not response.ok:
    #     print(f"Code: {response.status_code}, url: {url}")
    return BeautifulSoup(response.content, 'html.parser')  # 'lxml'


def parse_vod(url):
    vod = []
    try:
        url_vod = url + '/vod'
        soup_vod = get_url(url_vod)
        for i in soup_vod.find_all('li', {'class': 'filmVodSection__item'}):
            if i.find('div', {'class': 'filmVodSection__badge'}).get_text() == "abonament":
                vod.append(i.get('data-provider'))
    except Exception:
        pass
    if 'hbo_max' in vod and 'canal_plus_manual' in vod:
        vod.remove('canal_plus_manual')
    if 'amazon' in vod:
        vod = ['amazon']
    return vod


def get_movies_rated(user, test=False, run=False):
    movies_rated = {}
    if not run:
        return movies_rated
    page_no = 0

    page_rates_count = "https://www.filmweb.pl/user/uball/films?sortBy=RATE_DESC"
    soup = get_url(page_rates_count, user=True)
    soup = soup.find('div', {'class': 'barFilter__rates'})
    soup = soup.find_all('button', {'class': 'barFilter__bar'})
    rates_counts = {}
    for i in soup[1:][::-1]:
        rates_counts.update({int(i.get('data-id')): int(i.get('data-count'))})
    movie_cnt = 0
    curr_rate = max(rates_counts.keys())

    while True:
        page_no += 1
        if test and page_no == 2:
            break
        page = f'https://www.filmweb.pl/user/{user}/films?sortBy=RATE_DESC&page={page_no}'
        soup = get_url(page, user=True)

        soup = soup.find_all('div', {'class': 'voteBoxes__box'})
        if len(soup) == 0:
            break
        for movie in soup:
            movie_cnt += 1
            curr_rate_qty = rates_counts.get(curr_rate)
            if curr_rate_qty + 1 == movie_cnt:
                movie_cnt = 1
                while True:
                    curr_rate -= 1
                    if curr_rate_qty > 0 or curr_rate_qty is None:
                        break

            movie_id = movie.get('data-id')
            link = 'https://www.filmweb.pl' + movie.find('a', {'class': 'preview__link'}).get('href')
            title = movie.find('a', {'class': 'preview__link'}).get_text()
            try:
                title_original = movie.find('div', {'class', 'preview__originalTitle'}).get_text()
            except Exception:
                title_original = movie.find('a', {'class': 'preview__link'}).get_text()
            year = int(movie.find('div', {'class', 'preview__year'}).get_text())

            movies_rated.update({
                movie_id: {
                    'link': link,
                    'title': title,
                    'title_original': title_original,
                    'year': year,
                    'user_rate': curr_rate,
                    'wts_rate': None
                }
            })
    movies_rated = get_movie_data(movies_rated, test, vod_in=False)
    return movies_rated


def get_movies_wts(user, test=False):
    movies_wts = {}
    page_no = 0
    already_uploaded = False
    movies_uploaded = WTS.objects.all().values_list('movie_id', flat=True)
    while True:
        page_no += 1
        if (test and page_no == 2) or already_uploaded is True:
            break

        page = f'https://www.filmweb.pl/user/{user}/wantToSee?filmType=FILM&page={page_no}'
        soup = get_url(page, user=True)

        soup = soup.find_all('div', {'class': 'voteBoxes__box'})
        if len(soup) == 0:
            break
        for movie in soup:
            movie_id = movie.get('data-id')
            wts_rate = int(movie.find('div', {'class': 'userRate'}).get('data-rate'))

            int_movie_id = int(movie_id)
            if int_movie_id in movies_uploaded and \
                    len(WTS.objects.filter(movie_id=int_movie_id)) == 1 and \
                    wts_rate == WTS.objects.get(movie_id=int_movie_id).rate:
                already_uploaded = True
                break

            link = 'https://www.filmweb.pl' + movie.find('a', {'class': 'preview__link'}).get('href')
            title = movie.find('a', {'class': 'preview__link'}).get_text()
            try:
                title_original = movie.find('div', {'class': 'preview__originalTitle'}).get_text()
            except Exception:
                title_original = movie.find('a', {'class': 'preview__link'}).get_text()
            year = int(movie.find('div', {'class': 'preview__year'}).get_text())

            movies_wts.update({
                movie_id: {
                    'link': link,
                    'title': title,
                    'title_original': title_original,
                    'year': year,
                    'user_rate': None,
                    'wts_rate': wts_rate
                }
            })
    movies_wts = get_movie_data(movies_wts, test, vod_in=True)
    return movies_wts


def get_movie_data(movies_header, test, vod_in: bool):
    for movie in movies_header.values():
        url = movie['link']
        soup = get_url(url)

        rate = round(float(soup.find('div', {'class': 'filmRating'}).get('data-rate')), 3)
        rate_count = int(soup.find('div', {'class': 'filmRating'}).get('data-count'))
        try:
            critic_rate = extract_numbers(
                soup.find('div', {'class': 'filmRating--filmCritic'})
                .find('span', {'class': 'filmRating__rateValue'}).get_text())
        except Exception:
            critic_rate = None

        genre = []
        try:
            soup_genre = soup.find('div', {'class': 'filmInfo__info', 'itemprop': 'genre'})
            for i in soup_genre.find_all('a'):
                genre.append(i.get_text())
        except Exception:
            pass

        country = []
        award_oscar = award = nomination = 0
        soup_film_info = soup.find('div', {'class': 'filmPosterSection__info'}).find_all('h3')
        for i in soup_film_info:
            if i.get_text() == "produkcja":
                for j in i.next_sibling.find_all('a'):
                    country.append(j.get_text())
            elif i.get_text() == "nagrody":
                awards = i.next_sibling.find('a').get_text().strip().replace('\xa0', ' ')
                award_oscar, award, nomination = extract_award(awards)

        try:
            soup_awards = soup.find('div', {'class': 'awardsSection__title'}).get_text().strip().replace('\xa0', ' ')
        except Exception:
            pass
        else:
            award_oscar, award, nomination = extract_award(soup_awards)

        box_office = None
        box_office_usa = None
        box_office_outside_usa = None
        budget = None
        try:
            soup_info_section = soup.find('div', {'class': 'filmOtherInfoSection__group'})
            soup_box_office = soup_info_section.find_all('div', {'class': 'filmInfo__header'})
            for i in soup_box_office:
                if i.get_text() == "boxoffice":
                    for j in i.next_sibling.find_all():
                        box_office_text = j.get_text()
                        box_office_number = round(extract_numbers(box_office_text) / 1000000, 1)
                        if box_office_text.find('na świecie') != -1:
                            box_office = box_office_number
                        elif box_office_text.find('w USA') != -1:
                            box_office_usa = box_office_number
                        elif box_office_text.find('poza USA') != -1:
                            box_office_outside_usa = box_office_number
                elif i.get_text() == "budżet":
                    budget = round(extract_numbers(i.next_sibling.get_text()) / 1000000, 1)
        except Exception:
            pass

        try:
            director = soup.find('a', {'itemprop': 'director'}).get('title')
        except Exception:
            director = ''

        soup_actors = soup.find('div', {'class': 'crs--persons'})
        actors = []
        try:
            for i in soup_actors.find_all('div', {'class': 'crs__item'}):
                try:
                    actor_id = int(i.find('div', {'class': 'personRole'}).get('data-person-id'))
                    role_id = int(i.find('div', {'class': 'personRole'}).get('data-role-id'))
                    actor_name_soup = i.find('h3', {'class': 'personRole__title'})
                    actor_name = actor_name_soup.find('span').get_text()
                    # actor_name = i.find('span', {'data-person-source': ''}).get_text() - previous ver for top actors
                    actor_link = 'https://www.filmweb.pl' + actor_name_soup.find('a').get('href')
                    # role_txt = f"role-{role_id}"
                    # role = eval(soup.find('script', {'data-source': role_txt, 'type': 'application/json'}).get_text())
                    gender = ''  # role['person']['gender']
                    try:
                        role_top = extract_numbers(i.find('a', {'class': 'personRole__ranking'}).get_text())
                    except Exception:
                        role_top = None
                    try:
                        role_rate = extract_numbers(i.find('span', {'class', 'personRole__ratingRate'}).get_text())
                        role_rate_count = extract_numbers(
                            i.find('span', {'class', 'personRole__ratingCount'}).get_text())
                    except Exception:
                        # actor_name = role['person']['name']
                        role_rate = round(extract_numbers(i.find('div', {'class': 'personRole'}).get('data-rate')), 1)
                        role_rate_count = int(i.find('div', {'class': 'personRole'}).get('data-count'))
                    actor = {
                        'actor_id': actor_id,
                        'role_id': role_id,
                        'actor_name': actor_name,
                        'gender': gender,
                        'role_rate': role_rate,
                        'role_rate_count': role_rate_count,
                        'role_top': role_top,
                        'actor_link': actor_link,
                    }
                    actors.append(actor)
                except Exception:
                    pass
        except Exception:
            pass

        vod = []
        if vod_in:
            vod = parse_vod(url)

        movie.update({
            'rate': rate,
            'rate_count': rate_count,
            'critic_rate': critic_rate,
            'genre': genre,
            'country': country,
            'award_oscar': award_oscar,
            'award': award,
            'nomination': nomination,
            'box_office': box_office,
            'box_office_usa': box_office_usa,
            'box_office_outside_usa': box_office_outside_usa,
            'budget': budget,
            'director': director,
            'actors': actors,
            'vod': vod
        })
    if test:
        file_name = fr".\movies\resources\movies_{str(datetime.now().strftime('%y-%m-%d.%H-%M-%S'))}.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(json.dumps(movies_header))

    return movies_header
