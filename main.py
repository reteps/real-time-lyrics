from acrcloud.recognizer import ACRCloudRecognizer
import sounddevice as sd
import wave
import scipy.io.wavfile as wavf
from synced_lyric_sources import get_lyrics
import json
from timeit import default_timer as timer
import time

RATE = 44100
CHANNELS = 1
CHUNK = 1024
SECONDS = 10
def save_frames_to_wav(filename, frames):
    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

if __name__ == '__main__':
    config = {
        'host': 'identify-eu-west-1.acrcloud.com',
        'access_key': 'fe9e8e87f476705b22cd4cd413e027a2',
        'access_secret': 'DWBx6uRqVbLYzzI4NDChJid4OTS3T2m7lf2gAob0',
        'timeout': 10
    }

    data = sd.rec(int(SECONDS * RATE), samplerate=RATE, channels=2)
    sd.wait()
    print('Snip Found')
    wavf.write('out.wav', RATE, data)
    re = ACRCloudRecognizer(config)
    results = json.loads(re.recognize_by_file('out.wav', 0))
    response_time = results['cost_time']
    load_lyric_start = timer()
    for result in results['metadata']['music']:
        artist = result['artists'][0]['name'].split(';')[0]
        song = result['title']
        current_time = result['play_offset_ms'] / 1000
        print('Possible song -', song, artist)
        lyrics, url = get_lyrics(artist, song)
        if lyrics != None:
            print('Found URL:', url)
            break
    lyric_load_time = timer() - load_lyric_start

    lyric_start_time = current_time + response_time + lyric_load_time
    current_lyric_time = lyric_start_time
    for i in range(len(lyrics) - 1):
        lyric = lyrics[i]
        if lyric[0] > current_lyric_time: # If ahead, sleep
            time.sleep(lyric[0] - current_lyric_time + .01)
            current_lyric_time += lyric[0] - current_lyric_time + .01
            lyric = lyrics[i+1] # Print next line

        m,s = divmod(int(lyrics[i+1][0]), 60)
        ts = f'{m}:{s:02}'
        print(ts, lyrics[i+1][1])