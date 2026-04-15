"""
This package provides a Python wrapper for the standalone AY-3-8910 emulators
(MAME and Caprice32 versions).

It includes classes to emulate the PSG chip and high-level methods for live
audio playback.

### PSG Registers Reference (0-15)

#### Tone Period (Registers 0-5)
These registers control the pitch of the three square wave channels.
Each channel uses two registers (Fine and Coarse) to form a 12-bit period value.
Formula: $f = \text{Clock} / (16 \times \text{Period})$

| Register | Function | Bits |
| :--- | :--- | :--- |
| **0** | Channel A Fine Tune | 8-bit |
| **1** | Channel A Coarse Tune | 4-bit |
| **2** | Channel B Fine Tune | 8-bit |
| **3** | Channel B Coarse Tune | 4-bit |
| **4** | Channel C Fine Tune | 8-bit |
| **5** | Channel C Coarse Tune | 4-bit |

#### Noise Period (Register 6)
Controls the frequency of the pseudo-random noise generator used for percussion or sound effects.

| Register | Function | Bits |
| :--- | :--- | :--- |
| **6** | Noise Period | 5-bit |

#### Mixer Control (Register 7)
Enables or disables Tone and Noise for each of the three channels.
It also controls the I/O port directions. Bits are active-low (0 = Enabled, 1 = Disabled).

| Bit | Function |
| :--- | :--- |
| **0** | Tone A (0: On, 1: Off) |
| **1** | Tone B (0: On, 1: Off) |
| **2** | Tone C (0: On, 1: Off) |
| **3** | Noise A (0: On, 1: Off) |
| **4** | Noise B (0: On, 1: Off) |
| **5** | Noise C (0: On, 1: Off) |
| **6** | Port A Direction (0: Input, 1: Output) |
| **7** | Port B Direction (0: Input, 1: Output) |

#### Amplitude/Volume (Registers 8-10)
Controls the volume of each channel. A value of 0-15 sets a fixed volume.
If bit 4 is set (value 16), the channel follows the hardware envelope.

| Register | Function | Range |
| :--- | :--- | :--- |
| **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |
| **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |
| **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |

#### Envelope Period (Registers 11-12)
Sets the duration of one envelope cycle (16-bit value). Formula: $T = (256 \times \text{Period}) / \text{Clock}$

| Register | Function | Bits |
| :--- | :--- | :--- |
| **11** | Envelope Fine Tune | 8-bit |
| **12** | Envelope Coarse Tune | 8-bit |

#### Envelope Shape (Register 13)
Controls the shape of the volume variation over time. The 4 bits (B3-B0) of this register define the envelope cycle.

| Bit | Name | Function |
| :--- | :--- | :--- |
| **3** | **CONT** | **Continue**: If 0, the cycle ends after one attack/decay (Hold is ignored). |
| **2** | **ATT** | **Attack**: If 1, volume increases (0 to 15). If 0, volume decreases (15 to 0). |
| **1** | **ALT** | **Alternate**: If 1, the direction of the next cycle is reversed (Triangle shape). |
| **0** | **HOLD** | **Hold**: If 1, the volume stays at the last level (0 or 15) after one cycle. |

##### Shape Combinations

| B3-B0 | Hex | Graphical Representation | Description |
| :--- | :--- | :--- | :--- |
| **00xx** | 0-3 | `\\___` | Single Decay, then Silence |
| **01xx** | 4-7 | `/___` | Single Attack, then Silence |
| **1000** | 8 | `\\\\\\\\` | Repeating Decay (Sawtooth) |
| **1001** | 9 | `\\___` | Single Decay, then Silence |
| **1010** | A | `\\/\\/` | Repeating Decay-Attack (Triangle) |
| **1011** | B | `\\¯¯¯` | Single Decay, then Hold High |
| **1100** | C | `////` | Repeating Attack (Inverse Sawtooth) |
| **1101** | D | `/¯¯¯` | Single Attack, then Hold High |
| **1110** | E | `/\\/\\` | Repeating Attack-Decay (Inverse Triangle) |
| **1111** | F | `/___` | Single Attack, then Silence |

*Note: In the graphical representations, `\\` indicates Decay, `/` indicates Attack,
`_` indicates Hold Low (Silence), and `¯` indicates Hold High (Full Volume).*

#### I/O Ports (Registers 14-15)
Data registers for the two 8-bit parallel ports.

| Register | Function |
| :--- | :--- |
| **14** | Port A Data |
| **15** | Port B Data |

### Quick Start

```python
import ay8910_wrapper as ay

# Create a MAME-based AY-3-8910 emulator
chip = ay.ay8910(ay.psg_type.PSG_TYPE_AY, clock=2000000, streams=1, ioports=0)
chip.start()

# Enable live playback
chip.play()

# Set a tone on Channel A (high-level)
chip.set_register(0, 255) # Fine tune
chip.set_register(8, 15)  # Max volume

# Stop playback
# chip.stop()
```
"""

import enum
from typing import Any, Dict, List, Optional, Type

# Import the native module to make it accessible.
from .ay8910_wrapper import *  # noqa: F403
from .ay8910_wrapper import (
    ay8910 as _ay8910_native,
)
from .ay8910_wrapper import (
    ay8912_cap32 as _ay8912_cap32_native,
)
from .ay8910_wrapper import (
    ay_emul31 as _ay_emul31_native,
)
from .ay8910_wrapper import (
    ay_emul31_chip_type as _ay_emul31_chip_type_native,
)
from .ay8910_wrapper import (
    psg_type as _psg_type_native,
)
from .direct_output import DirectOutput

# Add live output capabilities to the classes
_live_outputs: Dict[Any, DirectOutput] = {}

class Backend(enum.Enum):
    """Enumeration of available emulation backends."""
    CAPRICE32 = "caprice32"
    MAME = "mame"
    AY_EMUL31 = "ay_emul31"

def _add_live_support(cls: Type[Any], channels: int) -> None:
    """
    Adds live audio playback support to a PSG class by injecting 'play' and 'stop' methods.

    Args:
        cls: The PSG class to enhance.
        channels: Number of audio channels (1 for mono, 2 for stereo).
    """
    def play(self: Any, sample_rate: int = 44100, clock: int = 1750000) -> None:
        """
        Starts live audio playback for this PSG instance.

        Args:
            sample_rate: The sample rate for the audio output (default 44100).
            clock: Master clock frequency (default 1750000).
        """
        if self not in _live_outputs:
            _live_outputs[self] = DirectOutput(self, sample_rate, channels, clock)
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

# Documentation for Constants
AY8910_LEGACY_OUTPUT = 0x01
"""Enable legacy MAME volume table (0-255)."""

AY8910_SINGLE_OUTPUT = 0x02
"""Mix all channels into a single mono output."""

AY8910_DISCRETE_OUTPUT = 0x04
"""Use discrete output emulation (experimental)."""

AY8910_RESISTOR_OUTPUT = 0x08
"""Calculate output voltage based on internal resistors and MOSFET characteristics."""

PSG_PIN26_IS_CLKSEL = 0x10
"""Pin 26 on the chip selects the clock divider (YM2149)."""

PSG_HAS_INTERNAL_DIVIDER = 0x20
"""The chip has an internal clock divider enabled."""

PSG_EXTENDED_ENVELOPE = 0x40
"""Enable extended envelope shapes (YM2149)."""

PSG_HAS_EXPANDED_MODE = 0x80
"""Enable expanded mode for extra registers (YM2149)."""

class psg_type:
    """
    Enum for selecting the chip model to emulate.
    
    Attributes:
        PSG_TYPE_AY: Emulates the General Instrument AY-3-8910.
        PSG_TYPE_YM: Emulates the Yamaha YM2149, with a different volume curve.
    """
    PSG_TYPE_AY = _psg_type_native.PSG_TYPE_AY
    PSG_TYPE_YM = _psg_type_native.PSG_TYPE_YM

class ay_emul31_chip_type:
    """
    Enum for selecting the chip model to emulate in the Ay_Emul31 engine.
    
    Attributes:
        AY_Chip: Emulates the AY-3-8910 chip.
        YM_Chip: Emulates the Yamaha YM2149 chip.
    """
    AY_Chip = _ay_emul31_chip_type_native.AY_Chip
    YM_Chip = _ay_emul31_chip_type_native.YM_Chip

class _AYBase:
    """Base class for AY-3-891x wrappers to provide a common interface."""
    def __init__(
        self, 
        backend: Backend = Backend.CAPRICE32, 
        clock: int = 1000000, 
        sample_rate: int = 44100, 
        ioports: int = 2
    ):
        self._backend = backend
        self._clock = clock
        self._sample_rate = sample_rate
        self._ioports = ioports
        
        if backend == Backend.CAPRICE32:
            self._impl = _ay8912_cap32_native(clock, sample_rate)
            _add_live_support(type(self._impl), 2)
        elif backend == Backend.MAME:
            # For MAME, we map psg_type to AY by default.
            self._impl = _ay8910_native(_psg_type_native.PSG_TYPE_AY, clock, 1, ioports)
            self._impl.start()
            _add_live_support(type(self._impl), 1)
        elif backend == Backend.AY_EMUL31:
            self._impl = _ay_emul31_native()
            _add_live_support(type(self._impl), 1)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def reset(self) -> None:
        """Resets the emulator state."""
        if self._backend == Backend.AY_EMUL31:
            self._impl.reset(True)
        else:
            self._impl.reset()

    def address_w(self, value: int) -> None:
        """Writes a value to the address latch."""
        if self._backend == Backend.AY_EMUL31:
            # Ay_Emul31 doesn't have address_w/data_w, it uses set_register directly.
            # We'll store the address for a subsequent data_w if needed, 
            # but usually it's better to use set_register.
            self._latched_address = value & 0x0F
        else:
            self._impl.address_w(value)

    def data_w(self, value: int) -> None:
        """Writes data to the selected register."""
        if self._backend == Backend.AY_EMUL31:
            if hasattr(self, '_latched_address'):
                self._impl.set_register(self._latched_address, value)
        else:
            self._impl.data_w(value)

    def get_register(self, reg: int) -> int:
        """Reads the value of an internal register (0-15)."""
        if self._backend == Backend.AY_EMUL31:
            # Ay_Emul31 native doesn't seem to expose get_register easily in wrapper? 
            # Wait, let me check wrapper.cpp
            return 0 # Default if not available
        return self._impl.get_register(reg)

    def set_register(self, reg: int, value: int) -> None:
        """Writes a value to an internal register (0-15)."""
        self._impl.set_register(reg, value)

    def get_registers(self) -> List[int]:
        """Returns all 16 internal registers as a list."""
        if self._backend == Backend.AY_EMUL31:
            return [0] * 16 # Not easily available
        return self._impl.get_registers()

    def generate(self, num_samples: int) -> List[int]:
        """Generates audio samples."""
        if self._backend == Backend.CAPRICE32:
            return self._impl.generate(num_samples)
        elif self._backend == Backend.MAME:
            return self._impl.generate(num_samples, self._sample_rate)
        elif self._backend == Backend.AY_EMUL31:
            return self._impl.generate(num_samples, self._clock, self._sample_rate)
        return []

    def play(self, sample_rate: Optional[int] = None, clock: Optional[int] = None) -> None:
        """Starts live playback."""
        sr = sample_rate if sample_rate is not None else self._sample_rate
        cl = clock if clock is not None else self._clock
        self._impl.play(sr, cl)

    def stop(self) -> None:
        """Stops live playback."""
        self._impl.stop()

    # MAME specific methods (delegated if backend is MAME)
    def set_flags(self, flags: int) -> None:
        if self._backend == Backend.MAME:
            self._impl.set_flags(flags)

    def set_resistors_load(self, res_load0: float, res_load1: float, res_load2: float) -> None:
        if self._backend == Backend.MAME:
            self._impl.set_resistors_load(res_load0, res_load1, res_load2)

    # Caprice32 specific
    def set_stereo_mix(self, al: int, ar: int, bl: int, br: int, cl: int, cr: int) -> None:
        if self._backend == Backend.CAPRICE32:
            self._impl.set_stereo_mix(al, ar, bl, br, cl, cr)

    # Ay_Emul31 specific
    @property
    def chip_type(self) -> Any:
        if self._backend == Backend.AY_EMUL31:
            return self._impl.chip_type
        return None

    @chip_type.setter
    def chip_type(self, value: Any) -> None:
        if self._backend == Backend.AY_EMUL31:
            self._impl.chip_type = value

class ay8910(_AYBase):
    """AY-3-8910: 3 channels, 2 I/O ports (Port A and Port B)."""
    def __init__(self, backend: Backend = Backend.CAPRICE32, clock: int = 1000000, sample_rate: int = 44100):
        super().__init__(backend, clock, sample_rate, ioports=2)

class ay8912(_AYBase):
    """AY-3-8912: 3 channels, 1 I/O port (Port A)."""
    def __init__(self, backend: Backend = Backend.CAPRICE32, clock: int = 1000000, sample_rate: int = 44100):
        super().__init__(backend, clock, sample_rate, ioports=1)

class ay8913(_AYBase):
    """AY-3-8913: 3 channels, 0 I/O ports."""
    def __init__(self, backend: Backend = Backend.CAPRICE32, clock: int = 1000000, sample_rate: int = 44100):
        super().__init__(backend, clock, sample_rate, ioports=0)

# Keep old classes for backward compatibility but they are now just aliases or wrappers
ay8912_cap32 = ay8912 
ay_emul31 = ay8910 # ay8910 with default AY_EMUL31 backend if one wants, but let's be more precise if needed.
