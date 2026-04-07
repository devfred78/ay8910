#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "ay8910.h"
#include "ay8912_cap32.h"

namespace py = pybind11;

PYBIND11_MODULE(ay8910_wrapper, m) {
    m.doc() = "Python wrapper for the standalone AY-3-8910 emulators (MAME and Caprice32 versions)";

    py::enum_<ay8910_device::psg_type_t>(m, "psg_type", "Enum for selecting the chip model to emulate.")
        .value("PSG_TYPE_AY", ay8910_device::PSG_TYPE_AY, "Emulates the General Instrument AY-3-8910.")
        .value("PSG_TYPE_YM", ay8910_device::PSG_TYPE_YM, "Emulates the Yamaha YM2149, with a different volume curve.")
        .export_values();

    m.attr("AY8910_LEGACY_OUTPUT") = py::int_(AY8910_LEGACY_OUTPUT);
    m.attr("AY8910_SINGLE_OUTPUT") = py::int_(AY8910_SINGLE_OUTPUT);
    m.attr("AY8910_DISCRETE_OUTPUT") = py::int_(AY8910_DISCRETE_OUTPUT);
    m.attr("AY8910_RESISTOR_OUTPUT") = py::int_(AY8910_RESISTOR_OUTPUT);
    m.attr("PSG_PIN26_IS_CLKSEL") = py::int_(static_cast<int>(ay8910_device::PSG_PIN26_IS_CLKSEL));
    m.attr("PSG_HAS_INTERNAL_DIVIDER") = py::int_(static_cast<int>(ay8910_device::PSG_HAS_INTERNAL_DIVIDER));
    m.attr("PSG_EXTENDED_ENVELOPE") = py::int_(static_cast<int>(ay8910_device::PSG_EXTENDED_ENVELOPE));
    m.attr("PSG_HAS_EXPANDED_MODE") = py::int_(static_cast<int>(ay8910_device::PSG_HAS_EXPANDED_MODE));

    // MAME version
    py::class_<ay8910_device>(m, "ay8910", "Main class for instantiating and controlling an AY-3-8910 emulator based on the MAME implementation.\n\n"
                                          "The emulated chip features 16 internal registers (0-15) to control 3 square wave channels and a noise generator.\n\n"
                                          "### PSG Registers Reference (0-15)\n\n"
                                          "* **0-1**: Channel A Tone Period (12-bit, Fine/Coarse).\n"
                                          "* **2-3**: Channel B Tone Period (12-bit, Fine/Coarse).\n"
                                          "* **4-5**: Channel C Tone Period (12-bit, Fine/Coarse).\n"
                                          "* **6**: Noise Period (5-bit).\n"
                                          "* **7**: Mixer Control (Tone/Noise enable for A/B/C, active-low).\n"
                                          "* **8-10**: Amplitude/Volume for A/B/C (0-15 fixed or 16 for Envelope).\n"
                                          "* **11-12**: Envelope Period (16-bit, Fine/Coarse).\n"
                                          "* **13**: Envelope Shape (Attack, Decay, Sustain, Release).\n"
                                          "* **14-15**: I/O Ports A and B Data.\n\n"
                                          "### Usage Examples\n\n"
                                          "**Low-level access (hardware-like):**\n"
                                          "```python\n"
                                          "chip.address_w(0) # Select Channel A Fine Tone register\n"
                                          "chip.data_w(255)   # Write value\n"
                                          "```\n\n"
                                          "**High-level access (direct register write):**\n"
                                          "```python\n"
                                          "chip.set_register(0, 255) # Directly write to Channel A Fine Tone register\n"
                                          "```")
        .def(py::init<ay8910_device::psg_type_t, int, int, int, int>(),
             py::arg("psg_type"), py::arg("clock"), py::arg("streams"), py::arg("ioports"), py::arg("feature") = static_cast<int>(ay8910_device::PSG_DEFAULT),
             "Constructor for the emulator instance.\n\n"
             "Args:\n"
             "    psg_type (psg_type): The type of sound chip to emulate (AY or YM).\n"
             "    clock (int): The clock frequency of the chip in Hertz (e.g., 2000000 for 2 MHz).\n"
             "    streams (int): Number of output audio streams (usually 1).\n"
             "    ioports (int): Number of I/O ports to emulate (0, 1, or 2).\n"
             "    feature (int, optional): Advanced chip-specific features. Defaults to PSG_DEFAULT.")
        .def("start", &ay8910_device::start, "Initializes the emulator core. Must be called before any sound generation.")
        .def("reset", &ay8910_device::reset, "Resets the state of all registers and internal counters to default values.")
        .def("set_flags", &ay8910_device::set_flags, py::arg("flags"),
             "Sets behavioral flags for the emulation (e.g., AY8910_LEGACY_OUTPUT).")
        .def("address_w", &ay8910_device::address_w, py::arg("value"),
             "Writes a value to the address latch to select a register (0-15).")
        .def("data_w", &ay8910_device::data_w, py::arg("value"),
             "Writes a 8-bit value to the register previously selected by address_w().")
        .def("get_register", &ay8910_device::get_register, py::arg("reg"),
             "Reads the value of an internal register (0-31).")
        .def("set_register", &ay8910_device::set_register, py::arg("reg"), py::arg("value"),
             "Writes a value to an internal register (0-31) and updates the emulation state.")
        .def("get_registers", &ay8910_device::get_registers, "Returns all 32 internal registers as a list of integers.")
        .def("generate", &ay8910_device::generate,
             py::arg("num_samples"), py::arg("sample_rate"),
             "Generates a block of audio samples and returns it as a list of 16-bit signed integers.\n\n"
             "Args:\n"
             "    num_samples (int): Number of audio samples to generate.\n"
             "    sample_rate (int): Target sample rate in Hertz (e.g., 44100).\n"
             "\n"
             "Returns:\n"
             "    List[int]: Mono audio samples ranging from -32768 to 32767.");

    // Caprice32 version
    py::class_<ay8912_cap32>(m, "ay8912_cap32", "Specialized emulator class based on the Caprice32 (Amstrad CPC) implementation. Natively stereo.\n\n"
                                                "The emulated chip features 16 internal registers (0-15) to control 3 square wave channels and a noise generator.\n\n"
                                                "### PSG Registers Reference (0-15)\n\n"
                                                "* **0-1**: Channel A Tone Period (12-bit, Fine/Coarse).\n"
                                                "* **2-3**: Channel B Tone Period (12-bit, Fine/Coarse).\n"
                                                "* **4-5**: Channel C Tone Period (12-bit, Fine/Coarse).\n"
                                                "* **6**: Noise Period (5-bit).\n"
                                                "* **7**: Mixer Control (Tone/Noise enable for A/B/C, active-low).\n"
                                                "* **8-10**: Amplitude/Volume for A/B/C (0-15 fixed or 16 for Envelope).\n"
                                                "* **11-12**: Envelope Period (16-bit, Fine/Coarse).\n"
                                                "* **13**: Envelope Shape (Attack, Decay, Sustain, Release).\n"
                                                "* **14-15**: I/O Ports A and B Data.\n\n"
                                                "### Usage Examples\n\n"
                                                "**Low-level access (hardware-like):**\n"
                                                "```python\n"
                                                "chip.address_w(0) # Select Channel A Fine Tone register\n"
                                                "chip.data_w(255)   # Write value\n"
                                                "```\n\n"
                                                "**High-level access (direct register write):**\n"
                                                "```python\n"
                                                "chip.set_register(0, 255) # Directly write to Channel A Fine Tone register\n"
                                                "```")
        .def(py::init<int, int>(), py::arg("clock"), py::arg("sample_rate"),
             "Constructor for the Caprice32 PSG instance.\n\n"
             "Args:\n"
             "    clock (int): Master clock frequency (e.g., 1000000 for 1 MHz).\n"
             "    sample_rate (int): Target output sample rate (e.g., 44100).")
        .def("reset", &ay8912_cap32::reset, "Resets the emulator state.")
        .def("address_w", &ay8912_cap32::address_w, py::arg("value"), "Writes a value to the address latch.")
        .def("data_w", &ay8912_cap32::data_w, py::arg("value"), "Writes data to the selected register.")
        .def("get_register", &ay8912_cap32::get_register, py::arg("reg"), "Reads the value of an internal register (0-15).")
        .def("set_register", &ay8912_cap32::set_register, py::arg("reg"), py::arg("value"),
             "Writes a value to an internal register (0-15) and updates the emulation state.")
        .def("get_registers", &ay8912_cap32::get_registers, "Returns all 16 internal registers as a list.")
        .def("set_stereo_mix", &ay8912_cap32::set_stereo_mix,
             py::arg("al"), py::arg("ar"), py::arg("bl"), py::arg("br"), py::arg("cl"), py::arg("cr"),
             "Sets the stereo weights (panning) for the three PSG channels (A, B, C).\n\n"
             "Args:\n"
             "    al, ar (int): Left and Right weights for Channel A (0-255).\n"
             "    bl, br (int): Left and Right weights for Channel B (0-255).\n"
             "    cl, cr (int): Left and Right weights for Channel C (0-255).")
        .def("generate", &ay8912_cap32::generate,
             py::arg("num_samples"),
             "Generates interleaved stereo audio samples.\n\n"
             "Args:\n"
             "    num_samples (int): Number of samples to generate.\n\n"
             "Returns:\n"
             "    List[int]: A list of num_samples * 2 integers (alternating Left and Right).");
}