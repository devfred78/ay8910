CXX = g++
CXXFLAGS = -std=c++11 -Wall -Wextra -O2

# Use the -static flag to create a fully standalone executable with no
# dependencies on MinGW runtime DLLs.
LDFLAGS = -static

SOURCES = main.cpp ay8910.cpp
OBJECTS = $(SOURCES:.cpp=.o)
EXECUTABLE = ay_standalone_test

.PHONY: all clean

all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(CXX) $(LDFLAGS) $(OBJECTS) -o $@

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(EXECUTABLE) output.wav
