import threading

import numpy as np
import sounddevice as sd


class DirectOutput:
    def __init__(self, device, sample_rate=44100, channels=1):
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream = None
        self._lock = threading.Lock()

    def _callback(self, outdata, frames, time, status):
        with self._lock:
            if self.channels == 2:
                # Caprice32 version
                chunk = self.device.generate(frames)
                outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 2)
            else:
                # MAME version
                chunk = self.device.generate(frames, self.sample_rate)
                outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 1)

    def start(self):
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                callback=self._callback
            )
            self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
