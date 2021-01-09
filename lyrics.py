import requests
import re
import html
from bs4 import BeautifulSoup
import unicodedata

def get_lyrics(artist, song):
    for engine in ENGINES:
        res = engine(artist, song)
        if res:
            return res, engine.__name__
    return None, None
def sogeci(artist, song):
    artist_fixed = re.sub(r'\W+', '', artist)
    artist_page = f'http://www.sogeci.net/geshou/{artist_fixed}.html'
    page = requests.get(artist_page)
    if page.status_code == 404:
        return None
    soup = BeautifulSoup(page.text, 'lxml')
    links = soup.find('div', class_='showNewSong')
    links = links.find_all('a')
    url = None
    for link in links:
        if link['title'].lower() in song.lower():
            url = 'http://www.sogeci.net' + link['href']
            break
    if url is None:
        return None
    
    lyric_regex = re.compile('<pre>([\s\S]*?)</pre>')
    lyric_page = requests.get(url).text
    lyrics = re.search(lyric_regex, lyric_page).group(1)
    return lyrics.strip()
def syair(artist, song):
    UA = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Safari/537.36'}
    name_normalized = ' '.join(re.sub(r'\W+',' ', artist).split(' '))
    search_page = requests.get("https://www.syair.info/search", params={
    "q": f'{name_normalized} {song}'
    }, headers = UA).text
    soup = BeautifulSoup(search_page, 'lxml')
    result_container = soup.find("div", class_="sub")
    if result_container:
        result_list = result_container.find_all("div", class_="li")

        if result_list:
            url = None
            for i, li in enumerate(result_list):
                result = li.find('a')
                name = result.text.lower()
                if (artist.lower() in name or name_normalized.lower() in name) and song.lower() in name:
                    url = "https://www.syair.info"
                    if '[offset:' in li.text:
                        # check next one just in case
                        next_link = result_list[i+1].find('a')
                        if next_link.text.lower() == name:
                            url += next_link['href']
                        else:
                            url += result['href']
                    else:
                        url += result['href']
                    print(url)
                    break
            
            if url:
                lyrics_page = requests.get(url, headers = UA)
                soup = BeautifulSoup(lyrics_page.text, 'lxml')
                lrc_link = None
                for download_link in soup.find_all("a", attrs={"rel": "nofollow"}):
                    if "download.php" in download_link["href"]:
                        lrc_link = "https://www.syair.info" + download_link["href"]
                        break
                if lrc_link:
                    lrc = requests.get(lrc_link,
                                        cookies=lyrics_page.cookies, headers = UA).text
                    return lrc
    return None
def mooflac(artist, song):
    def get_cookies():
        login_url = 'https://www.mooflac.com/login'
        res = requests.get(login_url)
        token_re = re.compile(r'name="_token" value="(.*)"')
        token = re.search(token_re, res.text).group(1)

        body = {
            'email': 'peter.promotions.stenger@gmail.com',
            'password': 'retep123',
            '_token': token
        }
        return requests.post(login_url, body, cookies=res.cookies).cookies
    def get_lyrics(url):
        lyrics_page = requests.get(url, cookies=lyric_cookies).text
        has_lyrics = 'lyric-context' in lyrics_page
        if not has_lyrics:
            return None
        lyrics_re = re.compile(r'<div class="hidden" id="lyric-context">([\s\S]*?)</div>')
        lyrics = re.search(lyrics_re, lyrics_page)
        lyrics = '\n'.join([html.unescape(line.split('<br>')[0]) for line in lyrics.group(1).split('\n')])
        if '[' not in lyrics and ']' not in lyrics:
            return None
        return lyrics
    lyric_cookies = get_cookies()
    name_normalized = ' '.join(re.sub(r'\W+',' ', artist).split(' '))

    search_page = requests.get('https://www.mooflac.com/search', params={
        'q': song + ' ' + name_normalized 
    }, cookies=lyric_cookies).text
    soup = BeautifulSoup(search_page, 'lxml')
    result_table = soup.find('tbody')
    url = None
    if result_table:
        for result in result_table.find_all('tr')[:10]:
            links = result.find_all('td')
            href = links[0].find('a')['href']
            text = [unicodedata.normalize("NFKD", l.text.strip()) for l in links]
            res_song = text[0].lower()
            res_artist = text[1].lower()
            if song.lower() in res_song and (name_normalized.lower() in res_artist or artist.lower() in res_artist):
                return get_lyrics(href)
    return None


def rentanadvisor(artist, song):
    service_name = "RentAnAdviser"
    url = ""

    search_results = requests.get("https://www.rentanadviser.com/en/subtitles/subtitles4songs.aspx", 
        params={'src': f'{artist} {song}'})
    soup = BeautifulSoup(search_results.text, 'html.parser')
    result_links = soup.find(id="tablecontainer").find_all("a")

    for result_link in result_links:
        if result_link["href"] != "subtitles4songs.aspx":
            lower_title = result_link.get_text().lower()
            if artist.lower() in lower_title and song.lower() in lower_title:
                url = "https://www.rentanadviser.com/en/subtitles/%s&type=lrc" % result_link["href"]
                break

    if url:
        possible_text = requests.get(url)
        soup = BeautifulSoup(possible_text.text, 'html.parser')

        event_validation = soup.find(id="__EVENTVALIDATION")["value"]
        view_state = soup.find(id="__VIEWSTATE")["value"]

        lrc = requests.post(url, {"__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnlyrics",
                                    "__EVENTVALIDATION": event_validation,
                                    "__VIEWSTATE": view_state}).text

        return lrc

    return None
def megalobiz(artist, song):
    service_name = "Megalobiz"
    url = ""
    search_results = requests.get("https://www.megalobiz.com/search/all", params={
    "qry": f'{artist} {song}',
    "display": "more"
    })
    soup = BeautifulSoup(search_results.text, 'html.parser')
    result_links = soup.find(id="list_entity_container").find_all("a", class_="entity_name")

    for result_link in result_links:
        lower_title = result_link.get_text().lower()
        if artist.lower() in lower_title and song.lower() in lower_title:
            url = "https://www.megalobiz.com%s" % result_link["href"]
            break

    if url:
        possible_text = requests.get(url)
        soup = BeautifulSoup(possible_text.text, 'html.parser')

        lrc = soup.find("div", class_="lyrics_details").span.get_text()
        return lrc
    return None
ENGINES = [sogeci, mooflac, syair] # rentanadvisor, megalobiz]
