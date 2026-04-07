import threading
from typing import Any, Optional, Union

import numpy as np
import sounddevice as sd


class DirectOutput:
    def __init__(self, device: Any, sample_rate: int = 44100, channels: int = 1) -> None:
        self.device: Any = device
        self.sample_rate: int = sample_rate
        self.channels: int = channels
        self.stream: Optional[sd.OutputStream] = None
        self._lock: threading.Lock = threading.Lock()

    def _callback(self, outdata: np.ndarray, frames: int, time: Any, status: sd.CallbackFlags) -> None:
        with self._lock:
            if self.channels == 2:
                # Caprice32 version
                chunk = self.device.generate(frames)
                outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 2)
            else:
                # MAME version
                chunk = self.device.generate(frames, self.sample_rate)
                outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 1)

    def start(self) -> None:
        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                callback=self._callback
            )
            self.stream.start()

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
