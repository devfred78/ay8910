# Scripts and Tools

The `scripts/` directory contains various utility scripts for playing chiptunes, rendering audio, and running tests.

## Chiptune Players

These scripts allow you to play `.ym` chiptune files using the integrated PSG emulators.

### `ym_player.py`

This is the main player and renderer. It can play `.ym` files live or render them to a `.wav` file.

**Usage:**
```bash
uv run scripts/ym_player.py <input_file.ym> [options]
```

**Options:**

- `-p`, `--play`: Play the file live instead of rendering to WAV.
- `-o <file.wav>`, `--output <file.wav>`: Output WAV file name (default: `output_ym.wav`).
- `--mame`: Use the MAME emulation engine (mono) instead of the Caprice32 engine (stereo).

**Example:**
```bash
# Play a file live using the stereo Caprice32 engine
uv run scripts/ym_player.py music.ym -p

# Render a file to WAV using the MAME engine
uv run scripts/ym_player.py music.ym --mame -o my_render.wav
```

### `ym_live_player.py`

A specialized player that demonstrates the high-level `.play()` API. It focuses on real-time playback and offers support for more emulation engines.

**Usage:**
```bash
uv run scripts/ym_live_player.py <input_file.ym> [options]
```

**Options:**

- `--mame`: Use the MAME engine (mono).
- `--ay_emul31`: Use the Ay_Emul31 engine (mono).
- (Default): Use the Caprice32 engine (stereo).

**Note:** This script requires the `lhafile` library for compressed `.ym` files.

---

## Development and Testing

### `run_local_tests.py`

A comprehensive test runner that executes tests across multiple Python versions using `uv`. It creates temporary virtual environments for each version to ensure isolation.

**Usage:**
```bash
uv run scripts/run_local_tests.py [options]
```

**Options:**
- `--all`: Run tests for all supported Python versions (3.9 to 3.14). If not specified, only the latest version is tested.
- `--fix`: Automatically fix linting issues using `ruff`.

**Example:**
```bash
# Run tests for the latest Python version
uv run scripts/run_local_tests.py

# Run tests for all supported versions and fix linting issues
uv run scripts/run_local_tests.py --all --fix
```

---

## Utility Scripts

The `scripts/` folder also contains technical utilities used during development:

- `analyze_wav.py`: Analyzes audio samples in a WAV file.
- `compare_wav.py`: Compares two WAV files to detect differences.
- `check_samples.py`: Verifies the validity of generated audio samples.
- `strip_wav_metadata.py`: Removes metadata from WAV files for bit-perfect comparison.
