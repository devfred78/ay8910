#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "ay8910.h"
#include "ay8912_cap32.h"

namespace py = pybind11;

PYBIND11_MODULE(ay8910_wrapper, m) {
    m.doc() = "Python wrapper for the standalone AY-3-8910 emulators (MAME and Caprice32 versions)";

    py::enum_<ay8910_device::psg_type_t>(m, "psg_type")
        .value("PSG_TYPE_AY", ay8910_device::PSG_TYPE_AY)
        .value("PSG_TYPE_YM", ay8910_device::PSG_TYPE_YM)
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
    py::class_<ay8910_device>(m, "ay8910")
        .def(py::init<ay8910_device::psg_type_t, int, int, int, int>(),
             py::arg("psg_type"), py::arg("clock"), py::arg("streams"), py::arg("ioports"), py::arg("feature") = static_cast<int>(ay8910_device::PSG_DEFAULT))
        .def("start", &ay8910_device::start)
        .def("reset", &ay8910_device::reset)
        .def("set_flags", &ay8910_device::set_flags)
        .def("address_w", &ay8910_device::address_w)
        .def("data_w", &ay8910_device::data_w)
        .def("generate", &ay8910_device::generate,
             py::arg("num_samples"), py::arg("sample_rate"),
             "Generate a number of audio samples at a given sample rate");

    // Caprice32 version
    py::class_<ay8912_cap32>(m, "ay8912_cap32")
        .def(py::init<int, int>(), py::arg("clock"), py::arg("sample_rate"))
        .def("reset", &ay8912_cap32::reset)
        .def("address_w", &ay8912_cap32::address_w)
        .def("data_w", &ay8912_cap32::data_w)
        .def("set_stereo_mix", &ay8912_cap32::set_stereo_mix,
             py::arg("al"), py::arg("ar"), py::arg("bl"), py::arg("br"), py::arg("cl"), py::arg("cr"),
             "Set stereo weights for channels A, B, and C")
        .def("generate", &ay8912_cap32::generate,
             py::arg("num_samples"),
             "Generate 16-bit stereo interleaved audio samples");
}
