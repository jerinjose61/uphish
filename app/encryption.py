from uphish.settings import BASE_DIR
import base64, json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

with open(str(BASE_DIR)+'/settings.json',"r") as infile:
    settings_dict = json.loads(infile.read())

# Function to generate encryption key from Django SECRET_KEY
def generate_key():
    password_provided = settings_dict['SECRET_KEY']
    password = password_provided.encode()  # Convert to type bytes

    # Salt should always be the same. Else the generated key will be different everytime
    salt = b'\xa5\xaa\x88Ey\xb9[\xb8\x05 \x07J\xd5\x1a\nL'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    key = base64.urlsafe_b64encode(kdf.derive(password))  # Can only use kdf once

    return key

def encrypt(plaintext, key):
    f = Fernet(key)
    encrypted = f.encrypt(plaintext)

    return encrypted

def decrypt(encrypted, key):
    f = Fernet(key)
    decrypted = f.decrypt(encrypted)

    return decrypted
