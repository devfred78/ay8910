# `ay8910_wrapper` API Reference

This document provides a detailed reference for the functions, classes, and constants available in the `ay8910_wrapper` Python module.

---

## The `ay8910` Class (MAME-based)

This is the main class used to instantiate and control an AY-3-8910 emulator, based on the MAME implementation.

### Usage Example

```python
import ay8910_wrapper as ay

# Initialize a YM2149 chip at 2MHz
chip = ay.ay8910(ay.psg_type.PSG_TYPE_YM, 2000000, 1, 0)
chip.start()
chip.set_flags(ay.AY8910_LEGACY_OUTPUT)

# Play a middle A (440Hz) on Channel A
# Period = Clock / (16 * Frequency) = 2000000 / (16 * 440) ≈ 284
period = 284
chip.address_w(0) # Channel A Fine Tone
chip.data_w(period & 0xFF)
chip.address_w(1) # Channel A Coarse Tone
chip.data_w((period >> 8) & 0x0F)

chip.address_w(8) # Channel A Amplitude
chip.data_w(15)   # Max volume (non-envelope)

# Generate 1 second of audio at 44.1kHz
audio = chip.generate(44100, 44100)

# Save to a WAV file
import wave
import struct

with wave.open("output_mame.wav", "w") as wav_file:
    # 1 channel (mono), 2 bytes per sample (16-bit), 44100Hz
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(44100)
    
    # Pack the list of integers into binary 16-bit signed little-endian
    data = struct.pack('<' + ('h' * len(audio)), *audio)
    wav_file.writeframes(data)
```

### `ay8910(psg_type, clock, streams, ioports, feature)`

The constructor for the emulator instance.

-   **`psg_type` (`ay.psg_type`)**: The type of sound chip to emulate. See the `psg_type` enum below.
-   **`clock` (`int`)**: The clock frequency of the chip in Hertz (e.g., `2000000` for 2 MHz).
-   **`streams` (`int`)**: The number of output audio streams. For a standard mono or stereo mix, this should be `1`.
-   **`ioports` (`int`)**: The number of I/O ports to emulate (0, 1, or 2). For sound generation, this can be `0`.
-   **`feature` (`int`, optional)**: Advanced chip-specific features. Defaults to `ay.psg_type.PSG_DEFAULT`.

### Methods

#### `.start()`

Initializes the emulator core. This must be called before any other sound generation methods.

#### `.reset()`

Resets the state of all registers and internal counters of the emulated chip to their default values.

#### `.set_flags(flags)`

Sets behavioral flags for the emulation.

-   **`flags` (`int`)**: A combination of one or more flag constants (see **Flag Constants** below). The most common is `ay.AY8910_LEGACY_OUTPUT` for compatibility with `.ym` files.

#### `.address_w(value)`

Writes a value to the address latch to select a register.

-   **`value` (`int`)**: The 8-bit address of the register to select (0-15).

#### `.data_w(value)`

Writes a value to the register previously selected by `.address_w()`.

-   **`value` (`int`)**: The 8-bit value to write to the selected register.

#### `.get_register(reg)`

Directly reads the value of an internal register.

-   **`reg` (`int`)**: The register index (0-31).
-   **Returns**: `int` - The 8-bit register value.

#### `.set_register(reg, value)`

Directly writes a value to an internal register and updates the internal emulation state (e.g., period, volume).

-   **`reg` (`int`)**: The register index (0-31).
-   **`value` (`int`)**: The 8-bit value to write.

#### `.get_registers()`

Returns all internal registers as a list.

-   **Returns**: `List[int]` - A list of 32 values representing the current state of the registers.

#### `.generate(num_samples, sample_rate)`

Generates a block of audio and returns it as a list of 16-bit signed integers.

-   **`num_samples` (`int`)**: The number of audio samples to generate.
-   **`sample_rate` (`int`)**: The target sample rate in Hertz (e.g., `44100`).
-   **Returns**: `List[int]` - A list of mono audio samples ranging from -32768 to 32767.

---

## Enums and Constants

### `psg_type`

An enumeration for selecting the chip model to emulate.

-   **`ay.psg_type.PSG_TYPE_AY`**: Emulates the AY-3-8910. This is the most common type.
-   **`ay.psg_type.PSG_TYPE_YM`**: Emulates the YM2149, which has a slightly different volume curve.

### Flag Constants

These constants can be used with the `.set_flags()` method.

-   **`ay.AY8910_LEGACY_OUTPUT`**: Enables a legacy mixing mode that is compatible with most `.ym` file players. When using this, the output of the 3 channels is summed, so the volume may need to be scaled down.
-   **`ay.AY8910_SINGLE_OUTPUT`**: Simulates the cross-channel mixing that occurs when the hardware outputs are tied together.
-   **`ay.AY8910_DISCRETE_OUTPUT`**: A mode for discrete mixing stages.
-   **`ay.AY8910_RESISTOR_OUTPUT`**: Causes the driver to output resistor values instead of audio samples, intended for netlist simulation.

---

## PSG Registers Reference (0-15)

Both engines support the standard AY-3-8910 register set. Below is a detailed description of each register and how to use them.

### Tone Period (Registers 0-5)

These registers control the pitch of the three square wave channels. Each channel uses two registers (Fine and Coarse) to form a 12-bit period value.
Formula: $f = \frac{Clock}{16 \times \text{Period}}$

| Register | Function | Bits |
| :--- | :--- | :--- |
| **0** | Channel A Fine Tune | 8-bit |
| **1** | Channel A Coarse Tune | 4-bit |
| **2** | Channel B Fine Tune | 8-bit |
| **3** | Channel B Coarse Tune | 4-bit |
| **4** | Channel C Fine Tune | 8-bit |
| **5** | Channel C Coarse Tune | 4-bit |

**Practical Example:**
```python
# Set Channel A to 440Hz (assuming 1MHz clock)
period = 1000000 // (16 * 440) # ≈ 142
chip.set_register(0, period & 0xFF)         # Fine: 142
chip.set_register(1, (period >> 8) & 0x0F)  # Coarse: 0
```

### Noise Period (Register 6)

Controls the frequency of the pseudo-random noise generator used for percussion or sound effects.

| Register | Function | Bits |
| :--- | :--- | :--- |
| **6** | Noise Period | 5-bit |

**Practical Example:**
```python
# Low frequency noise (deep rumble)
chip.set_register(6, 31) 
# High frequency noise (hissing)
chip.set_register(6, 1)
```

### Mixer Control (Register 7)

Enables or disables Tone and Noise for each of the three channels. It also controls the I/O port directions.
**Note:** Bits are active-low (0 = Enabled, 1 = Disabled).

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

**Practical Example:**
```python
# Enable Tone A and Noise C, disable everything else
# Binary: 11011110 -> Hex: 0xDE
chip.set_register(7, 0xDE)
```

### Amplitude/Volume (Registers 8-10)

Controls the volume of each channel. A value of 0-15 sets a fixed volume. If bit 4 is set (value 16), the channel follows the hardware envelope.

| Register | Function | Range |
| :--- | :--- | :--- |
| **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |
| **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |
| **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |

**Practical Example:**
```python
chip.set_register(8, 15)  # Max fixed volume for Channel A
chip.set_register(9, 16)  # Channel B uses the Envelope
```

### Envelope Period (Registers 11-12)

Sets the duration of one envelope cycle (16-bit value).
Formula: $T = \frac{256 \times \text{Period}}{Clock}$

| Register | Function | Bits |
| :--- | :--- | :--- |
| **11** | Envelope Fine Tune | 8-bit |
| **12** | Envelope Coarse Tune | 8-bit |

**Practical Example:**
```python
# Set a long 1-second envelope cycle (1MHz clock)
period = 1000000 // 256 # ≈ 3906
chip.set_register(11, period & 0xFF)
chip.set_register(12, (period >> 8) & 0xFF)
```

### Envelope Shape (Register 13)

Controls the shape of the volume variation (Attack, Decay, Sustain, Release).

| Bit 3 | Bit 2 | Bit 1 | Bit 0 | Shape Description |
| :--- | :--- | :--- | :--- | :--- |
| **0** | **0** | **x** | **x** | \___ (Single Decay, then Silence) |
| **1** | **0** | **0** | **0** | \\\\\\\ (Repeating Decay / Sawtooth) |
| **1** | **0** | **1** | **1** | /|/|/| (Repeating Attack / Inverse Sawtooth) |
| **1** | **1** | **0** | **0** | /\/\/\ (Triangle) |

**Practical Example:**
```python
# Set a Triangle shape
chip.set_register(13, 0x0C)
```

### I/O Ports (Registers 14-15)

Data registers for the two 8-bit parallel ports.

| Register | Function |
| :--- | :--- |
| **14** | Port A Data |
| **15** | Port B Data |

**Practical Example:**
```python
# Set Port A as output (in Register 7) and write a value
chip.set_register(7, 0x7F) # Bit 6 = 1
chip.set_register(14, 0xAA)
```

---

---

## The `ay8912_cap32` Class (Caprice32-based)

A specialized emulator class based on the **Caprice32** (Amstrad CPC) implementation. It uses different synthesis logic and specific amplitude tables (`Amplitudes_AY` by Sergey Bulba). It is natively **stereo**.

### Usage Example

```python
import ay8910_wrapper as ay

# Initialize a CPC-style PSG at 1MHz, targeting 44.1kHz output
chip = ay.ay8912_cap32(1000000, 44100)

# Set Amstrad CPC standard stereo mix (ABC)
# Weights are 0-255 for (Left, Right)
chip.set_stereo_mix(255, 13,   # Channel A (Mostly Left)
                    170, 170,  # Channel B (Center)
                    13, 255)   # Channel C (Mostly Right)

# Play 440Hz on Channel A
period = 1000000 // (16 * 440) # ≈ 142
chip.address_w(0)
chip.data_w(period & 0xFF)
chip.address_w(1)
chip.data_w((period >> 8) & 0x0F)
chip.address_w(8)
chip.data_w(15)

# Generate 1 second of stereo audio
# Returns 44100 * 2 = 88200 samples
audio = chip.generate(44100)

# Save to a WAV file
import wave
import struct

with wave.open("output_cap32.wav", "w") as wav_file:
    # 2 channels (stereo), 2 bytes per sample (16-bit), 44100Hz
    wav_file.setnchannels(2)
    wav_file.setsampwidth(2)
    wav_file.setframerate(44100)
    
    # Pack the list of integers into binary 16-bit signed little-endian
    # audio is already interleaved [L0, R0, L1, R1, ...]
    data = struct.pack('<' + ('h' * len(audio)), *audio)
    wav_file.writeframes(data)

# audio[0] is Left sample 0
# audio[1] is Right sample 0
```

### `ay8912_cap32(clock, sample_rate)`

-   **`clock` (`int`)**: The master clock frequency (e.g., `1000000` for 1 MHz).
-   **`sample_rate` (`int`)**: The target output sample rate (e.g., `44100`).

### Methods

#### `.reset()`
Resets the emulator state.

#### `.address_w(value)`
Writes to the address latch.

#### `.data_w(value)`
Writes data to the selected register.

#### `.get_register(reg)`

Directly reads the value of an internal register.

-   **`reg` (`int`)**: The register index (0-15).
-   **Returns**: `int` - The 8-bit register value.

#### `.set_register(reg, value)`

Directly writes a value to an internal register and updates the internal emulation state (e.g., period, volume).

-   **`reg` (`int`)**: The register index (0-15).
-   **`value` (`int`)**: The 8-bit value to write.

#### `.get_registers()`

Returns all 16 internal registers as a list.

-   **Returns**: `List[int]` - A list of 16 values.

#### `.set_stereo_mix(al, ar, bl, br, cl, cr)`

Sets the stereo weights (panning) for the three PSG channels.

-   **`al`, `ar` (`int`)**: Left and Right weights for Channel A (0-255).
-   **`bl`, `br` (`int`)**: Left and Right weights for Channel B (0-255).
-   **`cl`, `cr` (`int`)**: Left and Right weights for Channel C (0-255).

#### `.generate(num_samples)`

Generates interleaved stereo audio samples.

-   **`num_samples` (`int`)**: The number of samples to generate.
-   **Returns**: `List[int]` - A list of `num_samples * 2` integers (alternating Left and Right channels).