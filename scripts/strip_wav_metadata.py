import wave
import sys
import os

def strip_metadata(input_path, output_path):
    print(f"Reading {input_path}...")
    try:
        with wave.open(input_path, 'rb') as w_in:
            params = w_in.getparams()
            print(f"Parameters: {params}")
            frames = w_in.readframes(params.nframes)
            
        print(f"Writing to {output_path}...")
        with wave.open(output_path, 'wb') as w_out:
            # Keep only essential parameters: nchannels, sampwidth, framerate
            # nframes will be calculated automatically on close
            # comptype, compname are 'NONE' and 'not compressed' by default
            w_out.setnchannels(params.nchannels)
            w_out.setsampwidth(params.sampwidth)
            w_out.setframerate(params.framerate)
            w_out.writeframes(frames)
            
        print("Done. Metadata stripped.")
        
        in_size = os.path.getsize(input_path)
        out_size = os.path.getsize(output_path)
        print(f"Original size: {in_size} bytes")
        print(f"New size:      {out_size} bytes")
        print(f"Difference:    {in_size - out_size} bytes")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    input_file = r"YM example files\Deflektor_GOOD_MONO.wav"
    output_file = r"YM example files\Deflektor_GOOD_MONO_no_metadata.wav"
    strip_metadata(input_file, output_file)
