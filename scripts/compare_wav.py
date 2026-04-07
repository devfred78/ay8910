import os


def compare_files(file1: str, file2: str, max_diffs: int = 10) -> None:
    size1 = os.path.getsize(file1)
    size2 = os.path.getsize(file2)
    
    print(f"File 1: {file1} ({size1} bytes)")
    print(f"File 2: {file2} ({size2} bytes)")
    
    if size1 != size2:
        print(f"WARNING: Sizes differ by {abs(size1 - size2)} bytes")
    
    diff_count = 0
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        chunk_size = 4096
        offset = 0
        while True:
            b1 = f1.read(chunk_size)
            b2 = f2.read(chunk_size)
            
            if not b1 and not b2:
                break
            
            # Compare available bytes
            limit = min(len(b1), len(b2))
            for i in range(limit):
                if b1[i] != b2[i]:
                    if diff_count < max_diffs:
                        print(f"Difference at offset {offset + i:08X}: F1={b1[i]:02X}, F2={b2[i]:02X}")
                    diff_count += 1
            
            # Handle case where one file is shorter
            if len(b1) != len(b2):
                extra = abs(len(b1) - len(b2))
                print(f"End of stream at offset {offset + limit:08X}. {extra} bytes remaining in the longest file.")
                diff_count += extra
                break
                
            offset += len(b1)
            
    if diff_count == 0:
        print("Files are identical.")
    else:
        print(f"Total number of differences: {diff_count}")

if __name__ == "__main__":
    f1 = r"YM example files\Deflektor_GOOD_MONO_no_metadata.wav"
    f2 = r"YM example files\Deflektor_output_FINAL_V6.wav"
    compare_files(f1, f2)
