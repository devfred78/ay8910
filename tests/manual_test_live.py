import ay8910_wrapper as ay
import sounddevice as sd
import numpy as np
import time

def test_live_audio():
    print("Test de lecture audio en direct (Caprice32) via nouvelle API...")
    sample_rate = 44100
    clock = 1000000 # 1 MHz
    
    psg = ay.ay8912_cap32(clock, sample_rate)
    psg.set_stereo_mix(255, 255, 255, 255, 255, 255) # Mono mix for simplicity
    
    # Nouvelle API
    psg.play(sample_rate)

    print("Jouer un son sur le canal A...")
    # Canal A: Period = 254 (approx 246 Hz @ 1MHz clock / 16 / 254)
    psg.set_register(0, 254 & 0xFF)
    psg.set_register(1, (254 >> 8) & 0x0F)
    psg.set_register(7, 0x3E) # Enable Tone A only (111110 binary)
    psg.set_register(8, 15)   # Volume max
    
    time.sleep(1)
    
    print("Changement de fréquence...")
    psg.set_register(0, 127 & 0xFF)
    psg.set_register(1, (127 >> 8) & 0x0F)
    
    time.sleep(1)
    
    print("Arrêt du son.")
    psg.stop()
    time.sleep(0.5)

if __name__ == "__main__":
    test_live_audio()
