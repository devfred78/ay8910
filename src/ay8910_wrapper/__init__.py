# This file makes the directory a Python package.

from typing import Any, Dict, Type

# Import the native module to make it accessible.
from .ay8910_wrapper import *  # noqa: F403
from .direct_output import DirectOutput

# Add live output capabilities to the classes
_live_outputs: Dict[Any, DirectOutput] = {}

def _add_live_support(cls: Type[Any], channels: int) -> None:
    def play(self: Any, sample_rate: int = 44100) -> None:
        if self not in _live_outputs:
            _live_outputs[self] = DirectOutput(self, sample_rate, channels)
            _live_outputs[self].start()
            
    def stop(self: Any) -> None:
        if self in _live_outputs:
            _live_outputs[self].stop()
            del _live_outputs[self]

    cls.play = play  # type: ignore
    cls.stop = stop  # type: ignore

# Access names through the module dictionary since they are imported via *
_add_live_support(globals()['ay8910'], 1)
_add_live_support(globals()['ay8912_cap32'], 2)
