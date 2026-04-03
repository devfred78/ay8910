import ay8910_wrapper as ay
import wave
import struct
import numpy as np

def generate_tone_mame(clock, sr, freq, duration):
    psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, clock, 1, 0)
    psg.set_flags(ay.AY8910_LEGACY_OUTPUT | ay.AY8910_SINGLE_OUTPUT)
    psg.start()
    psg.reset()
    
    # Enable Tone A
    psg.address_w(7)
    psg.data_w(0b00111110)
    
    # MAME logic: period = clock / (16 * freq)
    period = int(clock / (16 * freq))
    psg.address_w(0)
    psg.data_w(period & 0xFF)
    psg.address_w(1)
    psg.data_w((period >> 8) & 0x0F)
    
    psg.address_w(8)
    psg.data_w(15)
    
    samples = psg.generate(sr * duration, sr)
    return samples

def generate_tone_cap32(clock, sr, freq, duration):
    psg = ay.ay8912_cap32(clock, sr)
    psg.reset()
    
    # Enable Tone A
    psg.address_w(7)
    psg.data_w(0b00111110)
    
    # Caprice32 logic: TonA is period in 1/8 ticks?
    # Actually step_logic increments ton_count every tick.
    # Logic runs at clock/8.
    # So if clock=1MHz, logic=125kHz.
    # period = (clock/8) / (2 * freq) ?
    period = int((clock/8) / (2 * freq))
    
    psg.address_w(0)
    psg.data_w(period & 0xFF)
    psg.address_w(1)
    psg.data_w((period >> 8) & 0x0F)
    
    psg.address_w(8)
    psg.data_w(15)
    
    samples_stereo = psg.generate(sr * duration)
    # Convert to mono for comparison
    samples_mono = []
    for i in range(0, len(samples_stereo), 2):
        samples_mono.append((samples_stereo[i] + samples_stereo[i+1]) // 2)
    return samples_mono

def save_wav(filename, samples, sr):
    with wave.open(filename, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

if __name__ == "__main__":
    clock = 1000000
    sr = 44100
    freq = 440
    duration = 2
    
    print("Generating MAME tone...")
    mame = generate_tone_mame(clock, sr, freq, duration)
    save_wav("test_mame.wav", mame, sr)
    
    print("Generating Caprice32 tone...")
    cap32 = generate_tone_cap32(clock, sr, freq, duration)
    save_wav("test_cap32.wav", cap32, sr)
    
    print("Done. Compare test_mame.wav and test_cap32.wav")
