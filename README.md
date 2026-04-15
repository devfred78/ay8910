# AY-3-8910 Standalone Library and Python Wrapper

A Python wrapper for the AY-3-8910 and AY-3-8912 sound chip emulators, featuring real-time audio playback and cycle-accurate synthesis.

> **A Note on this Project's Origin**
>
> This project is primarily the result of a series of experiments using various IA Code Assists for code generation and error handling. Rather than using it on academic examples, it seemed more interesting to apply it to a project that could meet a real practical need.
>
> This, therefore, is the reason for `AY8910`'s existence: you can dissect the code to see how Gemini and Junie (with my guidance) went about building it, or you can ignore all that and just use this library for your own needs!

This project contains a standalone C++ library for the AY-3-8910 sound chip. It features three emulation engines:
- **Caprice32-based (`ay8912_cap32`)**: The **recommended** engine for all new projects. It offers superior accuracy, stereo mixing, and integrated live audio support.
- **Ay_Emul31-based (`ay_emul31`)**: A port of Sergey Bulba's Ay_Emul 3.1. It provides high-quality mono emulation with accurate AY and YM volume tables.
- **MAME-based (`ay8910`)**: Kept primarily for **historical reasons** and legacy compatibility.

It also includes a Python wrapper to make these emulators accessible from Python scripts, allowing for programmatic chiptune generation and `.ym` file playback.

## Quick Start (Live Audio)

```python
import ay8910_wrapper as ay
import time

# Initialize
psg = ay.ay8912_cap32(1000000, 44100)
psg.set_stereo_mix(255, 13, 170, 170, 13, 255)

# Start live playback!
psg.play()

# Set registers - sound changes immediately
psg.set_register(0, 254) # Tone A Fine
psg.set_register(1, 0)   # Tone A Coarse
psg.set_register(7, 0x3E) # Enable Channel A
psg.set_register(8, 15)   # Max volume

time.sleep(1)
psg.stop()
```

```sh
# Play a .ym file using the new live script (defaults to Caprice32)
python scripts\ym_live_player.py PATH\TO\YM_FILE.YM

# Use the MAME or Ay_Emul31 engines
python scripts\ym_live_player.py PATH\TO\YM_FILE.YM --mame
python scripts\ym_live_player.py PATH\TO\YM_FILE.YM --ay_emul31
```

## Installation

You can install the library directly from [PyPI](https://pypi.org/project/ay8910-wrapper/):

```sh
pip install ay8910_wrapper
```

This will automatically install the necessary dependencies (`lhafile`, `numpy`, `sounddevice`).

For developers who want to compile from source or contribute, please refer to the [Contributing Guide](https://devfred78.github.io/ay8910/contribute/).

## Basic Usage in Python (Legacy MAME engine)

> **Note**: This section demonstrates the legacy `ay8910` class. For modern applications, please refer to the **Quick Start** section or the **Caprice32** section below.

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

# 1. Initialize the emulator
clock = 2000000  # 2 MHz, a common clock for this chip
sample_rate = 44100
psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, clock, 1, 0)
psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
psg.start()
psg.reset()

# 2. Program the chip registers
# Enable Tone on Channel A, disable everything else
psg.address_w(7)
psg.data_w(0b00111110)

# Set Channel A frequency to Middle C (261.63 Hz)
period = int(clock / (16 * 261.63))
psg.address_w(0)  # Fine tune
psg.data_w(period & 0xFF)
psg.address_w(1)  # Coarse tune
psg.data_w((period >> 8) & 0x0F)

# Set Channel A volume to max
psg.address_w(8)
psg.data_w(15)

# 3. Generate audio
# Generate 2 seconds of audio
num_samples = sample_rate * 2
samples = psg.generate(num_samples, sample_rate)

# 4. Save the result
write_wav("tone_output.wav", samples, sample_rate)
print("Generated 'tone_output.wav'")

```

For a complete list of all available functions, classes, and constants, please see the [API Reference](https://devfred78.github.io/ay8910/reference/).

## Scripts and Tools

The project includes several scripts for playing chiptunes and running tests. For a detailed description of how to use them, please see the **[Scripts and Tools](https://devfred78.github.io/ay8910/scripts/)** page.

## Recommended: Caprice32 (Amstrad CPC) Emulation

The **Caprice32** engine is the preferred choice for most users. It provides more authentic sound synthesis and advanced features like stereo panning.

```python
# Initialize the Caprice32-style emulator
psg_cpc = ay.ay8912_cap32(clock, sample_rate)
# Set standard CPC stereo mix (Channel A=Left, B=Center, C=Right)
psg_cpc.set_stereo_mix(255, 13, 170, 170, 13, 255)

# Generate stereo audio (interleaved)
stereo_samples = psg_cpc.generate(num_samples)
```

## Contributing Guide

If you wish to contribute to the project or compile it from source, please refer to our **[Contributing Guide](https://devfred78.github.io/ay8910/contribute/)**.

It contains all the necessary information about:
- The development workflow (**GitHub Flow**)
- Using **uv** for environment management
- Compilation and test commands
- Continuous integration processes (GitHub Actions)

## Acknowledgments

This project relies on the incredible work of the following open-source projects:

- **[MAME](https://github.com/mamedev/mame)**: The original AY-3-8910 and YM2149 emulation cores were derived from the MAME project. Their commitment to accuracy and historical preservation is a cornerstone of this library.
- **[Caprice32](https://github.com/ColinPitrat/caprice32)**: The Amstrad CPC-specific PSG emulation logic and amplitude tables were integrated from the Caprice32 project, providing authentic sound for CPC-related audio tasks.
- **[Ay_Emul](https://ay.strangled.net/main_e.htm)**: The `ay_emul31` engine is based on the work of **Sergey Bulba**. It's a port of his original Pascal source code (version 3.1) to C++.
- **[Sergey Bulba](https://ay.strangled.net/elect_e.htm)**: Special thanks for the AY/YM amplitude tables used in the Caprice32 and Ay_Emul31 engines, which are essential for reproducing the characteristic sound of these chips.
- **[Gemini & Junie](https://github.com/google-gemini)**: This project was built with the assistance of AI, demonstrating the potential of human-AI collaboration in software development.

## License
This project is licensed under the MIT License - see the [License](https://devfred78.github.io/ay8910/license/) for details.
The original MAME and Caprice32 cores have their own licensing terms (see [LICENSE_MAME.md](https://github.com/devfred78/ay8910/blob/main/ay8910_cpp_lib/LICENSE_MAME.md)).
