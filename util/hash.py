from hashlib import pbkdf2_hmac
from random import getrandbits


def random_salt():
    return getrandbits(128).to_bytes(16, byteorder='little').hex()


def hash_pbkdf2(x, salt):
    return pbkdf2_hmac('sha256', x.encode('utf-8'), bytes.fromhex(salt), 100000).hex()
