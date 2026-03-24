"""
Encrypts malware samples at rest using Fernet (AES-128-CBC + HMAC-SHA256).
Files are stored as <original>.enc on disk.  Decryption happens in memory
only at request time - plaintext never touches the filesystem again.
"""
import os, io
from cryptography.fernet import Fernet

ENC_SUFFIX = '.enc'
_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'data', '.secret.key')
_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if os.path.exists(_KEY_FILE):
            key = open(_KEY_FILE, 'rb').read().strip()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(_KEY_FILE), exist_ok=True)
            open(_KEY_FILE, 'wb').write(key)
        _fernet = Fernet(key)
    return _fernet


def encrypt_file(src_path: str, delete_original: bool = True) -> str:
    """Encrypt src_path -> src_path.enc and optionally remove the original."""
    data = open(src_path, 'rb').read()
    enc_path = src_path + ENC_SUFFIX
    open(enc_path, 'wb').write(_get_fernet().encrypt(data))
    if delete_original:
        os.remove(src_path)
    return enc_path


def decrypt_to_bytes(enc_path: str) -> io.BytesIO:
    """Decrypt enc_path -> BytesIO (never written to disk)."""
    buf = io.BytesIO(_get_fernet().decrypt(open(enc_path, 'rb').read()))
    buf.seek(0)
    return buf


def find_enc(file_path: str):
    """Return file_path.enc if it exists, else None."""
    enc = file_path + ENC_SUFFIX
    return enc if os.path.exists(enc) else None
