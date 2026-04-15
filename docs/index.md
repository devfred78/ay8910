# AY-3-8910 Standalone Library and Python Wrapper

A Python wrapper for the AY-3-8910 and AY-3-8912 sound chip emulators, featuring real-time audio playback and cycle-accurate synthesis.

> **A Note on this Project's Origin**
>
> This project is primarily the result of a series of experiments using various IA Code Assists for code generation and error handling. Rather than using it on academic examples, it seemed more interesting to apply it to a project that could meet a real practical need.
>
> This, therefore, is the reason for `AY8910`'s existence: you can dissect the code to see how Gemini and Junie (with my guidance) went about building it, or you can ignore all that and just use this library for your own needs!

This project contains a standalone C++ library for the AY-3-8910 sound chip. It now features a unified API with three main classes:

- **`ay8910`**: Emulates the 3-channel PSG with 2 I/O ports.
- **`ay8912`**: Emulates the 3-channel PSG with 1 I/O port.
- **`ay8913`**: Emulates the 3-channel PSG with 0 I/O ports.

At instantiation, you can choose between three emulation backends:

- **`CAPRICE32` (default)**: The **recommended** engine. High accuracy, stereo mixing, and integrated live audio.
- **`MAME`**: Based on the MAME implementation.
- **`AY_EMUL31`**: A port of Sergey Bulba's Ay_Emul 3.1.

## Quick Start (Live Audio)

```python
import ay8910_wrapper as ay
import time

# Initialize an AY-3-8912 using the Caprice32 backend (default)
psg = ay.ay8912(clock=1000000, sample_rate=44100)
psg.set_stereo_mix(255, 13, 170, 170, 13, 255)

# Start live playback!
psg.play()

# Set registers - sound changes immediately
psg.set_register(0, 254) # Tone A Fine
psg.set_register(1, 0)   # Tone A Coarse
psg.set_register(7, 0x3E) # Enable Tone A, disable others
psg.set_register(8, 15)   # Max volume

time.sleep(1)
psg.stop()
```

```sh
# Play a .ym file using the live player (defaults to ay8910 + Caprice32)
python scripts\ym_live_player.py PATH\TO\YM_FILE.YM

# Explicitly choose a backend
python scripts\ym_live_player.py PATH\TO\YM_FILE.YM --backend MAME
python scripts\ym_live_player.py PATH\TO\YM_FILE.YM --backend AY_EMUL31
```

## Installation

You can install the library directly from [PyPI](https://pypi.org/project/ay8910-wrapper/):

```sh
pip install ay8910_wrapper
```

This will automatically install the necessary dependencies (`lhafile`, `numpy`, `sounddevice`).

For developers who want to compile from source or contribute, please refer to the [Contributing Guide](contribute.md).

## Basic Usage in Python

```python
import ay8910_wrapper as ay
import wave
import struct

# Helper to write WAV files
def write_wav(filename, samples, sample_rate):
    with wave.open(filename, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        packed_samples = struct.pack('<' + 'h' * len(samples), *samples)
        f.writeframes(packed_samples)

# --- Main Program ---

# 1. Initialize the emulator using the MAME backend
clock = 2000000  # 2 MHz
sample_rate = 44100
psg = ay.ay8910(backend=ay.Backend.MAME, clock=clock, sample_rate=sample_rate)
psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
psg.reset()

# 2. Program the chip registers
# Enable Tone on Channel A, disable everything else
psg.set_register(7, 0b00111110)

# Set Channel A frequency to Middle C (261.63 Hz)
period = int(clock / (16 * 261.63))
psg.set_register(0, period & 0xFF)         # Fine tune
psg.set_register(1, (period >> 8) & 0x0F)  # Coarse tune

# Set Channel A volume to max
psg.set_register(8, 15)

# 3. Generate audio
# Generate 2 seconds of audio
num_samples = sample_rate * 2
samples = psg.generate(num_samples)

# 4. Save the result
write_wav("tone_output.wav", samples, sample_rate)
print("Generated 'tone_output.wav'")

```

For a complete list of all available functions, classes, and constants, please see the [API Reference](reference.md).

## Unified Architecture

The new architecture allows you to choose the exact chip model and the emulation engine that best fits your needs.

```python
# Initialize an AY-3-8910 (2 I/O ports) using the Caprice32 backend
psg_8910 = ay.ay8910(backend=ay.Backend.CAPRICE32)

# Initialize an AY-3-8912 (1 I/O port) using the MAME backend
psg_8912 = ay.ay8912(backend=ay.Backend.MAME)

# Initialize an AY-3-8913 (0 I/O ports) using the Ay_Emul31 backend
psg_8913 = ay.ay8913(backend=ay.Backend.AY_EMUL31)
```

## Contributing Guide

If you wish to contribute to the project or compile it from source, please refer to our **[Contributing Guide](contribute.md)**.

It contains all the necessary information about:

- The development workflow (**GitHub Flow**)
- Using **uv** for environment management
- Compilation and test commands
- Continuous integration processes (GitHub Actions)

## Acknowledgments

This project relies on the incredible work of the following open-source projects:

- **[MAME](https://github.com/mamedev/mame)**: The original AY-3-8910 and YM2149 emulation cores were derived from the MAME project. Their commitment to accuracy and historical preservation is a cornerstone of this library.
- **[Caprice32](https://github.com/ColinPitrat/caprice32)**: The Amstrad CPC-specific PSG emulation logic and amplitude tables were integrated from the Caprice32 project, providing authentic sound for CPC-related audio tasks.
- **[Sergey Bulba](https://ay.strangled.net/elect_e.htm)**: Special thanks for the AY/YM amplitude tables used in the Caprice32 and Ay_Emul31 engines, which are essential for reproducing the characteristic sound of these chips.
- **[Ay_Emul](https://ay.strangled.net/main_e.htm)**: The `ay_emul31` engine is based on the work of **Sergey Bulba**. It's a port of his original Pascal source code (version 3.1) to C++.
- **[Gemini & Junie](https://github.com/google-gemini)**: This project was built with the assistance of AI, demonstrating the potential of human-AI collaboration in software development.

## License
This project is licensed under the MIT License - see the [LICENSE.md](license.md) file for details.
The original MAME and Caprice32 cores have their own licensing terms (see [LICENSE_MAME.md](https://github.com/devfred78/ay8910/blob/main/ay8910_cpp_lib/LICENSE_MAME.md)).
