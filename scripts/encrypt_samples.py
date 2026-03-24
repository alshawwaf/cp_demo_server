#!/usr/bin/env python3
"""One-time migration: encrypt all files in app/data/malware_samples/"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.crypto_util import encrypt_file, ENC_SUFFIX

SAMPLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'app', 'data', 'malware_samples')

def main():
    for root, _, files in os.walk(SAMPLES_DIR):
        for fname in files:
            if fname.endswith(ENC_SUFFIX):
                continue
            src = os.path.join(root, fname)
            enc = encrypt_file(src, delete_original=True)
            print(f'Encrypted: {src} -> {enc}')
    print('Done. Key stored at app/data/.secret.key')

if __name__ == '__main__':
    main()
