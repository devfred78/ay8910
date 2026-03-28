import ay8910_standalone as ay
import wave
import struct

def write_wav(filename, samples, sample_rate):
    """Writes a list of samples to a WAV file."""
    with wave.open(filename, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)  # 2 bytes = 16-bit samples
        f.setframerate(sample_rate)
        # Pack samples to binary data
        packed_samples = struct.pack('<' + 'h' * len(samples), *samples)
        f.writeframes(packed_samples)

def main():
    print("Initializing AY-3-8910 emulator via Python wrapper...")

    # --- Parameters ---
    clock = 2000000  # 2 MHz
    sample_rate = 44100
    duration_secs = 2.0
    num_samples = int(sample_rate * duration_secs)

    # --- Create and initialize the AY-3-8910 device ---
    # We use the enums and constants exposed by the module
    psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, clock, 1, 0)
    psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
    psg.start()
    psg.reset()

    print("Programming AY-3-8910 to play a tone...")

    # --- Program the AY-3-8910 to produce a simple tone ---
    # Mixer: Enable Tone on Channel A, disable everything else
    psg.address_w(7)
    psg.data_w(0b00111110)

    # Set Channel A frequency (a simple middle C)
    period = int(clock / (16 * 261.63))
    psg.address_w(0)  # Fine tune
    psg.data_w(period & 0xFF)
    psg.address_w(1)  # Coarse tune
    psg.data_w((period >> 8) & 0x0F)

    # Set Channel A volume to max
    psg.address_w(8)
    psg.data_w(15)

    print(f"Generating {num_samples} samples at {sample_rate} Hz...")

    # --- Generate audio samples using our new method ---
    samples = psg.generate(num_samples, sample_rate)

    print(f"Audio generation complete. Total samples: {len(samples)}")

    # --- Write output to a WAV file ---
    if samples:
        output_filename = "output_python.wav"
        write_wav(output_filename, samples, sample_rate)
        print(f"Output written to {output_filename}")
    else:
        print("Warning: No samples were generated.")

if __name__ == "__main__":
    main()
