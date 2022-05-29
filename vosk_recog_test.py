from vosk import Model, KaldiRecognizer
import os
import pyaudio

class QueryRecognizer:
    def __init__(self, model_name):
        model = Model(model_name)
        self.rec = KaldiRecognizer(model, 44100)
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=44100, 
            input=True, 
            frames_per_buffer=4000
        )
    def recognize(self):
        while True:
            __data = self.stream.read(4000, exception_on_overflow = False)
            if self.rec.AcceptWaveform(__data):
                return self.rec.Result()


q = QueryRecognizer(r"./vosk-model-small-ru-0.22")
while True:
    q.recognize()