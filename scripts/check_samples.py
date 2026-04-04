import wave
import struct

def read_first_samples(path, count=1000):
    print(f"\nFirst samples of {path} (raw values):")
    try:
        with wave.open(path, 'rb') as w:
            frames = w.readframes(count)
            fmt = "<" + "h" * (len(frames) // 2)
            samples = struct.unpack(fmt, frames)
            # Display first 20 values
            print(samples[:20])
            # Calculate mean of the first 100
            avg = sum(samples[:100]) / 100
            print(f"Mean of first 100: {avg:.2f}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_first_samples(r"YM example files\Deflektor_GOOD_MONO_no_metadata.wav")
    read_first_samples(r"YM example files\Deflektor_output_FINAL_V6_recalc.wav")
