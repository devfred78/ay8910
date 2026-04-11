#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "ay8910.h"
#include "ay8912_cap32.h"
#include "ay_emul31.h"

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
                                          "#### Tone Period (Registers 0-5)\n"
                                          "These registers control the pitch of the three square wave channels. Each channel uses two registers (Fine and Coarse) to form a 12-bit period value.\n"
                                          "Formula: $f = \\text{Clock} / (16 \\times \\text{Period})$\n\n"
                                          "| Register | Function | Bits |\n"
                                          "| :--- | :--- | :--- |\n"
                                          "| **0** | Channel A Fine Tune | 8-bit |\n"
                                          "| **1** | Channel A Coarse Tune | 4-bit |\n"
                                          "| **2** | Channel B Fine Tune | 8-bit |\n"
                                          "| **3** | Channel B Coarse Tune | 4-bit |\n"
                                          "| **4** | Channel C Fine Tune | 8-bit |\n"
                                          "| **5** | Channel C Coarse Tune | 4-bit |\n\n"
                                          "#### Noise Period (Register 6)\n"
                                          "Controls the frequency of the pseudo-random noise generator used for percussion or sound effects.\n\n"
                                          "| Register | Function | Bits |\n"
                                          "| :--- | :--- | :--- |\n"
                                          "| **6** | Noise Period | 5-bit |\n\n"
                                          "#### Mixer Control (Register 7)\n"
                                          "Enables or disables Tone and Noise for each of the three channels. It also controls the I/O port directions. Bits are active-low (0 = Enabled, 1 = Disabled).\n\n"
                                          "| Bit | Function |\n"
                                          "| :--- | :--- |\n"
                                          "| **0** | Tone A (0: On, 1: Off) |\n"
                                          "| **1** | Tone B (0: On, 1: Off) |\n"
                                          "| **2** | Tone C (0: On, 1: Off) |\n"
                                          "| **3** | Noise A (0: On, 1: Off) |\n"
                                          "| **4** | Noise B (0: On, 1: Off) |\n"
                                          "| **5** | Noise C (0: On, 1: Off) |\n"
                                          "| **6** | Port A Direction (0: Input, 1: Output) |\n"
                                          "| **7** | Port B Direction (0: Input, 1: Output) |\n\n"
                                          "#### Amplitude/Volume (Registers 8-10)\n"
                                          "Controls the volume of each channel. A value of 0-15 sets a fixed volume. If bit 4 is set (value 16), the channel follows the hardware envelope.\n\n"
                                          "| Register | Function | Range |\n"
                                          "| :--- | :--- | :--- |\n"
                                          "| **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n"
                                          "| **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n"
                                          "| **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n\n"
                                          "#### Envelope Period (Registers 11-12)\n"
                                          "Sets the duration of one envelope cycle (16-bit value). Formula: $T = (256 \\times \\text{Period}) / \\text{Clock}$\n\n"
                                          "| Register | Function | Bits |\n"
                                          "| :--- | :--- | :--- |\n"
                                          "| **11** | Envelope Fine Tune | 8-bit |\n"
                                          "| **12** | Envelope Coarse Tune | 8-bit |\n\n"
                                          "#### Envelope Shape (Register 13)\n"
                                          "Controls the shape of the volume variation (Attack, Decay, Sustain, Release).\n\n"
                                          "| Bit 3 | Bit 2 | Bit 1 | Bit 0 | Shape Description |\n"
                                          "| :--- | :--- | :--- | :--- | :--- |\n"
                                          "| **0** | **0** | **x** | **x** | `\\___` (Single Decay, then Silence) |\n"
                                          "| **1** | **0** | **0** | **0** | `\\\\\\\\\\\\\\\\` (Repeating Decay / Sawtooth) |\n"
                                          "| **1** | **0** | **1** | **1** | `/\\|/\\|/\\|` (Repeating Attack / Inverse Sawtooth) |\n"
                                          "| **1** | **1** | **0** | **0** | `/\\/\\/\\` (Triangle) |\n\n"
                                          "#### I/O Ports (Registers 14-15)\n"
                                          "Data registers for the two 8-bit parallel ports.\n\n"
                                          "| Register | Function |\n"
                                          "| :--- | :--- |\n"
                                          "| **14** | Port A Data |\n"
                                          "| **15** | Port B Data |\n\n"
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
        .def("set_resistors_load", &ay8910_device::set_resistors_load, py::arg("res_load0"), py::arg("res_load1"), py::arg("res_load2"),
             "Sets the load resistors (in Ohms) for the three audio channels (A, B, C).\n\n"
             "Used when AY8910_RESISTOR_OUTPUT is enabled to calculate the output voltage based on MOSFET characteristics.")
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
                                                "#### Tone Period (Registers 0-5)\n"
                                                "These registers control the pitch of the three square wave channels. Each channel uses two registers (Fine and Coarse) to form a 12-bit period value.\n"
                                                "Formula: $f = \\text{Clock} / (16 \\times \\text{Period})$\n\n"
                                                "| Register | Function | Bits |\n"
                                                "| :--- | :--- | :--- |\n"
                                                "| **0** | Channel A Fine Tune | 8-bit |\n"
                                                "| **1** | Channel A Coarse Tune | 4-bit |\n"
                                                "| **2** | Channel B Fine Tune | 8-bit |\n"
                                                "| **3** | Channel B Coarse Tune | 4-bit |\n"
                                                "| **4** | Channel C Fine Tune | 8-bit |\n"
                                                "| **5** | Channel C Coarse Tune | 4-bit |\n\n"
                                                "#### Noise Period (Register 6)\n"
                                                "Controls the frequency of the pseudo-random noise generator used for percussion or sound effects.\n\n"
                                                "| Register | Function | Bits |\n"
                                                "| :--- | :--- | :--- |\n"
                                                "| **6** | Noise Period | 5-bit |\n\n"
                                                "#### Mixer Control (Register 7)\n"
                                                "Enables or disables Tone and Noise for each of the three channels. It also controls the I/O port directions. Bits are active-low (0 = Enabled, 1 = Disabled).\n\n"
                                                "| Bit | Function |\n"
                                                "| :--- | :--- |\n"
                                                "| **0** | Tone A (0: On, 1: Off) |\n"
                                                "| **1** | Tone B (0: On, 1: Off) |\n"
                                                "| **2** | Tone C (0: On, 1: Off) |\n"
                                                "| **3** | Noise A (0: On, 1: Off) |\n"
                                                "| **4** | Noise B (0: On, 1: Off) |\n"
                                                "| **5** | Noise C (0: On, 1: Off) |\n"
                                                "| **6** | Port A Direction (0: Input, 1: Output) |\n"
                                                "| **7** | Port B Direction (0: Input, 1: Output) |\n\n"
                                                "#### Amplitude/Volume (Registers 8-10)\n"
                                                "Controls the volume of each channel. A value of 0-15 sets a fixed volume. If bit 4 is set (value 16), the channel follows the hardware envelope.\n\n"
                                                "| Register | Function | Range |\n"
                                                "| :--- | :--- | :--- |\n"
                                                "| **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n"
                                                "| **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n"
                                                "| **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n\n"
                                                "#### Envelope Period (Registers 11-12)\n"
                                                "Sets the duration of one envelope cycle (16-bit value). Formula: $T = (256 \\times \\text{Period}) / \\text{Clock}$\n\n"
                                                "| Register | Function | Bits |\n"
                                                "| :--- | :--- | :--- |\n"
                                                "| **11** | Envelope Fine Tune | 8-bit |\n"
                                                "| **12** | Envelope Coarse Tune | 8-bit |\n\n"
                                                "#### Envelope Shape (Register 13)\n"
                                                "Controls the shape of the volume variation (Attack, Decay, Sustain, Release).\n\n"
                                                "| Bit 3 | Bit 2 | Bit 1 | Bit 0 | Shape Description |\n"
                                                "| :--- | :--- | :--- | :--- | :--- |\n"
                                                "| **0** | **0** | **x** | **x** | `\\___` (Single Decay, then Silence) |\n"
                                                "| **1** | **0** | **0** | **0** | `\\\\\\\\\\\\\\\\` (Repeating Decay / Sawtooth) |\n"
                                                "| **1** | **0** | **1** | **1** | `/\\|/\\|/\\|` (Repeating Attack / Inverse Sawtooth) |\n"
                                                "| **1** | **1** | **0** | **0** | `/\\/\\/\\` (Triangle) |\n\n"
                                                "#### I/O Ports (Registers 14-15)\n"
                                                "Data registers for the two 8-bit parallel ports.\n\n"
                                                "| Register | Function |\n"
                                                "| :--- | :--- |\n"
                                                "| **14** | Port A Data |\n"
                                                "| **15** | Port B Data |\n\n"
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

    // Sergey Bulba (Ay_Emul31b) version
    py::enum_<ay_emul31::ChType>(m, "ay_emul31_chip_type", "Enum for selecting the chip model to emulate in the Ay_Emul31 engine.")
        .value("AY_Chip", ay_emul31::ChType::AY_Chip, "Emulates the AY-3-8910 chip.")
        .value("YM_Chip", ay_emul31::ChType::YM_Chip, "Emulates the Yamaha YM2149 chip.")
        .export_values();

    py::class_<ay_emul31::TSoundChip>(m, "ay_emul31", "Emulator class based on Sergey Bulba's Ay_Emul29+ (version 3.1) implementation.\n\n"
                                                   "This version is a port of the original Pascal source code to C++, providing a mono emulation "
                                                   "with support for both AY and YM volume tables.\n\n"
                                                   "### PSG Registers Reference (0-15)\n\n"
                                                   "#### Tone Period (Registers 0-5)\n"
                                                   "These registers control the pitch of the three square wave channels.\n\n"
                                                   "| Register | Function | Bits |\n"
                                                   "| :--- | :--- | :--- |\n"
                                                   "| **0** | Channel A Fine Tune | 8-bit |\n"
                                                   "| **1** | Channel A Coarse Tune | 4-bit |\n"
                                                   "| **2** | Channel B Fine Tune | 8-bit |\n"
                                                   "| **3** | Channel B Coarse Tune | 4-bit |\n"
                                                   "| **4** | Channel C Fine Tune | 8-bit |\n"
                                                   "| **5** | Channel C Coarse Tune | 4-bit |\n\n"
                                                   "#### Noise Period (Register 6)\n"
                                                   "Controls the frequency of the pseudo-random noise generator.\n\n"
                                                   "| Register | Function | Bits |\n"
                                                   "| :--- | :--- | :--- |\n"
                                                   "| **6** | Noise Period | 5-bit |\n\n"
                                                   "#### Mixer Control (Register 7)\n"
                                                   "Enables or disables Tone and Noise for each of the three channels. Bits are active-low.\n\n"
                                                   "| Bit | Function |\n"
                                                   "| :--- | :--- |\n"
                                                   "| **0** | Tone A (0: On, 1: Off) |\n"
                                                   "| **1** | Tone B (0: On, 1: Off) |\n"
                                                   "| **2** | Tone C (0: On, 1: Off) |\n"
                                                   "| **3** | Noise A (0: On, 1: Off) |\n"
                                                   "| **4** | Noise B (0: On, 1: Off) |\n"
                                                   "| **5** | Noise C (0: On, 1: Off) |\n\n"
                                                   "#### Amplitude/Volume (Registers 8-10)\n"
                                                   "Controls the volume of each channel. A value of 0-15 sets a fixed volume. If bit 4 is set (value 16), the channel follows the hardware envelope.\n\n"
                                                   "| Register | Function | Range |\n"
                                                   "| :--- | :--- | :--- |\n"
                                                   "| **8** | Channel A Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n"
                                                   "| **9** | Channel B Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n"
                                                   "| **10** | Channel C Amplitude | 0-15 (Fixed) or 16 (Envelope) |\n\n"
                                                   "#### Envelope Period (Registers 11-12)\n"
                                                   "Sets the duration of one envelope cycle (16-bit value).\n\n"
                                                   "| Register | Function | Bits |\n"
                                                   "| :--- | :--- | :--- |\n"
                                                   "| **11** | Envelope Fine Tune | 8-bit |\n"
                                                   "| **12** | Envelope Coarse Tune | 8-bit |\n\n"
                                                   "#### Envelope Shape (Register 13)\n"
                                                   "Controls the shape of the volume variation.\n\n"
                                                   "| Bit 3 | Bit 2 | Bit 1 | Bit 0 | Shape Description |\n"
                                                   "| :--- | :--- | :--- | :--- | :--- |\n"
                                                   "| **0** | **0** | **x** | **x** | `\\___` (Single Decay, then Silence) |\n"
                                                   "| **1** | **0** | **0** | **0** | `\\\\\\\\\\\\\\\\` (Repeating Decay / Sawtooth) |\n"
                                                   "| **1** | **0** | **1** | **1** | `/\\|/\\|/\\|` (Repeating Attack / Inverse Sawtooth) |\n"
                                                   "| **1** | **1** | **0** | **0** | `/\\/\\/\\` (Triangle) |\n\n"
                                                   "### Usage Examples\n\n"
                                                   "```python\n"
                                                   "chip = ay.ay_emul31()\n"
                                                   "chip.chip_type = ay.ay_emul31_chip_type.YM_Chip\n"
                                                   "chip.set_register(0, 255) # Set Tone A\n"
                                                   "```")
        .def(py::init<>(), "Constructor for the Ay_Emul31 emulator instance.")
        .def_readwrite("chip_type", &ay_emul31::TSoundChip::chip_type, "The type of chip to emulate (AY or YM).")
        .def("reset", &ay_emul31::TSoundChip::Reset, py::arg("zeroregs") = true,
             "Resets the emulator state.\n\n"
             "Args:\n"
             "    zeroregs (bool): If true, all registers are cleared to zero (default: true).")
        .def("set_register", &ay_emul31::TSoundChip::SetAYRegister, py::arg("reg"), py::arg("value"),
             "Writes a value to an internal register (0-15).\n\n"
             "Args:\n"
             "    reg (int): The register index (0-15).\n"
             "    value (int): The 8-bit value to write.")
        .def("generate", &ay_emul31::TSoundChip::generate_vector,
             py::arg("num_samples"), py::arg("clock"), py::arg("sample_rate"),
             "Generates a block of mono audio samples.\n\n"
             "Args:\n"
             "    num_samples (int): Number of audio samples to generate.\n"
             "    clock (int): Master clock frequency in Hz.\n"
             "    sample_rate (int): Target output sample rate in Hz.\n\n"
             "Returns:\n"
             "    List[int]: Mono audio samples ranging from -32768 to 32767.");
}