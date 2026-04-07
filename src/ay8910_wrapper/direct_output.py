"""
Handles real-time audio output using sounddevice.
"""
import threading
from typing import Any, Optional, Union

import numpy as np
import sounddevice as sd


class DirectOutput:
    """
    Manages an audio stream to play sound from an emulator in real-time.

    Attributes:
        device (Any): The PSG emulator instance.
        sample_rate (int): Output sample rate in Hz.
        channels (int): Number of audio channels.
        stream (Optional[sd.OutputStream]): The current audio output stream.
    """
    def __init__(self, device: Any, sample_rate: int = 44100, channels: int = 1) -> None:
        """
        Initializes the direct output manager.

        Args:
            device: The emulator instance generating audio.
            sample_rate: Target sample rate for audio output (default 44100).
            channels: 1 for mono, 2 for stereo (default 1).
        """
        self.device: Any = device
        self.sample_rate: int = sample_rate
        self.channels: int = channels
        self.stream: Optional[sd.OutputStream] = None
        self._lock: threading.Lock = threading.Lock()

    def _callback(self, outdata: np.ndarray, frames: int, time: Any, status: sd.CallbackFlags) -> None:
        """
        Audio callback function for sounddevice to fetch samples from the emulator.

        Args:
            outdata: Output buffer to fill.
            frames: Number of frames to generate.
            time: Timing information.
            status: Callback flags (underflow, etc).
        """
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
        """
        Starts the audio output stream.
        """
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
