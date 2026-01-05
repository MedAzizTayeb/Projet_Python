from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import platform


if platform.system() == "Windows":
    PKI_PATH = Path("Z:/") 
else:
    PKI_PATH = Path.home() / "Documents" / "chat_pki"

class PKIManager:
    def __init__(self):
        """Initialize PKI - uses existing CA if available"""
        if not PKI_PATH.exists():
            print(f"Creating PKI directory: {PKI_PATH}")
            PKI_PATH.mkdir(parents=True, exist_ok=True)
        
        ca_key_path = PKI_PATH / "ca.key"
        ca_crt_path = PKI_PATH / "ca.crt"
        
        if ca_key_path.exists() and ca_crt_path.exists():
            print(f"✓ Using existing CA certificate from {PKI_PATH}")
        else:
            print("CA certificate not found, creating new one...")
            self.create_ca()
    
    def create_ca(self):
        """Create NEW Certificate Authority (only if doesn't exist)"""
        ca_key_path = PKI_PATH / "ca.key"
        ca_crt_path = PKI_PATH / "ca.crt"
        
        # Generate CA private key
        ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Save CA private key
        with open(ca_key_path, 'wb') as f:
            f.write(ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "TN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ChatApp"),
            x509.NameAttribute(NameOID.COMMON_NAME, "ChatAppCA"),
        ])
        
        ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650)  # 10 years
        ).sign(ca_key, hashes.SHA256(), default_backend())
        
        # Save CA certificate
        with open(ca_crt_path, 'wb') as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"✓ NEW CA certificate created at {PKI_PATH}")
    
    def create_user_cert(self, username):
        """
        Create user certificate SIGNED BY existing CA
        Each user gets their own certificate signed by the ONE CA
        """
        user_key_path = PKI_PATH / f"{username}.key"
        user_crt_path = PKI_PATH / f"{username}.crt"
        user_pub_path = PKI_PATH / f"{username}_pub.pem"
        
        # Check if user certificate already exists
        if user_key_path.exists() and user_crt_path.exists() and user_pub_path.exists():
            print(f"✓ Certificate already exists for {username}")
            return True
        
        print(f"Creating new certificate for {username}...")
        
        # Generate user private key
        user_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Save user private key
        with open(user_key_path, 'wb') as f:
            f.write(user_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save user public key (for RSA encryption)
        with open(user_pub_path, 'wb') as f:
            f.write(user_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        # Load the ONE CA key and certificate
        ca_key_path = PKI_PATH / "ca.key"
        ca_crt_path = PKI_PATH / "ca.crt"
        
        with open(ca_key_path, 'rb') as f:
            ca_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
        
        with open(ca_crt_path, 'rb') as f:
            ca_cert = x509.load_pem_x509_certificate(
                f.read(), default_backend()
            )
        
        # Create user certificate SIGNED BY CA
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "TN"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ChatApp"),
            x509.NameAttribute(NameOID.COMMON_NAME, username),
        ])
        
        user_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            ca_cert.subject  # Signed by CA
        ).public_key(
            user_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)  # 1 year
        ).sign(ca_key, hashes.SHA256(), default_backend())  # Signed with CA's private key
        
        # Save user certificate
        with open(user_crt_path, 'wb') as f:
            f.write(user_cert.public_bytes(serialization.Encoding.PEM))
        
        print(f"✓ Certificate created for {username} (signed by CA)")
        return True
    
    def get_user_key_path(self, username):
        """Get path to user's private key"""
        return str(PKI_PATH / f"{username}.key")
    
    def get_user_pubkey_path(self, username):
        """Get path to user's public key"""
        return str(PKI_PATH / f"{username}_pub.pem")
    
    def verify_cert(self, username):
        """Check if user certificate exists"""
        cert_path = PKI_PATH / f"{username}.crt"
        key_path = PKI_PATH / f"{username}.key"
        pub_path = PKI_PATH / f"{username}_pub.pem"
        return cert_path.exists() and key_path.exists() and pub_path.exists()