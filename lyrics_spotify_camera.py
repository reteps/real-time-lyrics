import pyvirtualcam
import numpy as np
from spotipy import Spotify, SpotifyOAuth
import lrc_kit
import time
from timeit import default_timer as timer
from dotenv import load_dotenv
import os
import sys
import math
import re
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont
load_dotenv()
import logging

HEIGHT = 240
WIDTH = 360

def to_min_sec_millis(millis):
    sign = 1
    if millis < 0:
        sign = -1
    m, s = divmod(millis, sign * 60 * 1000)
    s, mi = divmod(s, sign * 1000)
    mi = abs(mi)
    if sign == -1:
        if m != 0:
            m *= sign
        elif s != 0:
            s *= sign
        elif mi != 0:
            mi *= sign
    return m, s, mi

# logging.getLogger().setLevel('DEBUG')
class ExtendedSubs:
    def __init__(self, subs, runtime, currenttime, loadtime, song, artist, image):
        self.song = song
        self.artist = artist
        self.subs = subs
        self.runtime = runtime
        self.currenttime = currenttime
        self.loadtime = loadtime
        # self.image = Image.open(requests.get(image, stream=True).raw).convert('LA')
        self.isupdated = True
    def gen_frame(self, in_text, obj, use_obj=True):
        image = Image.new("RGBA", (WIDTH,HEIGHT), 'white')
        draw = ImageDraw.Draw(image)
        info = ImageFont.truetype('Helvetica-Bold.ttf', 20)
        draw.text((WIDTH//2, 25), self.song + ' - ' + self.artist, 'black', font=info, anchor='mm')
        if use_obj:
            m,s,millis = to_min_sec_millis(self.runtime*1000)
            timing = f'{obj.minutes:02}:{obj.seconds:02} / '
            timing += f'{int(m):02}:{int(s):02}'
            draw.text((WIDTH//2, 50), timing, 'black', font=info, anchor='mm')
        def font_fill_area(txt, stop, fontpath, direction=0, include_ascent=True):
            '''
            returns the font to have txt fill that % width of image
            '''
            jumpsize = 25
            fontsize = 25
            font = ImageFont.truetype(fontpath, fontsize)
            while True:
                size = draw.textsize(txt, font)[direction]
                if not include_ascent and direction == 1:
                    ascent, descent = font.getmetrics()
                    (width, height), (offset_x, offset_y) = font.font.getsize(txt)
                    size -= offset_y
                if size / stop < 1 and size / stop > .98:
                    break
                if size < stop:
                    fontsize += jumpsize
                else:
                    jumpsize = jumpsize // 2
                    fontsize -= jumpsize
                font = ImageFont.truetype(fontpath, fontsize)
                if jumpsize <= 1:
                    break
            return font

        start = 75
        pos = start
        final = []
        parts = in_text.split('\n')
        for i in range(len(parts)):
            if i == len(parts) - 2:
                color = 'red'
            else:
                color = 'black'
            line = parts[i]
            if len(line) > 50:
                final.extend([(l, color) for l in split_and_keep(line, ',')])
            else:
                final.append((line, color))
        for (line,color) in final:
            if len(line) == 0:
                continue
            if len(line) > 8:
                font = font_fill_area(line, WIDTH*.85, 'Helvetica-Bold.ttf')
                height = font.getsize(line)[1]
                draw.text((WIDTH//2, pos), line, color, font=font, anchor='mt')
                pos += height
            else:
                font = ImageFont.truetype('Helvetica-Bold.ttf', 35)
                draw.text((WIDTH//2, pos), line, color, font=font, anchor='mt')
                pos += 35
        # image = image.transpose(Image.FLIP_LEFT_RIGHT)
        return np.array(image)

print('Init Providers')
PROVIDER = lrc_kit.ComboLyricsProvider(lrc_kit.MINIMAL_PROVIDERS + [lrc_kit.Flac123Provider])
print('Done.')
class SpotifySubs(Spotify):
    def __init__(self, *args, **kwargs):
        self.current_subs = None
        super().__init__(*args, **kwargs)
    def current_user_playing_subs(self, current_time=0):
        start = timer()
        track = self.current_user_playing_track()
        if track and track['item']:
            current_pos = track['progress_ms']
            song = track['item']['name']
            artist = track['item']['artists'][0]['name']
            runtime = track['item']['duration_ms']
            image = track['item']['album']['images'][2]['url']
            if self.current_subs and (self.current_subs.song == song or self.current_subs.song == song.split('(')[0].split('-')[0].strip()):
                if abs((current_pos / 1000) - current_time) < 2:
                    self.current_subs.isupdated = False
                else:
                    self.current_subs.currenttime = current_pos / 1000
                    self.current_subs.loadtime = timer() - start
                    self.current_subs.isupdated = True
                return self.current_subs
            search_request = lrc_kit.SearchRequest(artist, song)
            subs = PROVIDER.search(search_request)
            if subs is None:
                if song.split('(')[0].split('-')[0].strip() != song:
                    song = song.split('(')[0].split('-')[0].strip()
                    search_request = lrc_kit.SearchRequest(artist, song)
                    print(search_request.as_string)
                    subs = lrc_kit.ComboLyricsProvider().search(search_request)
                    if subs is None:
                        return song + ' - ' + artist
                else:
                    return song + ' - ' + artist
            else:
                print(subs.metadata)
            search_time = timer() - start
            print('SEARCH TIME', search_time)
            print('CURRENT SPOT', current_pos / 1000)
            self.current_subs = ExtendedSubs(subs, runtime / 1000, current_pos / 1000, search_time, song, artist, image)
            return self.current_subs
        return None
   
# https://stackoverflow.com/questions/2136556/in-python-how-do-i-split-a-string-and-keep-the-separators
def split_and_keep(s, sep):
   if not s: return [''] # consistent with string.split()

   # Find replacement character that is not used in string
   # i.e. just use the highest available character plus one
   # Note: This fails if ord(max(s)) = 0x10FFFF (ValueError)
   p=chr(ord(max(s))+1) 

   return [x.replace(p,'') for x in s.replace(sep, sep+p).split(p, 1)]

if __name__ == '__main__':
    sp = SpotifySubs(auth_manager=SpotifyOAuth(client_id=os.getenv('SPOTIFY_ID'),
                                                client_secret=os.getenv('SPOTIFY_SECRET'),
                                                redirect_uri="https://google.com",
                                                scope="user-read-currently-playing"))

    LOOKAHEAD_TIME = 0
    CHECK_EVERY = 4
    extended_subs = None
    frames = 20
    old_subs = None
    with pyvirtualcam.Camera(width=WIDTH, height=HEIGHT, fps=frames) as cam:
        while True:

            if extended_subs is None or isinstance(extended_subs, str):
                possible_subs = sp.current_user_playing_subs()
                if possible_subs is None:
                    print('Error, no song is playing')
                    time.sleep(2)
                elif isinstance(possible_subs, str):
                    print(f'Could not find lyrics for: {possible_subs}')
                    image = Image.new("RGBA", (WIDTH,HEIGHT), 'white')
                    draw = ImageDraw.Draw(image)
                    info = ImageFont.truetype('Helvetica-Bold.ttf', 20)
                    font2 = ImageFont.truetype('Helvetica-Bold.ttf', 20)
                    draw.text((WIDTH//2, 25), possible_subs, 'black', font=info, anchor='mm')
                    draw.text((WIDTH//2, HEIGHT//2), 'Cannot find any lyrics for this song :/', 'black', font=font2, anchor='mm')
                    frame = np.array(image)
                    mytime = 2
                    start_sending_frames = timer()
                    while True:
                            if timer() - start_sending_frames > mytime:
                                break
                            cam.send(frame)
                            cam.sleep_until_next_frame()
                elif old_subs is None or old_subs.song != possible_subs.song:
                    print('Onto next song')
                    extended_subs = possible_subs
                else:
                    time.sleep(2)

            else:
                start_time = extended_subs.currenttime + extended_subs.loadtime
                print('Restarting...')
                current_time = start_time
                time_to_sleep = 0
                time_since_last_check = 0
                frames_to_wait = 0
                time_actually_waited = 0
                get_time = 0
                prematurely_break = False
                song_info = f"""Using lrc-kit 0.1.6.8. Loading song with engine "{extended_subs.subs.metadata['provider']}"..."""
                frame = extended_subs.gen_frame(song_info, None, use_obj=False)
                lyrics = extended_subs.subs.lyrics
                for j, line in enumerate(lyrics):
                    time_to_line = line.time_seconds - current_time - LOOKAHEAD_TIME
                    if time_to_line > 0:
                        get_time = 0
                        if time_since_last_check > CHECK_EVERY:
                            start = timer()
                            temp_subs = sp.current_user_playing_subs(current_time=current_time)
                            get_time = timer() - start
                            current_time += get_time
                            if temp_subs is None or isinstance(temp_subs, str) or temp_subs.isupdated:
                                # print('Breaking...')
                                extended_subs = temp_subs
                                prematurely_break = True
                                break
                        start_sending_frames = timer()
                        if j < len(lyrics) - 3:
                            lines = [l.text for l in lyrics[j-1:j+2]]
                            line_text = '\n'.join(lines)
                            next_frame = extended_subs.gen_frame(line_text, lyrics[j])
                        else:
                            next_frame = extended_subs.gen_frame(line.text, lyrics[j])
                        while True:
                            if timer() - start_sending_frames > time_to_line:
                                break
                            cam.send(frame)
                            cam.sleep_until_next_frame()
                        frame = next_frame
                        current_slept = timer() - start_sending_frames
                        time_since_last_check += current_slept
                        current_time += current_slept
                if not prematurely_break:
                    old_subs = extended_subs        
                    extended_subs = None
'''
with pyvirtualcam.Camera(width=1280, height=720, fps=30) as cam:
    while True:
        frame = np.zeros((cam.height, cam.width, 4), np.uint8) # RGBA
        frame[:,:,:3] = cam.frames_sent % 255 # grayscale animation
        frame[:,:,3] = 255
        cam.send(frame)
        cam.sleep_until_next_frame()
'''