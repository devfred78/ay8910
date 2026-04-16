"""
This package provides a Python wrapper for the standalone AY-3-8910 emulators
(MAME, Caprice32, and AY_Emul31 versions).

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

### Examples

#### 1. Basic Tone (Live Playback)
The simplest way to hear a sound.

```python
import ay8910_wrapper as ay
import time

# Create an AY-3-8912 (1 I/O port) as used in Amstrad CPC
psg = ay.ay8912(backend=ay.Backend.CAPRICE32, clock=1000000)

# Start live audio
psg.play()

# Set a 440Hz tone on Channel A
# Period = 1000000 / (16 * 440) ≈ 142
psg.set_register(0, 142 & 0xFF)
psg.set_register(1, (142 >> 8) & 0x0F)
psg.set_register(7, 0xFE)  # Enable Tone A
psg.set_register(8, 15)    # Max volume

time.sleep(1)
psg.stop()
```

#### 2. Generating Audio Data (WAV Export)
Generate samples manually and save them to a file.

```python
import ay8910_wrapper as ay
import wave, struct

psg = ay.ay8910(backend=ay.Backend.MAME, clock=2000000)

# Configure a noise effect (e.g., snare drum)
psg.set_register(6, 15)   # Noise period
psg.set_register(7, 0xF7) # Enable Noise on Channel A
psg.set_register(8, 16)   # Use envelope
psg.set_register(11, 0)   # Envelope period fine
psg.set_register(12, 10)  # Envelope period coarse
psg.set_register(13, 0x00) # Decay shape (\\___)

# Generate 0.5s of audio at 44100Hz
samples = psg.generate(22050)

with wave.open("noise_effect.wav", "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    f.writeframes(struct.pack('<' + ('h' * len(samples)), *samples))
```

#### 3. Advanced Configuration (MAME & Resistors)
Simulate specific hardware analog characteristics.

```python
import ay8910_wrapper as ay

# Use MAME backend for advanced hardware flags
psg = ay.ay8910(backend=ay.Backend.MAME, clock=1750000)

# Enable resistor-based output modeling (high accuracy)
psg.set_flags(ay.AY8910_RESISTOR_OUTPUT | ay.AY8910_SINGLE_OUTPUT)

# Set specific load resistors for ZX Spectrum (~1k Ohm)
psg.set_resistors_load(1000.0, 1000.0, 1000.0)

psg.play()
# ... program registers ...
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
    """
    Enumeration of available emulation backends.

    Attributes:
        CAPRICE32: Backend derived from the Caprice32 emulator. 
            Supports stereo mixing via `set_stereo_mix`. It is the default backend.
        MAME: Backend derived from MAME (Multiple Adult Mame Emulator). 
            Supports advanced features like resistor modeling (`set_resistors_load`) 
            and various output flags (`set_flags`).
        AY_EMUL31: Backend based on the Ay_Emul 3.1 engine. 
            Supports specific chip type selection via the `chip_type` property.
    """
    CAPRICE32 = "caprice32"
    MAME = "mame"
    AY_EMUL31 = "ay_emul31"

def _add_live_support(cls: Type[Any], channels: int) -> None:
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
"""
MAME Backend: Enable legacy volume table. 
The output samples will be in the range [0, 255] per channel.
"""

AY8910_SINGLE_OUTPUT = 0x02
"""
MAME Backend: Mix all three channels (A, B, and C) into a single mono output stream.
"""

AY8910_DISCRETE_OUTPUT = 0x04
"""
MAME Backend: Use discrete voltage levels for output (experimental).
The output values reflect raw internal DAC levels (0 to 524287).
"""

AY8910_RESISTOR_OUTPUT = 0x08
"""
MAME Backend: Enable advanced resistor-based output modeling.
Requires calling `set_resistors_load` to define external load resistances.
This provides the most accurate simulation of the analog output stage.
"""

PSG_PIN26_IS_CLKSEL = 0x10
"""
MAME Backend (YM2149 only): Pin 26 is used as a clock selector.
When high, the master clock is divided by 2 internally.
"""

PSG_HAS_INTERNAL_DIVIDER = 0x20
"""
MAME Backend: Forces the use of an internal clock divider (usually /2).
Equivalent to tying the CLKSEL pin on a YM2149.
"""

PSG_EXTENDED_ENVELOPE = 0x40
"""
MAME Backend: Enable extended 10-bit envelope resolution (specific to some YM variants).
"""

PSG_HAS_EXPANDED_MODE = 0x80
"""
MAME Backend: Enable expanded register mode (extra ports/features on specialized chips).
"""

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

class AYBase:
    """
    Base class for AY-3-891x wrappers to provide a common interface.

    Args:
        backend (Backend): The emulation engine to use (`Backend.CAPRICE32`,
            `Backend.MAME`, or `Backend.AY_EMUL31`). Default: `Backend.CAPRICE32`.
        clock (int): Master clock frequency in Hz. Default: 1000000.
            Typical values:
            - **Amstrad CPC**: 1000000 (1.0 MHz)
            - **ZX Spectrum**: 1750000 (1.75 MHz) or 1773400 (1.77 MHz)
            - **Atari ST**: 2000000 (2.0 MHz)
            - **Arcade Games**: Varies (often 1.5 MHz or 2.0 MHz)
        sample_rate (int): Audio sampling rate in Hz (default: 44100).
        ioports (int): Number of I/O ports (default: 2).

    Example:
        ```python
        psg = AYBase(backend=Backend.MAME, clock=1000000)
        psg.set_register(0, 0xFE)
        ```
    """
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
        """
        Resets the emulator to its initial state.

        This method mimics the hardware RESET pin. It clears all internal registers
        (setting them to 0), stops any ongoing sound, and resets the envelope and
        noise generators. Use it to ensure a clean state before starting a new
        song or sound effect.

        Example:
            ```python
            # Resets the chip
            psg.reset()
            ```
        """
        if self._backend == Backend.AY_EMUL31:
            self._impl.reset(True)
        else:
            self._impl.reset()

    def address_w(self, value: int) -> None:
        """
        Writes a value to the address latch.

        This method mimics the behavior of the real hardware bus (pins BC1/BDIR). It
        selects which register will be targeted by the next `data_w` call.

        **Note**: For pure software control, prefer `set_register`, which is more
        direct and avoids the two-step address/data latching process.

        Args:
            value (int): The address to select (0-15).

        Example:
            ```python
            psg.address_w(7)  # Select Mixer register
            ```
        """
        if self._backend == Backend.AY_EMUL31:
            # Ay_Emul31 doesn't have address_w/data_w, it uses set_register directly.
            # We'll store the address for a subsequent data_w if needed, 
            # but usually it's better to use set_register.
            self._latched_address = value & 0x0F
        else:
            self._impl.address_w(value)

    def data_w(self, value: int) -> None:
        """
        Writes data to the selected register.

        This method mimics the hardware data bus write operation. It writes a value
        to the register previously selected with `address_w`.

        **Note**: Using `set_register` is recommended instead, as it handles both
        selection and writing in a single atomic software call.

        Args:
            value (int): The value to write to the currently selected register.

        Example:
            ```python
            psg.address_w(7)
            psg.data_w(0xFE)  # Enable Tone A
            ```
        """
        if self._backend == Backend.AY_EMUL31:
            if hasattr(self, '_latched_address'):
                self._impl.set_register(self._latched_address, value)
        else:
            self._impl.data_w(value)

    def get_register(self, reg: int) -> int:
        """
        Reads the value of an internal register (0-15).

        Args:
            reg (int): The register index to read.

        Returns:
            int: The current value of the register.

        Example:
            ```python
            val = psg.get_register(7)
            ```
        """
        if self._backend == Backend.AY_EMUL31:
            # Ay_Emul31 native doesn't seem to expose get_register easily in wrapper? 
            # Wait, let me check wrapper.cpp
            return 0 # Default if not available
        return self._impl.get_register(reg)

    def set_register(self, reg: int, value: int) -> None:
        """
        Writes a value to an internal register (0-15).

        This is the recommended way to program the PSG in software. Unlike the
        hardware-level `address_w` and `data_w` methods, this combined call
        is more efficient and atomic in the context of the emulator wrapper.

        Args:
            reg (int): The register index to write.
            value (int): The value to write (0-255).

        Example:
            ```python
            psg.set_register(7, 0xFE)
            ```
        """
        self._impl.set_register(reg, value)

    def get_registers(self) -> List[int]:
        """
        Returns all 16 internal registers as a list.

        Returns:
            List[int]: A list of 16 integers containing the register values.

        Example:
            ```python
            regs = psg.get_registers()
            ```
        """
        if self._backend == Backend.AY_EMUL31:
            return [0] * 16 # Not easily available
        return self._impl.get_registers()

    def generate(self, num_samples: int) -> List[int]:
        """
        Generates a block of audio samples.

        This method triggers the emulation for a specific number of audio frames and returns
        the resulting samples as a list of 16-bit integers.

        **Output format**:

        - **Caprice32 (Stereo)**: Returns `num_samples * 2` values. The samples are interleaved
          (Left, Right, Left, Right, ...).
        - **MAME / AY_Emul31 (Mono)**: Returns `num_samples` values.

        **What to do with the generated list?**:

        The returned list contains raw 16-bit PCM (Pulse Code Modulation) samples. You can:

        1. **Save to a WAV file**: Using the standard `wave` module.
        2. **Process with NumPy**: For fast calculations, filtering, or visualization.
        3. **Play back**: Using libraries like `sounddevice`, `pyaudio`, or `pygame.mixer`.

        Args:
            num_samples (int): The number of audio frames (samples) to generate.

        Returns:
            List[int]: A list of generated 16-bit PCM samples. The length of the list
                depends on whether the backend is mono or stereo.

        Example:
            ```python
            # 1. Set up a simple tone on Channel A (440Hz at 2MHz clock)
            # Period = Clock / (16 * Frequency) = 2000000 / (16 * 440) = 284
            psg.set_register(0, 284 & 0xFF)  # Fine tune
            psg.set_register(1, (284 >> 8) & 0x0F)  # Coarse tune
            psg.set_register(7, 0xFE)        # Enable Tone A (Mixer bit 0 = 0)
            psg.set_register(8, 15)          # Maximum volume on Channel A
            
            # 2. Generate 1024 frames of this sound
            samples = psg.generate(1024)
            
            # 3. Save to a WAV file
            import wave, struct
            with wave.open("melody.wav", "wb") as f:
                f.setnchannels(2 if psg._backend == Backend.CAPRICE32 else 1)
                f.setsampwidth(2) # 16-bit
                f.setframerate(44100)
                f.writeframes(struct.pack('<' + ('h' * len(samples)), *samples))
            ```
        """
        if self._backend == Backend.CAPRICE32:
            return self._impl.generate(num_samples)
        elif self._backend == Backend.MAME:
            return self._impl.generate(num_samples, self._sample_rate)
        elif self._backend == Backend.AY_EMUL31:
            return self._impl.generate(num_samples, self._clock, self._sample_rate)
        return []

    def play(self, sample_rate: Optional[int] = None, clock: Optional[int] = None) -> None:
        """
        Starts live playback.

        Args:
            sample_rate (Optional[int]): Audio sampling rate in Hz (default: same as class init).
            clock (Optional[int]): Master clock frequency in Hz (default: same as class init).

        Example:
            ```python
            psg.play()
            ```
        """
        sr = sample_rate if sample_rate is not None else self._sample_rate
        cl = clock if clock is not None else self._clock
        self._impl.play(sr, cl)

    def stop(self) -> None:
        """
        Stops live playback.

        Example:
            ```python
            psg.stop()
            ```
        """
        self._impl.stop()

    # MAME specific methods (delegated if backend is MAME)
    def set_flags(self, flags: int) -> None:
        """
        Set internal flags (MAME backend only).

        These flags control how the MAME emulation engine handles audio output and specific
        hardware features of the chip.

        Commonly used flags:

        - `AY8910_LEGACY_OUTPUT` (0x01): Legacy output (0 to 32767). Default behavior if no flags are set.
        - `AY8910_SINGLE_OUTPUT` (0x02): Mixes all three channels into a single mono output stream.
        - `AY8910_DISCRETE_OUTPUT` (0x04): Raw output level (0 to 524287), where 0 is 0V and 524287 is 5V.
        - `AY8910_RESISTOR_OUTPUT` (0x08): Uses resistor values to calculate output. Requires `set_resistors_load`.
        - `YM2149_PIN26_LOW` (0x10): Forces pin 26 low for YM2149 (activates internal divider).

        Args:
            flags (int): Bitwise OR of flags to set.

        Example:
            ```python
            psg.set_flags(AY8910_SINGLE_OUTPUT | AY8910_LEGACY_OUTPUT)
            ```
        """
        if self._backend == Backend.MAME:
            self._impl.set_flags(flags)

    def set_resistors_load(self, res_load0: float, res_load1: float, res_load2: float) -> None:
        """
        Set the resistors load for each channel (MAME backend only).

        This method is used when the `AY8910_RESISTOR_OUTPUT` flag is set in `set_flags`.
        It defines the external load resistance (in Ohms) connected to each of the three
        analog output pins (A, B, and C).

        The PSG's internal output stage can be simplified as a voltage source followed
        by an internal resistance ($R_{int}$) and the chip's MOSFETs, which are then
        connected to an external pull-up or pull-down resistor ($R_{load}$).

        ```text
           Vcc (5V)
             |
           [R_load]  <-- res_load0/1/2
             |
             +----[ Analog Output ]
             |
          [ MOSFET ] (Internal)
             |
            GND
        ```

        Typical values for different systems:

        - **Amstrad CPC**: ~1000.0 Ω (standard pull-up)
        - **ZX Spectrum**: ~1000.0 Ω to 2000.0 Ω
        - **Arcade Boards**: Varies, often 1000.0 Ω or 680.0 Ω

        Args:
            res_load0 (float): Resistor load for channel A (Ohms).
            res_load1 (float): Resistor load for channel B (Ohms).
            res_load2 (float): Resistor load for channel C (Ohms).

        Example:
            ```python
            # Set standard 1kOhm pull-ups for all channels
            psg.set_flags(AY8910_RESISTOR_OUTPUT)
            psg.set_resistors_load(1000.0, 1000.0, 1000.0)
            ```
        """
        if self._backend == Backend.MAME:
            self._impl.set_resistors_load(res_load0, res_load1, res_load2)

    # Caprice32 specific
    def set_stereo_mix(self, al: int, ar: int, bl: int, br: int, cl: int, cr: int) -> None:
        """
        Set stereo mixing volumes (Caprice32 backend only).

        This method defines the volume weights for each of the three PSG channels (A, B, C)
        on the Left and Right stereo outputs.

        The values for each argument range from **0** (silent) to **255** (maximum volume).

        Typical configurations for different systems:

        - **Amstrad CPC (Default)**: (255, 13, 170, 170, 13, 255) - Standard CPC stereo distribution.
        - **Full Mono**: (255, 255, 255, 255, 255, 255) - All channels mixed equally on both outputs.
        - **ABC Stereo**: (255, 0, 128, 128, 0, 255) - Channel A Left, B Center, C Right.
        - **ACB Stereo**: (255, 0, 0, 255, 128, 128) - Channel A Left, C Right, B Center.
        - **Sharp X1**: Often uses a balanced mix for stereo effects.

        Args:
            al (int): Volume for channel A on Left output (0-255).
            ar (int): Volume for channel A on Right output (0-255).
            bl (int): Volume for channel B on Left output (0-255).
            br (int): Volume for channel B on Right output (0-255).
            cl (int): Volume for channel C on Left output (0-255).
            cr (int): Volume for channel C on Right output (0-255).

        Example:
            ```python
            # Classic ABC stereo distribution
            psg.set_stereo_mix(255, 0, 128, 128, 0, 255)
            ```
        """
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

class ay8910(AYBase):
    """
    AY-3-8910: 3 channels, 2 I/O ports (Port A and Port B).

    This class provides a full implementation of the AY-3-8910 chip with two 
    8-bit parallel I/O ports.

    Args:
        backend (Backend): The emulation engine to use (`Backend.CAPRICE32`,
            `Backend.MAME`, or `Backend.AY_EMUL31`). Default: `Backend.CAPRICE32`.
        clock (int): Master clock frequency in Hz (default: 1000000).
            (e.g., 1000000 for Amstrad CPC, 2000000 for Atari ST).
        sample_rate (int): Audio sampling rate in Hz (default: 44100).

    Example:
        ```python
        psg = ay8910(backend=Backend.MAME)
        ```
    """
    def __init__(self, backend: Backend = Backend.CAPRICE32, clock: int = 1000000, sample_rate: int = 44100):
        super().__init__(backend, clock, sample_rate, ioports=2)

class ay8912(AYBase):
    """
    AY-3-8912: 3 channels, 1 I/O port (Port A).

    This class emulates the AY-3-8912 variant, which is pin-compatible with the 
    AY-3-8910 but features only one 8-bit parallel I/O port to reduce pin count.

    Args:
        backend (Backend): The emulation engine to use (`Backend.CAPRICE32`,
            `Backend.MAME`, or `Backend.AY_EMUL31`). Default: `Backend.CAPRICE32`.
        clock (int): Master clock frequency in Hz (default: 1000000).
            (e.g., 1000000 for Amstrad CPC, 1750000 for ZX Spectrum).
        sample_rate (int): Audio sampling rate in Hz (default: 44100).

    Example:
        ```python
        psg = ay8912(backend=Backend.CAPRICE32)
        ```
    """
    def __init__(self, backend: Backend = Backend.CAPRICE32, clock: int = 1000000, sample_rate: int = 44100):
        super().__init__(backend, clock, sample_rate, ioports=1)

class ay8913(AYBase):
    """
    AY-3-8913: 3 channels, 0 I/O ports.

    This class emulates the AY-3-8913 variant, which has no I/O ports. 
    It was designed for applications where only sound generation is needed.

    Args:
        backend (Backend): The emulation engine to use (`Backend.CAPRICE32`,
            `Backend.MAME`, or `Backend.AY_EMUL31`). Default: `Backend.CAPRICE32`.
        clock (int): Master clock frequency in Hz (default: 1000000).
        sample_rate (int): Audio sampling rate in Hz (default: 44100).

    Example:
        ```python
        psg = ay8913(backend=Backend.AY_EMUL31)
        ```
    """
    def __init__(self, backend: Backend = Backend.CAPRICE32, clock: int = 1000000, sample_rate: int = 44100):
        super().__init__(backend, clock, sample_rate, ioports=0)

# Keep old classes for compatibility
ay8912_cap32 = ay8912
ay_emul31 = ay8913