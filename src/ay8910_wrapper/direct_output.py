"""
Handles real-time audio output using sounddevice.
"""
import threading
import sys
from typing import Any, Optional

try:
    import numpy as np
    import sounddevice as sd
except ImportError:
    np = None  # type: ignore
    sd = None  # type: ignore


class DirectOutput:
    """
    Manages an audio stream to play sound from an emulator in real-time.

    Note:
        Requires `numpy` and `sounddevice` libraries.
        Install them with: `pip install ay8910_wrapper[tools]`

    Args:
        device (Any): The emulator instance generating audio.
        sample_rate (int): Target sample rate for audio output (default: 44100).
        channels (int): 1 for mono, 2 for stereo (default: 1).
        clock (int): Master clock frequency (default: 1750000).

    Attributes:
        device (Any): The PSG emulator instance.
        sample_rate (int): Output sample rate in Hz.
        channels (int): Number of audio channels.
        stream (Optional[sd.OutputStream]): The current audio output stream.

    Example:
        ```python
        psg = ay8910()
        audio = DirectOutput(psg)
        audio.start()
        ```
    """
    def __init__(self, device: Any, sample_rate: int = 44100, channels: int = 1, clock: int = 1750000) -> None:
        self.device: Any = device
        self.sample_rate: int = sample_rate
        self.channels: int = channels
        self.clock: int = clock
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

        Example:
            This is typically called by sounddevice:
            ```python
            audio._callback(buffer, 1024, None, None)
            ```
        """
        with self._lock:
            # Check if it's one of our new wrapper classes
            from . import AYBase
            if isinstance(self.device, AYBase):
                chunk = self.device.generate(frames)
                # AYBase uses 2 channels for Caprice32 and 1 for others
                if self.channels == 2:
                    outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 2)
                else:
                    outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 1)
                return

            # Legacy support for native classes
            if self.channels == 2:
                # Caprice32 version
                chunk = self.device.generate(frames)
                outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 2)
            else:
                # MAME / Ay_Emul31 version
                try:
                    # Try MAME signature: generate(frames, sample_rate)
                    chunk = self.device.generate(frames, self.sample_rate)
                except TypeError:
                    # Try Ay_Emul31 signature: generate(frames, clock, sample_rate)
                    chunk = self.device.generate(frames, self.clock, self.sample_rate)
                
                outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 1)

    def start(self) -> None:
        """
        Starts the audio output stream.

        Example:
            ```python
            audio.start()
            ```
        """
        if sd is None or np is None:
            print("ERROR: The 'sounddevice' and 'numpy' libraries are not installed.", file=sys.stderr)
            print("Real-time audio output is not available. Please install them by running:", file=sys.stderr)
            print("pip install ay8910_wrapper[tools]", file=sys.stderr)
            raise ImportError("Missing dependencies: sounddevice, numpy")

        if self.stream is None:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                callback=self._callback
            )
            self.stream.start()

    def stop(self) -> None:
        """
        Stops the audio output stream.

        Example:
            ```python
            audio.stop()
            ```
        """
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None