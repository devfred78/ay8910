"""
This package provides a Python wrapper for the standalone AY-3-8910 emulators
(MAME and Caprice32 versions).

It includes classes to emulate the PSG chip and high-level methods for live
audio playback.
"""

from typing import Any, Dict, Type

# Import the native module to make it accessible.
from .ay8910_wrapper import *  # noqa: F403
from .direct_output import DirectOutput

# Add live output capabilities to the classes
_live_outputs: Dict[Any, DirectOutput] = {}

def _add_live_support(cls: Type[Any], channels: int) -> None:
    """
    Adds live audio playback support to a PSG class by injecting 'play' and 'stop' methods.

    Args:
        cls: The PSG class to enhance (e.g., ay8910 or ay8912_cap32).
        channels: Number of audio channels (1 for mono, 2 for stereo).
    """
    def play(self: Any, sample_rate: int = 44100) -> None:
        """
        Starts live audio playback for this PSG instance.

        Args:
            sample_rate: The sample rate for the audio output (default 44100).
        """
        if self not in _live_outputs:
            _live_outputs[self] = DirectOutput(self, sample_rate, channels)
            _live_outputs[self].start()
            
    def stop(self: Any) -> None:
        """
        Stops live audio playback for this PSG instance.
        """
        if self in _live_outputs:
            _live_outputs[self].stop()
            del _live_outputs[self]

    cls.play = play  # type: ignore
    cls.stop = stop  # type: ignore

# Access names through the module dictionary since they are imported via *
_add_live_support(globals()['ay8910'], 1)
_add_live_support(globals()['ay8912_cap32'], 2)
