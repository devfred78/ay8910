# Makefile for creating a Python module

# --- Variables ---
CXX = g++

# Use python3-config for robust flag generation
PYTHON_CFLAGS   := $(shell python3-config --cflags)
PYTHON_LIBS     := $(shell python3-config --libs --embed)
PYBIND11_INCLUDES := -I./pybind11/include

# Get the Python extension suffix
EXT_SUFFIX := $(shell python3-config --extension-suffix)
MODULE_NAME = ay8910_standalone

# --- CXX Flags ---
CXXFLAGS = -std=c++11 -Wall -Wextra -O2 -fPIC $(PYBIND11_INCLUDES) $(PYTHON_CFLAGS)

# --- Linker Flags ---
# Statically link the C++ and GCC runtime libraries to make the module portable.
LDFLAGS = -static-libgcc -static-libstdc++

# --- Sources ---
SOURCES = wrapper.cpp ay8910.cpp
OBJECTS = $(SOURCES:.cpp=.o)
TARGET = $(MODULE_NAME)$(EXT_SUFFIX)

# --- Rules ---
.PHONY: all clean

all: $(TARGET)

# Rule to link the final shared library (.pyd)
$(TARGET): $(OBJECTS)
	$(CXX) -shared $(OBJECTS) -o $@ $(PYTHON_LIBS) $(LDFLAGS)

# Rule to compile .cpp files into .o object files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET) output_python.wav
