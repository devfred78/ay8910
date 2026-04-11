
import ay8910_wrapper as ay
import numpy as np

def test_mame_output():
    # Test avec les réglages qui posent problème
    psg = ay.ay8910(ay.psg_type.PSG_TYPE_AY, 2000000, 1, 0)
    print("Moteur MAME initialisé.")
    
    # Mode haute fidélité
    psg.set_flags(ay.AY8910_SINGLE_OUTPUT | ay.AY8910_RESISTOR_OUTPUT)
    if hasattr(psg, 'set_resistors_load'):
        psg.set_resistors_load(1000, 1000, 1000)
    
    psg.start()
    psg.reset()
    
    # Activer un son simple : Canal A, fréquence ~440Hz (2000000 / (16 * 284) ~= 440)
    # Registre 0-1 : Période (284 = 0x011C)
    psg.set_register(0, 0x1C)
    psg.set_register(1, 0x01)
    # Registre 7 : Mixer (Bit 0 à 0 pour activer Tone A)
    psg.set_register(7, 0x3E)
    # Registre 8 : Volume A (15 = Max)
    psg.set_register(8, 15)
    
    # Générer beaucoup plus d'échantillons pour voir l'onde (440Hz à 44100Hz -> ~100 échantillons par cycle)
    samples = psg.generate(2000, 44100)
    print(f"Premiers 10 échantillons : {samples[:10]}")
    print(f"Valeur min : {min(samples)}, max : {max(samples)}")
    
    # Vérifier s'il y a du mouvement (plus d'une valeur unique)
    unique_vals = set(samples)
    print(f"Nombre de valeurs uniques : {len(unique_vals)}")
    
    # Test sans RESISTOR_OUTPUT pour comparer
    psg2 = ay.ay8910(ay.psg_type.PSG_TYPE_AY, 2000000, 1, 0)
    psg2.set_flags(ay.AY8910_SINGLE_OUTPUT) # Pas de RESISTOR_OUTPUT
    psg2.start()
    psg2.reset()
    psg2.set_register(0, 0x1C)
    psg2.set_register(1, 0x01)
    psg2.set_register(7, 0x3E)
    psg2.set_register(8, 15)
    
    samples2 = psg2.generate(100, 44100)
    print(f"\nSans RESISTOR_OUTPUT :")
    print(f"Premiers 10 échantillons : {samples2[:10]}")
    print(f"Valeur min : {min(samples2)}, max : {max(samples2)}")

if __name__ == "__main__":
    test_mame_output()
