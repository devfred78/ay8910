"""
This package provides a Python wrapper for the standalone AY-3-8910 emulators
(MAME and Caprice32 versions).

It includes classes to emulate the PSG chip and high-level methods for live
audio playback.

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

from typing import Any, Dict, List, Type, Union

# Import the native module to make it accessible.
from .ay8910_wrapper import *  # noqa: F403
from .ay8910_wrapper import (
    ay8910 as _ay8910_native,
    ay8912_cap32 as _ay8912_cap32_native,
    ay_emul31 as _ay_emul31_native,
    psg_type as _psg_type_native,
    ay_emul31_chip_type as _ay_emul31_chip_type_native,
)
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

class ay8910(_ay8910_native):
    """
    Main class for instantiating and controlling an AY-3-8910 emulator based on the MAME implementation.

    The emulated chip features 16 internal registers (0-15) to control 3 square wave channels and a noise generator.

    ### PSG Registers Reference (0-15)

    #### Tone Period (Registers 0-5)
    These registers control the pitch of the three square wave channels. Each channel uses two registers (Fine and Coarse) to form a 12-bit period value.
    Formula: $f = \\text{Clock} / (16 \\times \\text{Period})$

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
    Enables or disables Tone and Noise for each of the three channels. It also controls the I/O port directions. Bits are active-low (0 = Enabled, 1 = Disabled).

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
    Controls the volume of each channel. A value of 0-15 sets a fixed volume. If bit 4 is set (value 16), the channel follows the hardware envelope.

    | Register | Function | Range |
    | :--- | :--- | :--- |
    | **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |
    | **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |
    | **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |

    #### Envelope Period (Registers 11-12)
    Sets the duration of one envelope cycle (16-bit value). Formula: $T = (256 \\times \\text{Period}) / \\text{Clock}$

    | Register | Function | Bits |
    | :--- | :--- | :--- |
    | **11** | Envelope Fine Tune | 8-bit |
    | **12** | Envelope Coarse Tune | 8-bit |

    #### Envelope Shape (Register 13)
    Controls the shape of the volume variation (Attack, Decay, Sustain, Release).

    | Bit 3 | Bit 2 | Bit 1 | Bit 0 | Shape Description |
    | :--- | :--- | :--- | :--- | :--- |
    | **0** | **0** | **x** | **x** | `\\___` (Single Decay, then Silence) |
    | **1** | **0** | **0** | **0** | `\\\\\\\\\\\\\\\\` (Repeating Decay / Sawtooth) |
    | **1** | **0** | **1** | **1** | `/\\|/\\|/\\|` (Repeating Attack / Inverse Sawtooth) |
    | **1** | **1** | **0** | **0** | `/\\/\\/\\` (Triangle) |

    #### I/O Ports (Registers 14-15)
    Data registers for the two 8-bit parallel ports.

    | Register | Function |
    | :--- | :--- |
    | **14** | Port A Data |
    | **15** | Port B Data |

    ### Usage Examples

    **Low-level access (hardware-like):**
    ```python
    chip.address_w(0) # Select Channel A Fine Tone register
    chip.data_w(255)   # Write value
    ```

    **High-level access (direct register write):**
    ```python
    chip.set_register(0, 255) # Directly write to Channel A Fine Tone register
    ```
    """

    def __init__(self, psg_type: psg_type, clock: int, streams: int, ioports: int, feature: int = 0):
        """
        Constructor for the emulator instance.

        Args:
            psg_type (psg_type): The type of sound chip to emulate (AY or YM).
            clock (int): The clock frequency of the chip in Hertz (e.g., 2000000 for 2 MHz).
            streams (int): Number of output audio streams (usually 1).
            ioports (int): Number of I/O ports to emulate (0, 1, or 2).
            feature (int, optional): Advanced chip-specific features. Defaults to 0 (PSG_DEFAULT).
        """
        super().__init__(psg_type, clock, streams, ioports, feature)

    def start(self) -> None:
        """Initializes the emulator core. Must be called before any sound generation."""
        super().start()

    def reset(self) -> None:
        """Resets the state of all registers and internal counters to default values."""
        super().reset()

    def set_flags(self, flags: int) -> None:
        """Sets behavioral flags for the emulation (e.g., AY8910_LEGACY_OUTPUT)."""
        super().set_flags(flags)

    def set_resistors_load(self, res_load0: float, res_load1: float, res_load2: float) -> None:
        """
        Sets the load resistors (in Ohms) for the three audio channels (A, B, C).

        Used when AY8910_RESISTOR_OUTPUT is enabled to calculate the output voltage based on MOSFET characteristics.
        """
        super().set_resistors_load(res_load0, res_load1, res_load2)

    def address_w(self, value: int) -> None:
        """Writes a value to the address latch to select a register (0-15)."""
        super().address_w(value)

    def data_w(self, value: int) -> None:
        """Writes a 8-bit value to the register previously selected by address_w()."""
        super().data_w(value)

    def get_register(self, reg: int) -> int:
        """Reads the value of an internal register (0-31)."""
        return super().get_register(reg)

    def set_register(self, reg: int, value: int) -> None:
        """Writes a value to an internal register (0-31) and updates the emulation state."""
        super().set_register(reg, value)

    def get_registers(self) -> List[int]:
        """Returns all 32 internal registers as a list of integers."""
        return super().get_registers()

    def generate(self, num_samples: int, sample_rate: int) -> List[int]:
        """
        Generates a block of audio samples and returns it as a list of 16-bit signed integers.

        Args:
            num_samples (int): Number of audio samples to generate.
            sample_rate (int): Target sample rate in Hertz (e.g., 44100).

        Returns:
            List[int]: Mono audio samples ranging from -32768 to 32767.
        """
        return super().generate(num_samples, sample_rate)

    def play(self, sample_rate: int = 44100, clock: int = 1750000) -> None:
        """
        Starts live audio playback for this PSG instance.

        Args:
            sample_rate: The sample rate for the audio output (default 44100).
            clock: Master clock frequency (default 1750000).
        """
        pass # Injected by _add_live_support

    def stop(self) -> None:
        """Stops live audio playback for this PSG instance."""
        pass # Injected by _add_live_support

class ay8912_cap32(_ay8912_cap32_native):
    """
    Specialized emulator class based on the Caprice32 (Amstrad CPC) implementation. Natively stereo.

    The emulated chip features 16 internal registers (0-15) to control 3 square wave channels and a noise generator.

    ### PSG Registers Reference (0-15)

    #### Tone Period (Registers 0-5)
    These registers control the pitch of the three square wave channels. Each channel uses two registers (Fine and Coarse) to form a 12-bit period value.
    Formula: $f = \\text{Clock} / (16 \\times \\text{Period})$

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
    Enables or disables Tone and Noise for each of the three channels. It also controls the I/O port directions. Bits are active-low (0 = Enabled, 1 = Disabled).

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
    Controls the volume of each channel. A value of 0-15 sets a fixed volume. If bit 4 is set (value 16), the channel follows the hardware envelope.

    | Register | Function | Range |
    | :--- | :--- | :--- |
    | **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |
    | **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |
    | **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |

    #### Envelope Period (Registers 11-12)
    Sets the duration of one envelope cycle (16-bit value). Formula: $T = (256 \\times \\text{Period}) / \\text{Clock}$

    | Register | Function | Bits |
    | :--- | :--- | :--- |
    | **11** | Envelope Fine Tune | 8-bit |
    | **12** | Envelope Coarse Tune | 8-bit |

    #### Envelope Shape (Register 13)
    Controls the shape of the volume variation (Attack, Decay, Sustain, Release).

    | Bit 3 | Bit 2 | Bit 1 | Bit 0 | Shape Description |
    | :--- | :--- | :--- | :--- | :--- |
    | **0** | **0** | **x** | **x** | `\\___` (Single Decay, then Silence) |
    | **1** | **0** | **0** | **0** | `\\\\\\\\\\\\\\\\` (Repeating Decay / Sawtooth) |
    | **1** | **0** | **1** | **1** | `/\\|/\\|/\\|` (Repeating Attack / Inverse Sawtooth) |
    | **1** | **1** | **0** | **0** | `/\\/\\/\\` (Triangle) |

    #### I/O Ports (Registers 14-15)
    Data registers for the two 8-bit parallel ports.

    | Register | Function |
    | :--- | :--- |
    | **14** | Port A Data |
    | **15** | Port B Data |

    ### Usage Examples

    **Low-level access (hardware-like):**
    ```python
    chip.address_w(0) # Select Channel A Fine Tone register
    chip.data_w(255)   # Write value
    ```

    **High-level access (direct register write):**
    ```python
    chip.set_register(0, 255) # Directly write to Channel A Fine Tone register
    ```
    """

    def __init__(self, clock: int, sample_rate: int):
        """
        Constructor for the Caprice32 PSG instance.

        Args:
            clock (int): Master clock frequency (e.g., 1000000 for 1 MHz).
            sample_rate (int): Target output sample rate (e.g., 44100).
        """
        super().__init__(clock, sample_rate)

    def reset(self) -> None:
        """Resets the emulator state."""
        super().reset()

    def address_w(self, value: int) -> None:
        """Writes a value to the address latch."""
        super().address_w(value)

    def data_w(self, value: int) -> None:
        """Writes data to the selected register."""
        super().data_w(value)

    def get_register(self, reg: int) -> int:
        """Reads the value of an internal register (0-15)."""
        return super().get_register(reg)

    def set_register(self, reg: int, value: int) -> None:
        """Writes a value to an internal register (0-15) and updates the emulation state."""
        super().set_register(reg, value)

    def get_registers(self) -> List[int]:
        """Returns all 16 internal registers as a list."""
        return super().get_registers()

    def set_stereo_mix(self, al: int, ar: int, bl: int, br: int, cl: int, cr: int) -> None:
        """
        Sets the stereo weights (panning) for the three PSG channels (A, B, C).

        Args:
            al, ar (int): Left and Right weights for Channel A (0-255).
            bl, br (int): Left and Right weights for Channel B (0-255).
            cl, cr (int): Left and Right weights for Channel C (0-255).
        """
        super().set_stereo_mix(al, ar, bl, br, cl, cr)

    def generate(self, num_samples: int) -> List[int]:
        """
        Generates interleaved stereo audio samples.

        Args:
            num_samples (int): Number of samples to generate.

        Returns:
            List[int]: A list of num_samples * 2 integers (alternating Left and Right).
        """
        return super().generate(num_samples)

    def play(self, sample_rate: int = 44100, clock: int = 1750000) -> None:
        """
        Starts live audio playback for this PSG instance.

        Args:
            sample_rate: The sample rate for the audio output (default 44100).
            clock: Master clock frequency (default 1750000).
        """
        pass # Injected by _add_live_support

    def stop(self) -> None:
        """Stops live audio playback for this PSG instance."""
        pass # Injected by _add_live_support

class ay_emul31(_ay_emul31_native):
    """
    Emulator class based on Sergey Bulba's Ay_Emul29+ (version 3.1) implementation.

    This version is a port of the original Pascal source code to C++, providing a mono emulation with support for both AY and YM volume tables.

    ### PSG Registers Reference (0-15)

    #### Tone Period (Registers 0-5)
    These registers control the pitch of the three square wave channels.

    | Register | Function | Bits |
    | :--- | :--- | :--- |
    | **0** | Channel A Fine Tune | 8-bit |
    | **1** | Channel A Coarse Tune | 4-bit |
    | **2** | Channel B Fine Tune | 8-bit |
    | **3** | Channel B Coarse Tune | 4-bit |
    | **4** | Channel C Fine Tune | 8-bit |
    | **5** | Channel C Coarse Tune | 4-bit |

    #### Noise Period (Register 6)
    Controls the frequency of the pseudo-random noise generator.

    | Register | Function | Bits |
    | :--- | :--- | :--- |
    | **6** | Noise Period | 5-bit |

    #### Mixer Control (Register 7)
    Enables or disables Tone and Noise for each of the three channels. Bits are active-low.

    | Bit | Function |
    | :--- | :--- |
    | **0** | Tone A (0: On, 1: Off) |
    | **1** | Tone B (0: On, 1: Off) |
    | **2** | Tone C (0: On, 1: Off) |
    | **3** | Noise A (0: On, 1: Off) |
    | **4** | Noise B (0: On, 1: Off) |
    | **5** | Noise C (0: On, 1: Off) |

    #### Amplitude/Volume (Registers 8-10)
    Controls the volume of each channel. A value of 0-15 sets a fixed volume. If bit 4 is set (value 16), the channel follows the hardware envelope.

    | Register | Function | Range |
    | :--- | :--- | :--- |
    | **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |
    | **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |
    | **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |

    #### Envelope Period (Registers 11-12)
    Sets the duration of one envelope cycle (16-bit value).

    | Register | Function | Bits |
    | :--- | :--- | :--- |
    | **11** | Envelope Fine Tune | 8-bit |
    | **12** | Envelope Coarse Tune | 8-bit |

    #### Envelope Shape (Register 13)
    Controls the shape of the volume variation.

    | Bit 3 | Bit 2 | Bit 1 | Bit 0 | Shape Description |
    | :--- | :--- | :--- | :--- | :--- |
    | **0** | **0** | **x** | **x** | `\\___` (Single Decay, then Silence) |
    | **1** | **0** | **0** | **0** | `\\\\\\\\\\\\\\\\` (Repeating Decay / Sawtooth) |
    | **1** | **0** | **1** | **1** | `/\\|/\\|/\\|` (Repeating Attack / Inverse Sawtooth) |
    | **1** | **1** | **0** | **0** | `/\\/\\/\\` (Triangle) |

    ### Usage Examples

    ```python
    chip = ay.ay_emul31()
    chip.chip_type = ay.ay_emul31_chip_type.YM_Chip
    chip.set_register(0, 255) # Set Tone A
    ```
    """
    
    @property
    def chip_type(self) -> ay_emul31_chip_type:
        """The type of chip to emulate (AY or YM)."""
        return super().chip_type
        
    @chip_type.setter
    def chip_type(self, value: ay_emul31_chip_type) -> None:
        super().chip_type = value

    def __init__(self):
        """Constructor for the Ay_Emul31 emulator instance."""
        super().__init__()

    def reset(self, zeroregs: bool = True) -> None:
        """
        Resets the emulator state.

        Args:
            zeroregs (bool): If true, all registers are cleared to zero (default: true).
        """
        super().reset(zeroregs)

    def set_register(self, reg: int, value: int) -> None:
        """
        Writes a value to an internal register (0-15).

        Args:
            reg (int): The register index (0-15).
            value (int): The 8-bit value to write.
        """
        super().set_register(reg, value)

    def generate(self, num_samples: int, clock: int, sample_rate: int) -> List[int]:
        """
        Generates a block of mono audio samples.

        Args:
            num_samples (int): Number of audio samples to generate.
            clock (int): Master clock frequency in Hz.
            sample_rate (int): Target output sample rate in Hz.

        Returns:
            List[int]: Mono audio samples ranging from -32768 to 32767.
        """
        return super().generate(num_samples, clock, sample_rate)

    def play(self, sample_rate: int = 44100, clock: int = 1750000) -> None:
        """
        Starts live audio playback for this PSG instance.

        Args:
            sample_rate: The sample rate for the audio output (default 44100).
            clock: Master clock frequency (default 1750000).
        """
        pass # Injected by _add_live_support

    def stop(self) -> None:
        """Stops live audio playback for this PSG instance."""
        pass # Injected by _add_live_support

# Access names through the module dictionary since they are imported via *
# Note: we use the local classes defined above
_add_live_support(ay8910, 1)
_add_live_support(ay8912_cap32, 2)
_add_live_support(ay_emul31, 1)
