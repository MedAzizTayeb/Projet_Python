from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256

def encrypt(msg, pub_path):
    """
    Encrypt message using recipient's public key (RSA)
    """
    with open(pub_path, 'r') as f:
        pub_key = RSA.import_key(f.read())
    
    cipher = PKCS1_OAEP.new(pub_key, hashAlgo=SHA256)
    encrypted = cipher.encrypt(msg.encode('utf-8'))
    
    return encrypted

def decrypt(cipher_text, priv_path):
    """
    Decrypt message using own private key (RSA)
    """
    with open(priv_path, 'r') as f:
        priv_key = RSA.import_key(f.read())
    
    cipher = PKCS1_OAEP.new(priv_key, hashAlgo=SHA256)
    decrypted = cipher.decrypt(cipher_text)
    
    return decrypted.decode('utf-8')