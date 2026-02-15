"""
安全与加密工具：密码哈希
"""
import os
import binascii
import hashlib

def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    if salt_hex is None:
        salt = os.urandom(16)
        salt_hex = binascii.hexlify(salt).decode("utf-8")
    else:
        salt = binascii.unhexlify(salt_hex.encode("utf-8"))
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return h, salt_hex
