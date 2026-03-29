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

def play_ym(filename, output_wav, live_play):
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

    # --- Initialize AY8910 Emulator ---
    sample_rate = 44100
    if clock < 1000000 or clock > 4000000:
        print(f"Warning: Bizarre clock rate ({clock} Hz) detected. Forcing 2 MHz.")
        clock = 2000000

    psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, clock, 1, 0)
    psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
    psg.start()
    psg.reset()

    if live_play:
        # --- Live Playback using sounddevice ---
        print("\nPlaying live... Press Ctrl+C to stop.")
        
        def callback(outdata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            
            chunk = psg.generate(frames, sample_rate)
            if len(chunk) < frames:
                chunk.extend([0] * (frames - len(chunk)))

            outdata[:] = np.array(chunk, dtype=np.int16).reshape(-1, 1)

        try:
            with sd.OutputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=callback):
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
        print("\nRendering audio to file...")
        total_samples = int((nframes / fps) * sample_rate)
        all_samples = psg.generate(total_samples, sample_rate)
                
        print("Rendering done!")

        print(f"Writing to {output_wav}...")
        with wave.open(output_wav, 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            packed = struct.pack('<' + 'h' * len(all_samples), *all_samples)
            f.writeframes(packed)

def main():
    parser = argparse.ArgumentParser(description="Play or render an AY/YM chiptune file.")
    parser.add_argument("input_file", help="Path to the .ym file.")
    parser.add_argument("-p", "--play", action="store_true", help="Play the file live instead of rendering to WAV.")
    parser.add_argument("-o", "--output", default="output_ym.wav", help="Output WAV file name (default: output_ym.wav).")
    
    args = parser.parse_args()
    
    play_ym(args.input_file, args.output, args.play)

if __name__ == "__main__":
    main()
