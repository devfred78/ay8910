# AY-3-8910 Standalone Library and Python Wrapper

This project contains a standalone C++ library for the AY-3-8910 sound chip, originally derived from the MAME project, and a Python wrapper to make it accessible from Python scripts.

## Features

- C++ library for AY-3-8910 emulation.
- Python wrapper using `pybind11`.
- Example scripts to generate music and play `.ym` files.

## How to Build

This project uses a modern Python build system with `scikit-build-core` and `cmake`.

1.  **Create and activate a virtual environment:**
    ```sh
    uv venv
    source .venv/bin/activate  # or .venv\Scripts\activate.bat on Windows
    ```

2.  **Install the project in editable mode:**
    ```sh
    uv pip install -e .
    ```

## How to Use

Once installed, you can run the example scripts located in the `scripts/` directory.

For example, to play a YM file:
```sh
python scripts/ym_player.py path/to/your/music.ym
```
