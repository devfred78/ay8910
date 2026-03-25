#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "ay8910.h"

namespace py = pybind11;

PYBIND11_MODULE(ay8910_standalone, m) {
    m.doc() = "Python wrapper for the standalone AY-3-8910 emulator";

    py::enum_<ay8910_device::psg_type_t>(m, "psg_type")
        .value("PSG_TYPE_AY", ay8910_device::PSG_TYPE_AY)
        .value("PSG_TYPE_YM", ay8910_device::PSG_TYPE_YM)
        .export_values();

    m.attr("AY8910_LEGACY_OUTPUT") = py::int_(AY8910_LEGACY_OUTPUT);
    m.attr("AY8910_SINGLE_OUTPUT") = py::int_(AY8910_SINGLE_OUTPUT);
    m.attr("AY8910_DISCRETE_OUTPUT") = py::int_(AY8910_DISCRETE_OUTPUT);
    m.attr("AY8910_RESISTOR_OUTPUT") = py::int_(AY8910_RESISTOR_OUTPUT);

    py::class_<ay8910_device>(m, "ay8910")
        .def(py::init<ay8910_device::psg_type_t, int, int, int, int>(),
             py::arg("psg_type"), py::arg("clock"), py::arg("streams"), py::arg("ioports"), py::arg("feature") = ay8910_device::PSG_DEFAULT)
        .def("start", &ay8910_device::start)
        .def("reset", &ay8910_device::reset)
        .def("set_flags", &ay8910_device::set_flags)
        .def("address_w", &ay8910_device::address_w)
        .def("data_w", &ay8910_device::data_w)
        .def("generate", &ay8910_device::generate,
             py::arg("num_samples"), py::arg("sample_rate"),
             "Generate a number of audio samples at a given sample rate");
}
