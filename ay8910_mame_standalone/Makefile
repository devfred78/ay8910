# Makefile for creating a Python module

# --- Variables ---
CXX = g++

# Use python3-config for robust flag generation. This is the standard way.
# --cflags provides include paths.
# --libs provides library paths and names.
# --embed ensures all symbols are available for linking, which is crucial on some systems.
PYTHON_CFLAGS   := $(shell python3-config --cflags)
PYTHON_LIBS     := $(shell python3-config --libs --embed)
PYBIND11_INCLUDES := -I./pybind11/include

# Get the Python extension suffix (e.g., .pyd, .so)
EXT_SUFFIX := $(shell python3-config --extension-suffix)
MODULE_NAME = ay8910_standalone

# --- CXX Flags ---
# -fPIC is required for shared libraries
CXXFLAGS = -std=c++11 -Wall -Wextra -O2 -fPIC $(PYBIND11_INCLUDES) $(PYTHON_CFLAGS)

# --- Sources ---
SOURCES = wrapper.cpp ay8910.cpp
OBJECTS = $(SOURCES:.cpp=.o)
TARGET = $(MODULE_NAME)$(EXT_SUFFIX)

# --- Rules ---
.PHONY: all clean

all: $(TARGET)

# Rule to link the final shared library (.pyd)
$(TARGET): $(OBJECTS)
	$(CXX) -shared $(OBJECTS) -o $@ $(PYTHON_LIBS)

# Rule to compile .cpp files into .o object files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET) output_python.wav
