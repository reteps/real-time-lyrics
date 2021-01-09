# Real time lyric detection

![godzilla gif](godzilla.gif)
# Setup

```
$ python3 -m pip install -r requirements.txt
```

Set the environment variables in `.env` or elsewhere:
+ `ACR_ACCESS_KEY`
+ `ACR_ACCESS_SECRET`

Then simply

```
$ python3 main.py
```


The program will first record audio from the microphone, then identify it using [acrcloud](https://acrcloud.com).

Next the identified song is looked up on `LRC` sites, such as:

+ http://www.sogeci.net/
+ https://www.mooflac.com/
+ https://www.syair.info/

These sites are not used, but are implemented. I have found them to have minimal LRCs that the previous 3 sites do not have.

+ https://www.rentanadviser.com/
+ https://www.megalobiz.com/

If you have access to it, I reccommend using the musixmatch subtitle service.

Next, the song is synced up the lyrics and printed out `2` seconds ahead of when the lyrics are actually spoken.

### Current bugs

+ If you find a snippet in a chorus, the lyric timing will be off if it identifies the chorus in another part of the song instead.

+ Sampling can lead to the program searching for a very old or relatively unknown song before the main song.

+ The original swear words cannot be recovered if the word is completely starred out. E.g. `****` does not work, but `d**k` -> `dick`.

### Other quirks

The `out.wav` file and `logs/res_dump.json` are written to the current directory every record / identification cycle.

I am using my personal login for the `mooflac.com` lyric site. Maybe don't change it. Otherwise I will have to force users to create their own account for the site.