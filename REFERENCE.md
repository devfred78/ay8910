# `ay8910_wrapper` API Reference

This document provides a detailed reference for the functions, classes, and constants available in the `ay8910_wrapper` Python module.

---

## The `ay8910` Class

This is the main class used to instantiate and control an AY-3-8910 emulator.

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

#### `.generate(num_samples, sample_rate)`

Generates a block of audio and returns it as a list of 16-bit signed integers.

-   **`num_samples` (`int`)**: The number of audio samples to generate.
-   **`sample_rate` (`int`)**: The target sample rate in Hertz (e.g., `44100`).
-   **Returns**: `List[int]` - A list of audio samples ranging from -32768 to 32767.

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
