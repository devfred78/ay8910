import struct
import sys
import os
import ay8910_wrapper as ay
import time
import argparse

# Essayer d'importer lhafile pour les fichiers .ym compressés
try:
    import lhafile
except ImportError:
    lhafile = None

def read_nt_string(data, offset):
    """Lit une chaîne terminée par un caractère nul."""
    end = data.find(b'\0', offset)
    if end == -1:
        return "", len(data)
    return data[offset:end].decode('latin-1', 'ignore'), end + 1

def play_ym_live(filename, engine="cap32"):
    print(f"Lecture de {filename}...")
    try:
        with open(filename, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Erreur : Impossible de trouver le fichier '{filename}'.")
        return

    # Gestion de la compression LHA
    if len(data) > 6 and b'-lh' in data[2:6]:
        if lhafile is None:
            print("Erreur : Le fichier est compressé (LHA) mais 'lhafile' n'est pas installé.")
            print("Installez-le avec : pip install lhafile")
            return
        
        print("Compression LHA détectée. Décompression en mémoire...")
        try:
            lha_archive = lhafile.LhaFile(filename)
            best_candidate = max(lha_archive.infolist(), key=lambda f: f.file_size, default=None)
            if best_candidate:
                data = lha_archive.read(best_candidate.filename)
            else:
                print("Erreur : Aucun fichier valide dans l'archive LHA.")
                return
        except Exception as e:
            print(f"Erreur lors de la décompression LHA : {e}")
            return

    header_id = data[0:4]
    if header_id not in (b'YM5!', b'YM6!'):
        print(f"Erreur : Format YM '{header_id}' non supporté. Seuls YM5! et YM6! le sont.")
        return

    # Parsing du header YM
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
    
    print(f"Titre  : {song_name}")
    print(f"Auteur : {author}")
    print(f"Durée  : {nframes/fps:.2f} secondes ({fps} FPS)")

    # Extraction des registres
    if not interleaved:
        print("Erreur : Seul le format entrelacé est supporté.")
        return

    num_regs = 16
    frames = []
    if offset + num_regs * nframes > len(data):
        nframes = (len(data) - offset) // num_regs
        
    for i in range(nframes):
        frame_regs = [data[offset + r * nframes + i] for r in range(num_regs)]
        frames.append(frame_regs)

    # Initialisation du PSG avec la nouvelle API
    sample_rate = 44100
    if engine == "cap32":
        psg = ay.ay8912_cap32(clock, sample_rate)
        psg.set_stereo_mix(255, 13, 170, 170, 13, 255)
    else:
        psg = ay.ay8910(ay.psg_type.PSG_TYPE_YM, clock, 1, 0)
        psg.set_flags(ay.AY8910_LEGACY_OUTPUT | ay.AY8910_SINGLE_OUTPUT)
        psg.start()

    psg.reset()
    
    # DÉBUT DE LA LECTURE DIRECTE
    print("\nLancement de la lecture directe... Appuyez sur Ctrl+C pour arrêter.")
    psg.play(sample_rate)
    
    start_time = time.time()
    try:
        for i in range(nframes):
            frame = frames[i]
            # On met à jour les 14 registres standard du PSG
            for r in range(14):
                psg.set_register(r, frame[r])
            
            # Synchronisation temporelle
            next_frame_time = start_time + (i + 1) / fps
            sleep_time = next_frame_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
                
            if i % fps == 0:
                print(f"Temps : {i//fps}s / {nframes//fps}s", end='\r')
                
    except KeyboardInterrupt:
        print("\nArrêt par l'utilisateur.")
    finally:
        psg.stop()
        print("\nLecture terminée.")

def main():
    parser = argparse.ArgumentParser(description="Lecteur live de fichiers YM utilisant la nouvelle API .play()")
    parser.add_argument("input_file", help="Chemin vers le fichier .ym")
    parser.add_argument("--mame", action="store_true", help="Utiliser le moteur MAME (mono) au lieu de Caprice32 (stéréo)")
    
    args = parser.parse_args()
    engine = "mame" if args.mame else "cap32"
    
    play_ym_live(args.input_file, engine)

if __name__ == "__main__":
    main()
