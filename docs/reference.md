# `ay8910_wrapper` API Reference

This document provides a detailed reference for the functions, classes, and constants available in the `ay8910_wrapper` Python module, automatically generated from the source code.

## Main Interface

The `ay8910_wrapper` package provides a high-level interface to the PSG emulators. The following attributes include constants used to configure the emulation during the instantiation of the `ay8910`, `ay8912`, and `ay8913` classes.

::: ay8910_wrapper
    options:
      members:
        - AYBase
        - ay8910
        - ay8912
        - ay8913
        - Backend
        - psg_type
        - ay_emul31_chip_type
        - AY8910_LEGACY_OUTPUT
        - AY8910_SINGLE_OUTPUT
        - AY8910_DISCRETE_OUTPUT
        - AY8910_RESISTOR_OUTPUT
        - PSG_PIN26_IS_CLKSEL
        - PSG_HAS_INTERNAL_DIVIDER
        - PSG_EXTENDED_ENVELOPE
        - PSG_HAS_EXPANDED_MODE
      show_root_heading: false
      show_source: false
      inherited_members: false
      show_category_heading: true
      show_root_toc_entry: true
      show_root_full_path: true

## Audio Output

The `direct_output` module handles real-time audio playback using `sounddevice`.

::: ay8910_wrapper.direct_output
    options:
      show_root_heading: true
      show_source: true
