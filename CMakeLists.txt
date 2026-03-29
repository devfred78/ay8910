cmake_minimum_required(VERSION 3.15)

# Silence the pybind11 deprecation warning
cmake_policy(SET CMP0148 NEW)

project(ay8910_wrapper CXX)

# --- C++ Standard ---
# The MAME code uses C++17 features (like if-initializers)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- C++ Library ---
# Define our standalone C++ library
add_library(ay8910_cpp_lib
    ay8910_cpp_lib/ay8910.cpp
)
# Specify its include directory
target_include_directories(ay8910_cpp_lib PUBLIC ay8910_cpp_lib)

# --- Python Module ---
# Find pybind11 (provided by scikit-build-core)
find_package(pybind11 CONFIG REQUIRED)

# Define the Python module using our wrapper and linking to our C++ library
pybind11_add_module(ay8910_wrapper
    src/ay8910_wrapper/wrapper.cpp
)
target_link_libraries(ay8910_wrapper PRIVATE ay8910_cpp_lib)

# --- Installation ---
# This tells scikit-build where to install the final .pyd file
install(TARGETS ay8910_wrapper DESTINATION ay8910_wrapper)
