import subprocess
import os
from pathlib import Path
import platform


if platform.system() == "Windows":
    PKI_PATH = Path(rf"\\192.168.92.128\chat_pki")
else:
    PKI_PATH = Path.home() / "Documents" / "chat_pki"

class PKIManager:
    def __init__(self):
        """Initialize PKI directory structure"""
        PKI_PATH.mkdir(exist_ok=True)
        self.ensure_ca_exists()
    
    def ensure_ca_exists(self):
        """Create CA certificate if it doesn't exist"""
        ca_key = PKI_PATH / "ca.key"
        ca_crt = PKI_PATH / "ca.crt"
        
        if not ca_key.exists():
            # Generate CA private key
            subprocess.run([
                "openssl", "genrsa", 
                "-out", str(ca_key), 
                "4096"
            ], check=True)
            
            # Generate CA certificate
            subprocess.run([
                "openssl", "req", "-new", "-x509",
                "-days", "3650",
                "-key", str(ca_key),
                "-out", str(ca_crt),
                "-subj", "/CN=ChatAppCA/O=ChatApp/C=TN"
            ], check=True)
            
            print("CA certificate created successfully")
    
    def create_user_cert(self, username):
        """Create X.509 certificate and RSA key pair for user"""
        try:
            # Ensure PKI directory is accessible
            if not PKI_PATH.exists():
                print(f"Creating PKI directory: {PKI_PATH}")
                PKI_PATH.mkdir(parents=True, exist_ok=True)
            
            user_key = PKI_PATH / f"{username}.key"
            user_csr = PKI_PATH / f"{username}.csr"
            user_crt = PKI_PATH / f"{username}.crt"
            
            # Generate RSA private key (2048 bits)
            subprocess.run([
                "openssl", "genrsa",
                "-out", str(user_key),
                "2048"
            ], check=True, cwd=str(PKI_PATH))
            
            # Generate certificate signing request
            subprocess.run([
                "openssl", "req", "-new",
                "-key", str(user_key),
                "-out", str(user_csr),
                "-subj", f"/CN={username}/O=ChatApp/C=TN"
            ], check=True)
            
            # Sign certificate with CA
            subprocess.run([
                "openssl", "x509", "-req",
                "-in", str(user_csr),
                "-CA", str(PKI_PATH / "ca.crt"),
                "-CAkey", str(PKI_PATH / "ca.key"),
                "-CAcreateserial",
                "-out", str(user_crt),
                "-days", "365",
                "-sha256"
            ], check=True)
            
            # Generate public key from private key for RSA encryption
            user_pub = PKI_PATH / f"{username}_pub.pem"
            subprocess.run([
                "openssl", "rsa",
                "-in", str(user_key),
                "-pubout",
                "-out", str(user_pub)
            ], check=True)
            
            print(f"Certificate and keys created for {username}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error creating certificate: {e}")
            return False
    
    def get_user_cert_path(self, username):
        """Get path to user's certificate"""
        return str(PKI_PATH / f"{username}.crt")
    
    def get_user_key_path(self, username):
        """Get path to user's private key"""
        return str(PKI_PATH / f"{username}.key")
    
    def get_user_pubkey_path(self, username):
        """Get path to user's public key"""
        return str(PKI_PATH / f"{username}_pub.pem")
    
    def verify_cert(self, username):
        """Verify user certificate against CA"""
        try:
            result = subprocess.run([
                "openssl", "verify",
                "-CAfile", str(PKI_PATH / "ca.crt"),
                str(PKI_PATH / f"{username}.crt")
            ], capture_output=True, text=True)
            
            return "OK" in result.stdout
        except:
            return False