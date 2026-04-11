import ay8910_wrapper
import numpy as np

def test_ay_emul31():
    print("Testing ay_emul31 wrapper...")
    chip = ay8910_wrapper.ay_emul31()
    
    # Configurer un son simple : Canal A, Ton 440 Hz approx
    # Clock = 1.75 MHz, Period = Clock / (16 * Freq) = 1750000 / (16 * 440) approx 248
    period = 248
    chip.set_register(0, period & 0xFF) # Fine
    chip.set_register(1, (period >> 8) & 0x0F) # Coarse
    
    chip.set_register(7, 0x3E) # Mixer : Tone A ON, others OFF
    chip.set_register(8, 15)   # Amplitude A : Max
    
    # Générer 1000 échantillons à 44100 Hz
    samples = chip.generate(1000, 1750000, 44100)
    
    print(f"Generated {len(samples)} samples.")
    print(f"First 10 samples: {samples[:10]}")
    
    # Vérifier s'il y a du signal (pas que des zéros)
    has_signal = any(s != 0 for s in samples)
    print(f"Signal detected: {has_signal}")
    
    if has_signal:
        print("SUCCESS: ay_emul31 is working!")
    else:
        print("FAILURE: No signal detected.")

if __name__ == "__main__":
    test_ay_emul31()
