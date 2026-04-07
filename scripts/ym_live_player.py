"""
Live YM file player using the .play() API.

This script demonstrates how to use the high-level playback API added to the
emulator classes in the ay8910_wrapper package.
"""
import argparse
import struct
import time

import ay8910_wrapper as ay

# Try to import lhafile for compressed .ym files
try:
    import lhafile
except ImportError:
    lhafile = None

from typing import Tuple

def read_nt_string(data: bytes, offset: int) -> Tuple[str, int]:
    """
    Reads a null-terminated string from bytes.

    Args:
        data: Byte array to read from.
        offset: Initial offset.

    Returns:
        The decoded string and the next offset.
    """
    end = data.find(b'\0', offset)
    if end == -1:
        return "", len(data)
    return data[offset:end].decode('latin-1', 'ignore'), end + 1

def play_ym_live(filename: str, engine: str = "cap32") -> None:
    """
    Plays a YM chiptune file in real-time.

    Args:
        filename: Path to the .ym file.
        engine: The engine to use ('cap32' or 'mame').
    """
    print(f"Playing {filename}...")
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find file '{filename}'.")
        return

    # Handle LHA compression
    if len(data) > 6 and b'-lh' in data[2:6]:
        if lhafile is None:
            print("Error: The file is compressed (LHA) but 'lhafile' is not installed.")
            print("Install it with: pip install lhafile")
            return
        
        print("LHA compression detected. Decompressing in memory...")
        try:
            lha_archive = lhafile.LhaFile(filename)
            best_candidate = max(lha_archive.infolist(), key=lambda f: f.file_size, default=None)
            if best_candidate:
                data = lha_archive.read(best_candidate.filename)
            else:
                print("Error: No valid file found in the LHA archive.")
                return
        except Exception as e:
            print(f"Error during LHA decompression: {e}")
            return

    header_id = data[0:4]
    if header_id not in (b'YM5!', b'YM6!'):
        print(f"Error: Unsupported YM format '{header_id}'. Only YM5! and YM6! are supported.")
        return

    # Parsing the YM header
    nframes = struct.unpack('>I', data[12:16])[0]
    attributes = struct.unpack('>I', data[16:20])[0]
    interleaved = (attributes & 1) != 0
    ndigidrums = struct.unpack('>H', data[20:22])[0]
    clock = struct.unpack('>I', data[22:26])[0]
    fps = struct.unpack('>H', data[26:28])[0]
    
    offset = 34
    for _ in range(ndigidrums):
        size = struct.unpack('>I', data[offset:offset+4])[0]
        offset += 4 + size
        
    song_name, offset = read_nt_string(data, offset)
    author, offset = read_nt_string(data, offset)
    comment, offset = read_nt_string(data, offset)
    
    print(f"Title  : {song_name}")
    print(f"Author : {author}")
    print(f"Length : {nframes/fps:.2f} seconds ({fps} FPS)")

    # Register extraction
    if not interleaved:
        print("Error: Only interleaved format is supported.")
        return

    num_regs = 16
    frames = []
    if offset + num_regs * nframes > len(data):
        nframes = (len(data) - offset) // num_regs
        
    for i in range(nframes):
        frame_regs = [data[offset + r * nframes + i] for r in range(num_regs)]
        frames.append(frame_regs)

    # Initializing PSG with the new API
    sample_rate = 44100
    if engine == "cap32":
        psg = ay.ay8912_cap32(clock, sample_rate)
        psg.set_stereo_mix(255, 13, 170, 170, 13, 255)
    else:
        psg = ay.ay8910(ay.psg_type.PSG_TYPE_YM, clock, 1, 0)
        psg.set_flags(ay.AY8910_LEGACY_OUTPUT | ay.AY8910_SINGLE_OUTPUT)
        psg.start()

    psg.reset()
    
    # START LIVE PLAYBACK
    print("\nStarting live playback... Press Ctrl+C to stop.")
    psg.play(sample_rate)
    
    start_time = time.time()
    try:
        for i in range(nframes):
            frame = frames[i]
            # Update the 14 standard PSG registers
            for r in range(14):
                psg.set_register(r, frame[r])
            
            # Time synchronization
            next_frame_time = start_time + (i + 1) / fps
            sleep_time = next_frame_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
                
            if i % fps == 0:
                print(f"Time: {i//fps}s / {nframes//fps}s", end='\r')
                
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        psg.stop()
        print("\nPlayback finished.")

def main():
    parser = argparse.ArgumentParser(description="Live YM file player using the new .play() API")
    parser.add_argument("input_file", help="Path to the .ym file")
    parser.add_argument("--mame", action="store_true", help="Use MAME engine (mono) instead of Caprice32 (stereo)")
    