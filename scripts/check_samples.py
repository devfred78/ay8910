import wave
import struct

def read_first_samples(path, count=1000):
    print(f"\nPremiers échantillons de {path} (valeurs brutes) :")
    try:
        with wave.open(path, 'rb') as w:
            frames = w.readframes(count)
            fmt = "<" + "h" * (len(frames) // 2)
            samples = struct.unpack(fmt, frames)
            # Afficher les 20 premières valeurs
            print(samples[:20])
            # Calculer la moyenne des 100 premiers
            avg = sum(samples[:100]) / 100
            print(f"Moyenne des 100 premiers: {avg:.2f}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_first_samples(r"YM example files\Deflektor_GOOD_MONO_no_metadata.wav")
    read_first_samples(r"YM example files\Deflektor_output_FINAL_V6_recalc.wav")
