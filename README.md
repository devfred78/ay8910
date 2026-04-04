# AY-3-8910 Standalone Library and Python Wrapper

A Python wrapper for the AY-3-8910 and AY-3-8912 sound chip emulators, featuring real-time audio playback and cycle-accurate synthesis.

> **A Note on this Project's Origin**
>
> This project is primarily the result of a series of experiments using various IA Code Assists for code generation and error handling. Rather than using it on academic examples, it seemed more interesting to apply it to a project that could meet a real practical need.
>
> This, therefore, is the reason for `AY8910`'s existence: you can dissect the code to see how Gemini and Junie (with my guidance) went about building it, or you can ignore all that and just use this library for your own needs!

This project contains a standalone C++ library for the AY-3-8910 sound chip. It features two emulation engines:
- **Caprice32-based (`ay8912_cap32`)**: The **recommended** engine for all new projects. It offers superior accuracy, stereo mixing, and integrated live audio support.
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
# Play a .ym file using the new live script
python scripts\ym_live_player.py PATH\TO\YM_FILE.YM
```

## Installation

1.  **Download the Wheel File**: Go to the [Releases](https://github.com/devfrd78/ay8910/releases) page of this project and download the latest `.whl` file for your system (e.g., `ay8910_wrapper-0.1.0-cp314-cp314-win_amd64.whl`).

2.  **Install with `pip`**: Open a terminal and use `pip` (or `uv pip`) to install the downloaded file:
    ```sh
    # Make sure you are in the same directory as the downloaded .whl file
    # or provide the full path to it.
    pip install ay8910_wrapper-0.1.0-cp314-cp314-win_amd64.whl
    ```
    This will also install the necessary dependency (`lhafile`).

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

For a complete list of all available functions, classes, and constants, please see the [API Reference](REFERENCE.md).

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

## For Developers: Building from Source

If you want to modify the code, you need to build the project from source.

1.  **Clone the repository and create a virtual environment:**
    ```sh
    git clone https://github.com/devfred78/ay8910.git
    cd your-repo
    uv venv
    # On Windows PowerShell
    .venv\Scripts\activate
    # On Linux/macOS/MSYS2
    # source .venv/bin/activate
    ```

2.  **Install in editable mode:**
    This command will compile the C++ core and make the Python wrapper available in your environment.
    ```sh
    uv pip install -e .
    ```
3.  **Build the wheel for distribution:**
    ```sh
    uv build
    ```
    The final `.whl` file will be in the `dist/` directory.

## Running Tests

The project includes a suite of unit tests to verify the functionality of the wrapper and the emulation core.

1.  **Install test dependencies:**
    The tests require `numpy`.
    ```sh
    uv pip install numpy
    ```

2.  **Run the tests:**
    From the root directory of the project, run the `unittest` discovery command:
    ```sh
    uv run python -m unittest discover -s tests
    ```
    This will find and execute all tests in the `tests/` directory.

## Acknowledgments

This project relies on the incredible work of the following open-source projects:

- **[MAME](https://github.com/mamedev/mame)**: The original AY-3-8910 and YM2149 emulation cores were derived from the MAME project. Their commitment to accuracy and historical preservation is a cornerstone of this library.
- **[Caprice32](https://github.com/ColinPitrat/caprice32)**: The Amstrad CPC-specific PSG emulation logic and amplitude tables were integrated from the Caprice32 project, providing authentic sound for CPC-related audio tasks.
- **[Sergey Bulba](http://bulba.at.gz.ru/)**: Special thanks for the AY/YM amplitude tables used in the Caprice32 engine, which are essential for reproducing the characteristic sound of these chips.
