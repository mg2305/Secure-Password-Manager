from argon2 import PasswordHasher, low_level
from cryptography.fernet import Fernet
from database import *  # Imports database functions like getting metadata

import os
import base64
import secrets
import string

ph = PasswordHasher()

# Hashes the master password securely using Argon2
def hash_mp(masterPassword):
    return ph.hash(masterPassword)

# Verifies the entered master password against the stored hash
def verify_mp(masterPassword):
    try:
        ph.verify(get_MP_HASH(), masterPassword)
        return True
    except:
        return False

# Generates a random key file (default size: 32 bytes) and saves it to the given path
def gen_keyfile(keyfile_path, key_size=32):
    if os.path.isfile(keyfile_path):
        delete_keyfile(keyfile_path)  # Ensure old keyfile is removed

    try:
        os.makedirs(os.path.dirname(keyfile_path), exist_ok=True)  # Create directory if not exists
        key = os.urandom(key_size)  # Generate a random key
        with open(keyfile_path, "wb") as keyfile:
            keyfile.write(key)  # Save key to file
        return True
    except:
        return False

# Deletes the keyfile from the filesystem
def delete_keyfile(keyfile_path):
    try:
        os.remove(keyfile_path)
        return True
    except:
        return False

# Encrypts a token using the keyfile data
def encrypt_token(TOKEN, keyfile_path):
    with open(keyfile_path, "rb") as keyfile:
        key = keyfile.read()

    if len(key) != 32:
        return None  

    fernet_key = Fernet(base64.urlsafe_b64encode(key))
    encrypted_token = fernet_key.encrypt(TOKEN.encode())  
    return encrypted_token

# Decrypts the encrypted token using the keyfile data
def decrypt_token(keyfile_path, encrypted_token):
    with open(keyfile_path, "rb") as keyfile:
        key = keyfile.read()

    fernet_key = Fernet(base64.urlsafe_b64encode(key))
    decrypted_token = fernet_key.decrypt(encrypted_token)  
    return decrypted_token.decode()

# Verifies if the keyfile is correct by decrypting and comparing the token
def verify_keyfile(keyfile_path, TOKEN):
    try:
        return decrypt_token(keyfile_path, get_ENC_TOKEN()) == TOKEN
    except:
        return False

# Derives a 32-byte encryption key using the master password and keyfile (Argon2 raw hashing)
def derive_key(masterPassword, keyfile_path):
    try:
        with open(keyfile_path, "rb") as keyfile:
            keyfile_data = keyfile.read()

        combined_data = masterPassword.encode() + keyfile_data  

        salt = b"securePasswordManager"  

        derived_key = low_level.hash_secret_raw(
            secret=combined_data,
            salt=salt,
            time_cost=3,  
            memory_cost=65536,  
            parallelism=1,  
            hash_len=32,  
            type=low_level.Type.ID  
        )

        return derived_key
    except:
        return None

# Generates a random password with uppercase, lowercase, digits, and special characters
def get_random_password(length=20):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

# Encrypts a website password using the derived key
def encrypt_password(password, key):
    fernet_key = Fernet(base64.urlsafe_b64encode(key))
    encrypted_password = fernet_key.encrypt(password.encode())
    return encrypted_password

# Decrypts an encrypted website password using the derived key
def decrypt_password(encrypted_password, key):
    fernet_key = Fernet(base64.urlsafe_b64encode(key))
    decrypted_password = fernet_key.decrypt(encrypted_password).decode()
    return decrypted_password
