from acrcloud.recognizer import ACRCloudRecognizer
import sounddevice as sd
import wave
import scipy.io.wavfile as wavf
from lyrics import get_lyrics
import json
from timeit import default_timer as timer
import time
import pylrc
import os
import re
from dotenv import load_dotenv
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
if __name__ == '__main__':
    config = {
        'host': 'identify-eu-west-1.acrcloud.com',
        'access_key': os.getenv('ACR_ACCESS_KEY'),
        'access_secret': os.getenv('ACR_ACCESS_SECRET'),
        'timeout': 10
    }

    while True:
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
        for result in results['metadata']['music']:
            artist = result['artists'][0]['name'].split(';')[0]
            song = result['title']
            offset_time = result['play_offset_ms'] / 1000
            run_time = result['duration_ms'] / 1000
            print(song, artist)
            lyrics, engine = get_lyrics(artist, song)
            if lyrics:
                print(f'Found Using Engine "{engine}"')
                if isinstance(lyrics, list):
                    subs = lyrics
                else:
                    subs = pylrc.parse(lyrics)
                break
        if subs is None:
            input('No matches. Next song?')
            continue
        lyric_load_time = timer() - load_lyric_start
        lyric_start_time = offset_time + response_time + lyric_load_time
        current_time = lyric_start_time
        lookahead_time = 2
        song_ended = timer()
        for line in subs:
            # if hasattr(line, 'duration'):
            #     lookahead_time = line.duration
            time_to_line = line.time - current_time - lookahead_time
            if time_to_line > 0: # Print the line
                time.sleep(time_to_line)
                current_time = line.time - lookahead_time
            m,s = divmod(int(line.time), 60)
            ts = f'{m}:{s:02}'
            print(ts, ' '.join(uncensor(w) for w in line.text.split(' ')))
        current_time += lookahead_time
        if run_time > current_time:
            time.sleep(run_time - current_time)