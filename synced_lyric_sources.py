from bs4 import BeautifulSoup
import requests

UA = "Mozilla/5.0 (Maemo; Linux armv7l; rv:10.0.1) Gecko/20100101 Firefox/10.0.1 Fennec/10.0.1"
ERROR = False

def RentAnAdvisorSource(artist, song):
    service_name = "RentAnAdviser"
    url = ""

    try:
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

            return lrc, url, service_name, True

    except Exception as error:
        print("%s: %s" % (service_name, error))
    return ERROR, url, service_name, False
def valid_lyric_line(l):
    return ']' in l and len(l[l.index(']')+1:]) > 0 and l[1].isdigit() and 'RentAnAdviser.com' not in l
def get_lyrics(artist, song):
    for source in SOURCES:
        lrc, urls, service_name, success = source(artist, song)
        if success:
            lrc = [l.strip() for l in lrc.split('\n')]
            valid_lines = list(filter(valid_lyric_line, lrc))
            time_stamped_lines = []
            for l in valid_lines:
                parts = l.split(']', 1)
                lyric = parts[1]
                m, s = map(float, parts[0][1:].split(':'))
                time = round(m * 60 + s, 4)
                time_stamped_lines.append([time, lyric])
            return time_stamped_lines
    return None
def MegalobizSource(artist, song):
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
        return lrc, url, service_name, True
    return ERROR, url, service_name, False

def SyairSource(artist, song):
    service_name = "Syair"
    url = ""

    search_results = requests.get("https://www.syair.info/search", params={
    "q": f'{artist} {song}'
    }, headers={"User-Agent": UA})
    soup = BeautifulSoup(search_results.text, 'html.parser')

    result_container = soup.find("div", class_="sub")

    if result_container:
        result_list = result_container.find_all("div", class_="li")

        if result_list:
            for result in result_list:
                result_link = result.find("a")
                name = result_link.get_text().lower()
                if artist.lower() in name and song.lower() in name:
                    url = "https://www.syair.info%s" % result_link["href"]
                    break

            if url:
                lyrics_page = requests.get(url, headers={"User-Agent": UA})
                soup = BeautifulSoup(lyrics_page.text, 'html.parser')
                lrc_link = ""
                for download_link in soup.find_all("a"):
                    if "download.php" in download_link["href"]:
                        lrc_link = download_link["href"]
                        break
                if lrc_link:
                    lrc = requests.get("https://www.syair.info%s" % lrc_link,
                                        cookies=lyrics_page.cookies, headers={"User-Agent": UA}).text
                    return lrc, url, service_name, True
    return ERROR, url, service_name, False

SOURCES = [SyairSource, MegalobizSource, RentAnAdvisorSource]