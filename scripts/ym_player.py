import struct
import sys
import os
import wave
import ay8910_wrapper as ay
import time
import argparse

# We need to add the lhafile library to handle compressed .ym files
try:
    import lhafile
except ImportError:
    print("ERROR: The 'lhafile' library is not installed.", file=sys.stderr)
    print("Please install it by running: pip install lhafile", file=sys.stderr)
    sys.exit(1)

# Use sounddevice for live playback (easier to install than pyaudio)
try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    sd = None

def read_nt_string(data, offset):
    """Reads a null-terminated string from bytes."""
    end = data.find(b'\0', offset)
    if end == -1:
        return "", len(data)
    return data[offset:end].decode('latin-1', 'ignore'), end + 1

def play_ym(filename, output_wav, live_play, engine="cap32"):
    if live_play and sd is None:
        print("ERROR: The 'sounddevice' and/or 'numpy' libraries are not installed.", file=sys.stderr)
        print("Live playback is not available. Please install them by running:", file=sys.stderr)
        print("uv pip install sounddevice numpy", file=sys.stderr)
        return

    print(f"Reading {filename}...")
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find file '{filename}'.")
        return

    if len(data) < 4:
        print("Error: File too small.")
        return

    # Check for LHA compression signature and decompress in-memory if found
    if len(data) > 6 and b'-lh' in data[2:6]:
        print("LHA compression detected. Attempting to decompress in-memory...")
        try:
            lha_archive = lhafile.LhaFile(filename)
            best_candidate = max(lha_archive.infolist(), key=lambda f: f.file_size, default=None)
            if best_candidate:
                print(f"Extracting '{best_candidate.filename}' from archive...")
                data = lha_archive.read(best_candidate.filename)
            else:
                print("Error: Could not find a valid file inside the LHA archive.")
                return
        except Exception as e:
            print(f"Error during LHA decompression: {e}")
            return

    header_id = data[0:4]
    
    clock = 2000000
    fps = 50
    nframes = 0
    interleaved = False
    offset = 0
    num_regs = 16
    
    if header_id in (b'YM5!', b'YM6!'):
        if data[4:12] != b'LeOnArD!':
            print("Error: Invalid YM5/YM6 signature.")
            return
            
        nframes = struct.unpack('>I', data[12:16])[0]
        attributes = struct.unpack('>I', data[16:20])[0]
        interleaved = (attributes & 1) != 0
        ndigidrums = struct.unpack('>H', data[20:22])[0]
        clock = struct.unpack('>I', data[22:26])[0]
        fps = struct.unpack('>H', data[26:28])[0]
        loop_frame = struct.unpack('>I', data[28:32])[0]
        add_size = struct.unpack('>H', data[32:34])[0]

        offset = 34
        
        for _ in range(ndigidrums):
            size = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4 + size
            
        song_name, offset = read_nt_string(data, offset)
        author, offset = read_nt_string(data, offset)
        comment, offset = read_nt_string(data, offset)
        
        print(f"Format : {header_id.decode()}")
        print(f"Song   : {song_name}")
        print(f"Author : {author}")
        print(f"Frames : {nframes} ({nframes/fps:.2f} seconds)")
        print(f"Clock  : {clock} Hz, FPS: {fps}")
        
    else:
        print(f"Error: Unsupported YM format '{header_id}'. Only YM5! and YM6! are supported for now.")
        return

    # --- Parse register data ---
    frames = []
    if interleaved:
        if offset + num_regs * nframes > len(data):
            print("Warning: File truncated, reducing frame count.")
            nframes = (len(data) - offset) // num_regs
        for i in range(nframes):
            frame_regs = [data[offset + r * nframes + i] for r in range(num_regs)]
            frames.append(frame_regs)
    else:
        print("Error: Non-interleaved YM format is not supported.")
        return

    # --- Initialize PSG Emulator ---
    sample_rate = 44100
    channels = 1
    
    if engine == "cap32":
        print(f"Initializing PSG: Caprice32 (AY-3-8912), Clock={clock} Hz")
        psg = ay.ay8912_cap32(clock, sample_rate)
        # Standard CPC stereo mix: A=Left, B=Center, C=Right
        psg.set_stereo_mix(255, 13, 170, 170, 13, 255)
        channels = 2
    else:
        print(f"Initializing PSG: MAME (YM2149), Clock={clock} Hz")
        psg = ay.ay8910(ay.psg_type.PSG_TYPE_YM, clock, 1, 0)
        # Configuration Flags:
        # 0x01: AY8910_LEGACY_OUTPUT (Normalize 0..1)
        # 0x02: AY8910_SINGLE_OUTPUT (Internal MAME Mono Mixing)
        psg.set_flags(0x01 | 0x02)
        psg.start()
        channels = 1
    
    psg.reset()

    if live_play:
        # --- Live Playback using sounddevice ---
        print(f"\nPlaying live ({'Stereo' if channels == 2 else 'Mono'})... Press Ctrl+C to stop.")
        
        def callback(outdata, frames_to_gen, time_info, status):
            if status:
                print(status, file=sys.stderr)
            
            if engine == "cap32":
                chunk = psg.generate(frames_to_gen)
            else:
                chunk = psg.generate(frames_to_gen, sample_rate)

            if len(chunk) // channels < frames_to_gen:
                chunk.extend([0] * (frames_to_gen * channels - len(chunk)))

            outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, channels)

        try:
            with sd.OutputStream(samplerate=sample_rate, channels=channels, dtype='int16', callback=callback):
                for i in range(nframes):
                    frame = frames[i]
                    for r in range(14):
                        psg.address_w(r)
                        psg.data_w(frame[r])
                    
                    # The callback handles generation, we just need to wait
                    time.sleep(1.0 / fps)
        except KeyboardInterrupt:
            print("\nPlayback stopped.")
        except Exception as e:
            print(f"\nAn error occurred during playback: {e}")
            
    else:
        # --- Render to File ---
        print(f"\nRendering audio to file ({'Stereo' if channels == 2 else 'Mono'})...")
        all_samples = []
        
        for i in range(nframes):
            frame = frames[i]
            for r in range(14):
                psg.address_w(r)
                psg.data_w(frame[r])
            
            # Use floating point math to keep track of total samples needed up to this frame
            target_total_samples = int((i + 1) * sample_rate / fps)
            samples_to_generate = target_total_samples - (len(all_samples) // channels)
            
            if samples_to_generate > 0:
                if engine == "cap32":
                    chunk = psg.generate(samples_to_generate)
                else:
                    chunk = psg.generate(samples_to_generate, sample_rate)
                all_samples.extend(chunk)
            
            if i % 100 == 0:
                print(f"Progress: {i}/{nframes} frames", end='\r')
                
        print("\nRendering done!")

        print(f"Writing to {output_wav}...")
        with wave.open(output_wav, 'wb') as f:
            f.setnchannels(channels)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            packed = struct.pack('<' + 'h' * len(all_samples), *all_samples)
            f.writeframes(packed)

def main():
    parser = argparse.ArgumentParser(description="Play or render an AY/YM chiptune file.")
    parser.add_argument("input_file", help="Path to the .ym file.")
    parser.add_argument("-p", "--play", action="store_true", help="Play the file live instead of rendering to WAV.")
    parser.add_argument("-o", "--output", default="output_ym.wav", help="Output WAV file name (default: output_ym.wav).")
    parser.add_argument("--mame", action="store_true", help="Use the MAME emulation engine (mono) instead of Caprice32 (stereo).")
    
    args = parser.parse_args()
    
    engine = "mame" if args.mame else "cap32"
    
    play_ym(args.input_file, args.output, args.play, engine)

if __name__ == "__main__":
    main()
