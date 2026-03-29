import struct
import sys
import os
import wave
import ay8910_wrapper as ay

# We need to add the lhafile library to handle compressed .ym files
try:
    import lhafile
except ImportError:
    print("ERROR: The 'lhafile' library is not installed.", file=sys.stderr)
    print("Please install it by running: pip install lhafile", file=sys.stderr)
    sys.exit(1)

def read_nt_string(data, offset):
    """Reads a null-terminated string from bytes."""
    end = data.find(b'\0', offset)
    if end == -1:
        return "", len(data)
    return data[offset:end].decode('latin-1', 'ignore'), end + 1

def play_ym(filename, output_wav):
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
            
            # Find the largest file in the archive, which is almost always the music data.
            best_candidate = None
            max_size = -1
            for info in lha_archive.infolist():
                if info.file_size > max_size:
                    max_size = info.file_size
                    best_candidate = info.filename
            
            if best_candidate:
                print(f"Extracting '{best_candidate}' from archive...")
                data = lha_archive.read(best_candidate)
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
            print("Error: Invalid YM5/YM6 signature (LeOnArD! not found).")
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
        
        # Skip digidrums
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
        
    elif header_id == b'YM3b':
        interleaved = True
        offset = 4
        num_regs = 14
        nframes = (len(data) - 4) // 14
        print(f"Format : YM3b")
        print(f"Frames : {nframes} ({nframes/fps:.2f} seconds)")
        
    else:
        print(f"Error: Unsupported YM format '{header_id}'.")
        return

    # --- Parse register data ---
    frames = []
    
    if interleaved:
        if offset + num_regs * nframes > len(data):
            print("Warning: File truncated, reducing frame count.")
            nframes = (len(data) - offset) // num_regs

        for i in range(nframes):
            frame_regs = []
            for r in range(num_regs):
                val = data[offset + r * nframes + i]
                frame_regs.append(val)
            frames.append(frame_regs)
    else:
        if offset + num_regs * nframes > len(data):
            nframes = (len(data) - offset) // num_regs
            
        for i in range(nframes):
            frame_regs = list(data[offset + i * num_regs : offset + (i+1) * num_regs])
            frames.append(frame_regs)

    # --- Initialize AY8910 Emulator ---
    sample_rate = 44100
    
    if clock < 1000000 or clock > 4000000:
        print(f"Warning: Bizarre clock rate ({clock} Hz) detected. Forcing 2 MHz.")
        clock = 2000000

    psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, clock, 1, 0)
    psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
    psg.start()
    psg.reset()

    # --- Render Audio ---
    print("\nRendering audio...")
    samples_per_frame = sample_rate / fps
    all_samples = []
    
    sample_accumulator = 0.0

    for i in range(nframes):
        frame = frames[i]
        
        for r in range(14):
            psg.address_w(r)
            psg.data_w(frame[r])
            
        sample_accumulator += samples_per_frame
        samples_to_generate = int(sample_accumulator)
        sample_accumulator -= samples_to_generate
        
        if samples_to_generate > 0:
            all_samples.extend(psg.generate(samples_to_generate, sample_rate))
            
        if i % fps == 0:
            sys.stdout.write(f"\rProgress: {i//fps}s / {nframes//fps}s")
            sys.stdout.flush()
            
    print(f"\rProgress: {nframes//fps}s / {nframes//fps}s")
    print("Rendering done!")

    # --- Write WAV file ---
    print(f"Writing to {output_wav}...")
    with wave.open(output_wav, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        packed = struct.pack('<' + 'h' * len(all_samples), *all_samples)
        f.writeframes(packed)
        
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ym_player.py <song.ym> [output.wav]")
        print("Example: python3 ym_player.py my_music.ym")
    else:
        ym_file = sys.argv[1]
        wav_file = sys.argv[2] if len(sys.argv) > 2 else "output_ym.wav"
        play_ym(ym_file, wav_file)

if __name__ == "__main__":
    main()
