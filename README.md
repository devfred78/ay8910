# AY-3-8910 Standalone Library and Python Wrapper

This project contains a standalone C++ library for the AY-3-8910 sound chip, originally derived from the MAME project, and a Python wrapper to make it accessible from Python scripts.

It allows for the programmatic generation of chiptune-style audio and the playback of `.ym` music files.

## Installation

1.  **Download the Wheel File**: Go to the [Releases](https://github.com/devfrd78/ay8910/releases) page of this project and download the latest `.whl` file for your system (e.g., `ay8910_wrapper-0.1.0-cp314-cp314-win_amd64.whl`).

2.  **Install with `pip`**: Open a terminal and use `pip` (or `uv pip`) to install the downloaded file:
    ```sh
    # Make sure you are in the same directory as the downloaded .whl file
    # or provide the full path to it.
    pip install ay8910_wrapper-0.1.0-cp314-cp314-win_amd64.whl
    ```
    This will also install the necessary dependency (`lhafile`).

## Basic Usage in Python

Here is a simple example of how to use the `ay8910_wrapper` to generate a single tone and save it as a WAV file.

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

## Advanced: Caprice32 (Amstrad CPC) Emulation

The wrapper also includes an alternative implementation based on the **Caprice32** emulator, which uses a different synthesis logic and specific amplitude tables for a more "authentic" CPC sound.

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
