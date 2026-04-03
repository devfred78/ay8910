import wave
import struct
import sys

def analyze_wav(path):
    print(f"\nAnalyse de {path} :")
    try:
        with wave.open(path, 'rb') as w:
            params = w.getparams()
            print(f"  Canaux      : {params.nchannels}")
            print(f"  Largeur éch.: {params.sampwidth} octets ({params.sampwidth*8} bits)")
            print(f"  Fréquence   : {params.framerate} Hz")
            print(f"  Nombre frames: {params.nframes}")
            duration = params.nframes / params.framerate
            print(f"  Durée       : {duration:.2f} s")
            
            # Analyse statistique sur un segment de 5 secondes au milieu
            w.setpos(params.framerate * 30) # 30s
            n_frames = params.framerate * 5
            frames = w.readframes(n_frames)
            if params.sampwidth == 2:
                fmt = "<" + "h" * (len(frames) // 2)
                samples = struct.unpack(fmt, frames)
                if params.nchannels == 2:
                    samples_l = samples[::2]
                    samples_r = samples[1::2]
                    print(f"  Stéréo détecté.")
                    print(f"  Amplitude max (L/R): {max(abs(min(samples_l)), max(samples_l))} / {max(abs(min(samples_r)), max(samples_r))}")
                    samples = samples_l # Travailler sur L pour la suite
                else:
                    print(f"  Mono détecté.")
                    print(f"  Amplitude max: {max(abs(min(samples)), max(samples))}")
                
                # Moyenne (DC offset)
                avg = sum(samples) / len(samples)
                print(f"  Valeur moyenne (DC): {avg:.2f}")

                # Passages par zéro pour fréquence dominante
                last_s = samples[0]
                crossings = []
                for i in range(1, len(samples)):
                    if (last_s <= 0 and samples[i] > 0):
                        crossings.append(i)
                    last_s = samples[i]
                
                if len(crossings) >= 2:
                    freq = (len(crossings)-1) * params.framerate / (crossings[-1] - crossings[0])
                    print(f"  Fréquence dominante estimée: {freq:.2f} Hz")
    except Exception as e:
        print(f"  Erreur : {e}")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        analyze_wav(arg)
    if len(sys.argv) == 1:
        analyze_wav("YM example files/Deflektor_GOOD.wav")
        analyze_wav("YM example files/Deflektor_output.wav")
