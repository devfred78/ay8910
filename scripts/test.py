import ay8910_wrapper as ay
import wave
import struct
import math

def write_wav(filename, samples, sample_rate):
    """Writes a list of samples to a WAV file."""
    with wave.open(filename, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)  # 2 bytes = 16-bit samples
        f.setframerate(sample_rate)
        packed_samples = struct.pack('<' + 'h' * len(samples), *samples)
        f.writeframes(packed_samples)

def play_sync(psg, clock, freq_trumpet, freq_piano, duration_sec, sample_rate):
    """
    Plays two notes synchronously:
    - Channel A: Trumpet (ADSR + Vibrato) - Muted in this version
    - Channel B: Piano (Percussive Attack + Decay, No Vibrato)
    """
    chunk_duration = 0.01 # Update the chip every 10ms
    num_chunks = int(duration_sec / chunk_duration)
    all_samples = []
    
    # --- Trumpet Params (Channel A) ---
    t_atk = 0.05
    t_dec = 0.10
    t_sus = 11.0
    t_rel = 0.08
    if duration_sec < t_atk + t_rel:
        t_atk = duration_sec * 0.4
        t_rel = duration_sec * 0.4

    t_period = int(clock / (16 * freq_trumpet)) if freq_trumpet > 0 else 0
    t_period = max(1, min(4095, t_period)) if t_period > 0 else 0

    # --- Piano Params (Channel B) ---
    p_atk = 0.01  # Frappe immédiate du marteau
    p_dec = 1.5   # Le son résonne et s'atténue lentement
    p_rel = 0.05  # Relâchement de la touche (étouffoir)
    if duration_sec < p_atk + p_rel:
        p_atk = duration_sec * 0.1
        p_rel = duration_sec * 0.4

    p_period = int(clock / (16 * freq_piano)) if freq_piano > 0 else 0
    p_period = max(1, min(4095, p_period)) if p_period > 0 else 0

    # Main update loop
    for i in range(num_chunks):
        t = i * chunk_duration
        
        # --- 1. Update Trumpet (Voie A) --- MUTE
        psg.address_w(8)
        psg.data_w(0)

        # --- 2. Update Piano (Voie B) ---
        if freq_piano > 0:
            # Volume
            if t < p_atk:
                p_vol = 15.0 * (t / p_atk)
            elif t < duration_sec - p_rel:
                # Le piano n'a pas de sustain, il s'atténue en permanence
                p_vol = 15.0 * max(0.0, 1.0 - (t - p_atk) / p_dec)
            else:
                # La touche est relâchée
                lvl = 15.0 * max(0.0, 1.0 - (duration_sec - p_rel - p_atk) / p_dec)
                p_vol = lvl * ((duration_sec - t) / p_rel)
                
            p_vol_int = max(0, min(15, int(p_vol)))
            psg.address_w(9)
            psg.data_w(p_vol_int)
            
            # Pas de vibrato pour le piano
            psg.address_w(2)
            psg.data_w(p_period & 0xFF)
            psg.address_w(3)
            psg.data_w((p_period >> 8) & 0x0F)
        else:
            psg.address_w(9)
            psg.data_w(0)
            
        # Générer les échantillons pour cette tranche de 10ms
        chunk_samples = int(sample_rate * chunk_duration)
        all_samples.extend(psg.generate(chunk_samples, sample_rate))

    # Silence final
    generated_duration = num_chunks * chunk_duration
    remainder = duration_sec - generated_duration
    if remainder > 0:
        psg.address_w(8)
        psg.data_w(0)
        psg.address_w(9)
        psg.data_w(0)
        all_samples.extend(psg.generate(int(sample_rate * remainder), sample_rate))

    return all_samples

def main():
    print("Initializing AY-3-8910 emulator...")

    clock = 2000000  # 2 MHz
    sample_rate = 44100

    psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, clock, 1, 0)
    psg.set_flags(ay.AY8910_LEGACY_OUTPUT)
    psg.start()
    psg.reset()

    # Mixer: Enable Tone on Channel A and B, disable everything else
    psg.address_w(7)
    psg.data_w(0b00111100)

    # --- Dictionary of note frequencies (Hz) ---
    N = {
        'F2': 87.31,  'G2': 98.00,  'A2': 110.00, 'B2': 123.47,
        'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
        'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00,
        'REST': 0
    }

    bpm = 120
    q = 60.0 / bpm
    e = q / 2.0
    h = q * 2.0

    # Sequence of (Trumpet Melody, Piano Accompaniment, Duration)
    # Dans cette version, la mélodie principale est sur le canal du piano
    song = [
        # Anacrouse
        (N['REST'], N['G4'], e),
        (N['REST'], N['G4'], e),
        
        # Mesure 1
        (N['REST'], N['A4'], q),
        (N['REST'], N['G4'], q),
        (N['REST'], N['C5'], q),
        
        # Mesure 2
        (N['REST'], N['B4'], h),
        (N['REST'], N['G4'], e),
        (N['REST'], N['G4'], e),
        
        # Mesure 3
        (N['REST'], N['A4'], q),
        (N['REST'], N['G4'], q),
        (N['REST'], N['D5'], q),
        
        # Mesure 4
        (N['REST'], N['C5'], h),
        (N['REST'], N['G4'], e),
        (N['REST'], N['G4'], e),
        
        # Mesure 5
        (N['REST'], N['G5'], q),
        (N['REST'], N['E5'], q),
        (N['REST'], N['C5'], q),
        
        # Mesure 6
        (N['REST'], N['B4'], q),
        (N['REST'], N['A4'], q),
        (N['REST'], N['F5'], e),
        (N['REST'], N['F5'], e),
        
        # Mesure 7
        (N['REST'], N['E5'], q),
        (N['REST'], N['C5'], q),
        (N['REST'], N['D5'], q),
        
        # Mesure 8
        (N['REST'], N['C5'], h)
    ]

    print("Generating Piano solo...")
    all_samples = []
    
    for note_trump, note_piano, duration in song:
        all_samples.extend(play_sync(psg, clock, note_trump, note_piano, duration, sample_rate))

    # Add a final bit of silence
    all_samples.extend(play_sync(psg, clock, 0, 0, 1.0, sample_rate))

    print(f"Audio generation complete. Total samples: {len(all_samples)}")

    if all_samples:
        output_filename = "output_python.wav"
        write_wav(output_filename, all_samples, sample_rate)
        print(f"Output written to {output_filename}")

if __name__ == "__main__":
    main()
