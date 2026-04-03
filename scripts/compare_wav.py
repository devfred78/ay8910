import sys
import os

def compare_files(file1, file2, max_diffs=10):
    size1 = os.path.getsize(file1)
    size2 = os.path.getsize(file2)
    
    print(f"Fichier 1: {file1} ({size1} octets)")
    print(f"Fichier 2: {file2} ({size2} octets)")
    
    if size1 != size2:
        print(f"ATTENTION: Les tailles diffèrent de {abs(size1 - size2)} octets")
    
    diff_count = 0
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        chunk_size = 4096
        offset = 0
        while True:
            b1 = f1.read(chunk_size)
            b2 = f2.read(chunk_size)
            
            if not b1 and not b2:
                break
            
            # Comparer les octets disponibles
            limit = min(len(b1), len(b2))
            for i in range(limit):
                if b1[i] != b2[i]:
                    if diff_count < max_diffs:
                        print(f"Différence à l'offset {offset + i:08X}: F1={b1[i]:02X}, F2={b2[i]:02X}")
                    diff_count += 1
            
            # Gérer le cas où un fichier est plus court
            if len(b1) != len(b2):
                extra = abs(len(b1) - len(b2))
                print(f"Fin de flux à l'offset {offset + limit:08X}. {extra} octets restants dans le fichier le plus long.")
                diff_count += extra
                break
                
            offset += len(b1)
            
    if diff_count == 0:
        print("Les fichiers sont identiques.")
    else:
        print(f"Nombre total de différences: {diff_count}")

if __name__ == "__main__":
    f1 = r"YM example files\Deflektor_GOOD_MONO_no_metadata.wav"
    f2 = r"YM example files\Deflektor_output_FINAL_V6.wav"
    compare_files(f1, f2)
