from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256

def encrypt(msg, pub_path):
    """
    Encrypt message using recipient's public key
    
    Args:
        msg (str): Message to encrypt
        pub_path (str): Path to recipient's public key file
    
    Returns:
        bytes: Encrypted message
    """
    try:
        # Import public key
        with open(pub_path, 'r') as f:
            pub_key = RSA.import_key(f.read())
        
        # Create cipher with OAEP padding
        cipher = PKCS1_OAEP.new(pub_key, hashAlgo=SHA256)
        
        # Encrypt message
        encrypted = cipher.encrypt(msg.encode('utf-8'))
        
        return encrypted
    except Exception as e:
        raise Exception(f"Encryption failed: {e}")

def decrypt(cipher_text, priv_path):
    """
    Decrypt message using own private key
    
    Args:
        cipher_text (bytes): Encrypted message
        priv_path (str): Path to own private key file
    
    Returns:
        str: Decrypted message
    """
    try:
        # Import private key
        with open(priv_path, 'r') as f:
            priv_key = RSA.import_key(f.read())
        
        # Create cipher with OAEP padding
        cipher = PKCS1_OAEP.new(priv_key, hashAlgo=SHA256)
        
        # Decrypt message
        decrypted = cipher.decrypt(cipher_text)
        
        return decrypted.decode('utf-8')
    except Exception as e:
        raise Exception(f"Decryption failed: {e}")

def generate_rsa_keypair(key_size=2048):
    """
    Generate RSA key pair (alternative to OpenSSL)
    
    Args:
        key_size (int): Key size in bits (default 2048)
    
    Returns:
        tuple: (private_key, public_key) as PEM strings
    """
    key = RSA.generate(key_size)
    
    private_key = key.export_key('PEM')
    public_key = key.publickey().export_key('PEM')
    
    return private_key.decode(), public_key.decode()

# Test function
if __name__ == "__main__":
    print("Testing RSA encryption/decryption...")
    
    # Generate test keys
    priv, pub = generate_rsa_keypair()
    
    # Save to temp files
    with open('/tmp/test_priv.pem', 'w') as f:
        f.write(priv)
    with open('/tmp/test_pub.pem', 'w') as f:
        f.write(pub)
    
    # Test encryption/decryption
    message = "Hello, secure world!"
    print(f"Original: {message}")
    
    encrypted = encrypt(message, '/tmp/test_pub.pem')
    print(f"Encrypted: {encrypted.hex()[:50]}...")
    
    decrypted = decrypt(encrypted, '/tmp/test_priv.pem')
    print(f"Decrypted: {decrypted}")
    
    assert message == decrypted, "Encryption/Decryption failed!"
    print("✓ Test passed!")