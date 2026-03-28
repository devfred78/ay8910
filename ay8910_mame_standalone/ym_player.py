import struct
import sys
import os
import wave
import ay8910_standalone as ay

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

    # Check for LHA compression signature
    # Most .ym files downloaded from the internet are actually LHA archives
    if len(data) > 6 and b'-lh' in data[2:6]:
        print("\n" + "="*60)
        print(f" ERROR: The file '{filename}' is LHA compressed!")
        print("="*60)
        print(" Most .ym files from the internet are LHA archives renamed to .ym.")
        print(" Please extract it using 7-Zip, WinRAR, or an LHA unarchiver first.")
        print(" Once extracted, run this script on the uncompressed file.")
        print("="*60 + "\n")
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
        
        # Skip digidrums (Not supported in this basic player)
        for _ in range(ndigidrums):
            size = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4 + size
            
        # Read metadata strings
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
        print(f"Error: Unsupported YM format '{header_id}'. Only YM3b, YM5! and YM6! are supported.")
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
    
    # Check if clock is bizarre, default to 2MHz if so
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
    
    # We use a fractional accumulator to handle non-integer samples per frame (e.g. 44100 / 50 = 882)
    sample_accumulator = 0.0

    for i in range(nframes):
        frame = frames[i]
        
        # Write to AY-3-8910 registers 0 to 13 
        # (14 and 15 are IO ports, usually not needed for sound)
        for r in range(14):
            psg.address_w(r)
            psg.data_w(frame[r])
            
        # Calculate exactly how many samples to generate for this specific frame
        sample_accumulator += samples_per_frame
        samples_to_generate = int(sample_accumulator)
        sample_accumulator -= samples_to_generate
        
        if samples_to_generate > 0:
            all_samples.extend(psg.generate(samples_to_generate, sample_rate))
            
        # Update progress bar
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
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ym_player.py <song.ym> [output.wav]")
        print("Example: python3 ym_player.py my_music.ym")
    else:
        ym_file = sys.argv[1]
        wav_file = sys.argv[2] if len(sys.argv) > 2 else "output_ym.wav"
        play_ym(ym_file, wav_file)
