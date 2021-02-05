from acrcloud.recognizer import ACRCloudRecognizer
import sounddevice as sd
import wave
import scipy.io.wavfile as wavf
import json
from timeit import default_timer as timer
import time
from lrc_kit import ComboLyricsProvider, SearchRequest
import os
import re
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint

load_dotenv()

RATE = 44100
CHUNK = 1024
SECONDS = 10

wordlist = '''fuck
hoes
hoe
ass
bitch
bitches
fucked
titties
pussy
fuckin
dope
dick
fucking
shit
damn
codeine
dickride
motherfuckers
motherfucking
motherfuckin'
shit's
fuckin'
motherfucker
motherfucka
fuckers
faggots
niggas
nigga
niggas
sex'''.split('\n')
endings = [',','!','.',')','?']
beginnings = ['(']
addl_words = []
for symbol in endings:
    addl_words.extend([word + symbol for word in wordlist])
wordlist.extend(addl_words)
addl_words = []
for symbol in beginnings:
    addl_words.extend([word + symbol for word in wordlist])
wordlist.extend(addl_words)
def uncensor(word):
    if '*' not in word:
        return word
    start, end = re.split('\*+', word)
    if len(start) == len(end) == 0:
        return word
    capital = word.lower() != word
    possible_words = list(filter(lambda x: len(x) == len(word) and x.startswith(start.lower()) and x.endswith(end.lower()), wordlist))
    if len(possible_words) != 1:
        return word
    uncensored = possible_words[0]
    if capital:
        uncensored = uncensored[0].upper() + uncensored[1:]
    return uncensored
def get_subs():
    while True:
        print('Recording... ',end='\r')
        data = sd.rec(int(SECONDS * RATE), samplerate=RATE, channels=2)
        sd.wait()
        wavf.write('out.wav', RATE, data)
        acr = ACRCloudRecognizer(config)
        results = json.loads(acr.recognize_by_file('out.wav', 0))
        if results.get('status') and results['status'].get('code') == 1001:
            continue
        break
    with open('logs/res_dump.json', 'w') as f:
        json.dump(results, f, indent=2)
    response_time = results['cost_time']
    load_lyric_start = timer()
    subs = None
    for result in acr['metadata']['music']:
        artist = result['artists'][0]['name'].split(';')[0]
        song = result['title']
        offset_time = result['play_offset_ms'] / 1000
        run_time = result['duration_ms'] / 1000
        print(song, artist)
        search_request = SearchRequest(artist, song)
        subs = ComboLyricsProvider().search(search_request)
        if subs:
            print(f"Found Using Engine '{subs.metadata['provider']}'")
            return subs, load_lyric_start-response_time-offset_time, run_time, song
    return None
def get_spotify_subs():
    while True:
        track = sp.current_user_playing_track()
        if track is not None:
            break
        time.sleep(1)

    load = timer()
    # pprint(track)
    current_pos = track['progress_ms']
    song = track['item']['name']
    artist = track['item']['artists'][0]['name']
    runtime = track['item']['duration_ms']
    search_request = SearchRequest(artist, song)
    subs = ComboLyricsProvider().search(search_request)
    if subs:
        print(f"Found Using Engine '{subs.metadata['provider']}'")
        search_time = timer() - load
        return subs, current_pos / 1000 + search_time, runtime / 1000, song
if __name__ == '__main__':
    config = {
        'host': 'identify-eu-west-1.acrcloud.com',
        'access_key': os.getenv('ACR_ACCESS_KEY'),
        'access_secret': os.getenv('ACR_ACCESS_SECRET'),
        'timeout': 10
    }
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv('SPOTIFY_ID'),
                                                client_secret=os.getenv('SPOTIFY_SECRET'),
                                                redirect_uri="https://google.com",
                                                scope="user-read-currently-playing"))

    
    while True:

        # subs, load_lyric_start = get_subs(config)
        subs, load_lyric_start, run_time, so = get_spotify_subs()
        print(so)
        if subs is None:
            input('No matches. Next song?')
            continue
        lyric_start_time = load_lyric_start
        current_time = lyric_start_time
        lookahead_time = 0.25
        song_ended = timer()
        since_last_check = 0
        for line in subs.lyrics:
            passed = True
            # if hasattr(line, 'duration'):
            #     lookahead_time = line.duration
            time_to_line = line.time_seconds - current_time - lookahead_time
            if time_to_line > 0: # Print the line
                r2 = 0
                if since_last_check > 3:
                    r = timer()
                    t = sp.current_user_playing_track()
                    r2 = timer() - r
                    if t and t['item']['name'] != so:
                        print('different', t['item']['name'], so)
                        break
                    since_last_check = 0
                time.sleep(time_to_line - r2)
                since_last_check += time_to_line - r2
                current_time = line.time_seconds - lookahead_time
            else:
                passed = False
            m,s = divmod(int(line.time_seconds), 60)
            ts = f'{m}:{s:02}'
            if not line.timing:
                print(ts, ' '.join(uncensor(w) for w in line.text.split(' ')))
            else:
                print(ts, ' ')
                for word in line.timing:
                    print(word.text)
                    # print(word.duration)
                    if passed:
                        time.sleep(word.duration / 1000)
                        current_time += word.duration / 1000
                print()
        else:
            current_time += lookahead_time
            if run_time > current_time:
                time.sleep(run_time - current_time)