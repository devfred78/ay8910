#include "ay8910.h"
#include <iostream>
#include <vector>
#include <fstream>

// A simple WAV file writer
void write_wav(const std::string& filename, const std::vector<short>& samples, int sample_rate) {
    std::ofstream f(filename, std::ios::binary);
    if (!f.is_open()) {
        std::cerr << "Error: Could not open " << filename << " for writing." << std::endl;
        return;
    }

    // WAV header
    f.write("RIFF", 4);
    uint32_t file_size = 36 + samples.size() * sizeof(short);
    f.write(reinterpret_cast<const char*>(&file_size), 4);
    f.write("WAVE", 4);
    f.write("fmt ", 4);
    uint32_t fmt_chunk_size = 16;
    f.write(reinterpret_cast<const char*>(&fmt_chunk_size), 4);
    uint16_t audio_format = 1; // PCM
    f.write(reinterpret_cast<const char*>(&audio_format), 2);
    uint16_t num_channels = 1;
    f.write(reinterpret_cast<const char*>(&num_channels), 2);
    f.write(reinterpret_cast<const char*>(&sample_rate), 4);
    uint32_t byte_rate = sample_rate * num_channels * sizeof(short);
    f.write(reinterpret_cast<const char*>(&byte_rate), 4);
    uint16_t block_align = num_channels * sizeof(short);
    f.write(reinterpret_cast<const char*>(&block_align), 2);
    uint16_t bits_per_sample = 16;
    f.write(reinterpret_cast<const char*>(&bits_per_sample), 2);
    f.write("data", 4);
    uint32_t data_size = samples.size() * sizeof(short);
    f.write(reinterpret_cast<const char*>(&data_size), 4);

    // Audio data
    f.write(reinterpret_cast<const char*>(samples.data()), data_size);

    if (!f.good()) {
        std::cerr << "Error: An error occurred while writing to " << filename << std::endl;
    }
}


int main() {
    const int clock = 2000000; // 2 MHz
    const int sample_rate = 44100;
    const double duration_secs = 2.0;
    const int num_samples = static_cast<int>(sample_rate * duration_secs);

    // --- Create and initialize the AY-3-8910 device ---
    ay8910_device ay(ay8910_device::PSG_TYPE_AY, clock, 1, 0);
    ay.set_flags(AY8910_LEGACY_OUTPUT);
    ay.start();
    ay.reset();

    std::cout << "AY-3-8910 initialized." << std::endl;

    // --- Program the AY-3-8910 to produce a simple tone ---
    // Mixer: Enable Tone on Channel A, disable everything else.
    // Bit 0 is Tone A. 0 = ON, 1 = OFF.
    ay.address_w(7);
    ay.data_w(0b00111110);

    // Set Channel A frequency (a simple middle C)
    int period = clock / (16 * 261.63);
    ay.address_w(0); // Fine tune
    ay.data_w(period & 0xFF);
    ay.address_w(1); // Coarse tune
    ay.data_w((period >> 8) & 0x0F);

    // Set Channel A volume to max
    ay.address_w(8);
    ay.data_w(15);

    std::cout << "AY-3-8910 programmed to play a tone." << std::endl;

    // --- Generate audio samples ---
    std::vector<short> final_samples;
    final_samples.reserve(num_samples);

    sound_stream stream;
    stream.set_sample_rate(sample_rate);

    int samples_generated = 0;
    while (samples_generated < num_samples) {
        int samples_to_generate = std::min(1024, num_samples - samples_generated);
        stream.update(samples_to_generate);
        ay.sound_stream_update(stream);

        const auto& buffer = stream.get_buffer();
        for (const auto& sample : buffer) {
            // Convert double sample to short
            final_samples.push_back(static_cast<short>(sample * 32767.0));
        }
        samples_generated += samples_to_generate;
    }

    std::cout << "Audio generation complete. Total samples: " << final_samples.size() << std::endl;


    // --- Write output to a WAV file ---
    if (!final_samples.empty()) {
        write_wav("output.wav", final_samples, sample_rate);
        std::cout << "Output written to output.wav" << std::endl;
    } else {
        std::cerr << "Warning: No samples were generated. output.wav was not created." << std::endl;
    }

    return 0;
}
