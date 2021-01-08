from acrcloud.recognizer import ACRCloudRecognizer
import pyaudio
import wave

RATE = 44100
FORMAT = pyaudio.paInt16
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
def callback(input_data, frame_count, time_info, flags):

    return input_data, pyaudio.paContinue
if __name__ == '__main__':
    config = {
        'host': 'identify-eu-west-1.acrcloud.com',
        'access_key': 'fe9e8e87f476705b22cd4cd413e027a2',
        'access_secret': 'DWBx6uRqVbLYzzI4NDChJid4OTS3T2m7lf2gAob0',
        'timeout': 10
    }

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK, input_device_index=1)
    #, stream_callback=callback
    frames = []
    for _ in range(RATE // (CHUNK * SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    audio.terminate()

    save_frames_to_wav('out.wav', frames)

    # re = ACRCloudRecognizer(config)