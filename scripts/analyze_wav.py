import struct
import sys
import wave


def analyze_wav(path):
    print(f"\nAnalyzing {path}:")
    try:
        with wave.open(path, 'rb') as w:
            params = w.getparams()
            print(f"  Channels      : {params.nchannels}")
            print(f"  Sample width  : {params.sampwidth} bytes ({params.sampwidth*8} bits)")
            print(f"  Frequency     : {params.framerate} Hz")
            print(f"  Frame count   : {params.nframes}")
            duration = params.nframes / params.framerate
            print(f"  Duration      : {duration:.2f} s")
            
            # Statistical analysis on a 5-second segment in the middle
            mid = params.nframes // 2
            start = max(0, mid - params.framerate * 2)
            w.setpos(start)
            n_frames = min(params.framerate * 5, params.nframes - start)
            frames = w.readframes(n_frames)
            if params.sampwidth == 2:
                fmt = "<" + "h" * (len(frames) // 2)
                samples = struct.unpack(fmt, frames)
                if params.nchannels == 2:
                    samples_l = samples[::2]
                    samples_r = samples[1::2]
                    print("  Stereo detected.")
                    print(
                        f"  Max amplitude (L/R): {max(abs(min(samples_l)), max(samples_l))} / "
                        f"{max(abs(min(samples_r)), max(samples_r))}"
                    )
                    samples = samples_l # Work on L for the following
                else:
                    print("  Mono detected.")
                    print(f"  Max amplitude: {max(abs(min(samples)), max(samples))}")
                
                # Mean (DC offset)
                avg = sum(samples) / len(samples)
                print(f"  Mean value (DC): {avg:.2f}")

                # Zero crossings for dominant frequency
                last_s = samples[0]
                crossings = []
                for i in range(1, len(samples)):
                    if (last_s <= 0 and samples[i] > 0):
                        crossings.append(i)
                    last_s = samples[i]
                
                if len(crossings) >= 2:
                    freq = (len(crossings)-1) * params.framerate / (crossings[-1] - crossings[0])
                    print(f"  Estimated dominant frequency: {freq:.2f} Hz")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        analyze_wav(arg)
    if len(sys.argv) == 1:
        analyze_wav("YM example files/Deflektor_GOOD.wav")
        analyze_wav("YM example files/Deflektor_output.wav")
