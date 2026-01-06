"""
Comprehensive Test Suite for P2P Chat Room
Run this to verify all components work correctly
"""

import sys
import os
from pathlib import Path
import time

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(test_name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {test_name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")

def print_info(message):
    print(f"  {message}")


class ChatSystemTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def test_imports(self):
        """Test 1: Verify all required modules can be imported"""
        print_test("Module Imports")
        
        modules = [
            ('crypto_manager', ['encrypt', 'decrypt']),
            ('ldap_manager', ['LDAPManager']),
            ('pki_manager', ['PKIManager', 'PKI_PATH']),
            ('rabbitmq_manager', ['MQ', 'RABBITMQ_HOST']),
            ('ui.login', ['LoginApp']),
            ('ui.chat', ['ChatApp']),
        ]
        
        for module_name, items in modules:
            try:
                module = __import__(module_name, fromlist=items)
                for item in items:
                    if not hasattr(module, item):
                        print_error(f"{module_name}.{item} not found")
                        self.failed += 1
                    else:
                        print_success(f"Imported {module_name}.{item}")
                        self.passed += 1
            except ImportError as e:
                print_error(f"Failed to import {module_name}: {e}")
                self.failed += 1
        
        # Test external dependencies
        external = ['tkinter', 'pika', 'ldap3', 'cryptography', 'Crypto']
        for lib in external:
            try:
                __import__(lib)
                print_success(f"External library: {lib}")
                self.passed += 1
            except ImportError:
                print_error(f"Missing external library: {lib}")
                self.failed += 1
    
    def test_pki_setup(self):
        """Test 2: Verify PKI infrastructure"""
        print_test("PKI Certificate Infrastructure")
        
        try:
            from pki_manager import PKIManager, PKI_PATH
            
            # Check PKI directory
            if PKI_PATH.exists():
                print_success(f"PKI directory exists: {PKI_PATH}")
                self.passed += 1
            else:
                print_error(f"PKI directory not found: {PKI_PATH}")
                self.failed += 1
                return
            
            # Check CA certificate
            ca_cert = PKI_PATH / "ca.crt"
            ca_key = PKI_PATH / "ca.key"
            
            if ca_cert.exists() and ca_key.exists():
                print_success("CA certificate and key exist")
                self.passed += 1
            else:
                print_warning("CA not found - will be created on first run")
                self.warnings += 1
            
            # Test PKI manager initialization
            try:
                pki = PKIManager()
                print_success("PKI Manager initialized successfully")
                self.passed += 1
            except Exception as e:
                print_error(f"PKI Manager initialization failed: {e}")
                self.failed += 1
            
            # Check for user certificates
            user_certs = list(PKI_PATH.glob("*.crt"))
            user_certs = [f for f in user_certs if f.stem != "ca"]
            
            if user_certs:
                print_success(f"Found {len(user_certs)} user certificate(s)")
                for cert in user_certs:
                    print_info(f"  - {cert.stem}")
                self.passed += 1
            else:
                print_warning("No user certificates found - register users first")
                self.warnings += 1
                
        except Exception as e:
            print_error(f"PKI test failed: {e}")
            self.failed += 1
    
    def test_ldap_connection(self):
        """Test 3: Verify LDAP server connection"""
        print_test("LDAP Authentication Server")
        
        try:
            from ldap_manager import LDAPManager, LDAP_SERVER, BASE_DN
            
            print_info(f"LDAP Server: {LDAP_SERVER}")
            print_info(f"Base DN: {BASE_DN}")
            
            ldap = LDAPManager()
            
            # Test connection by trying to check if a user exists
            try:
                # This will attempt to connect
                result = ldap.user_exists("test_user_that_doesnt_exist")
                print_success("Successfully connected to LDAP server")
                self.passed += 1
            except ConnectionRefusedError:
                print_error(f"Cannot connect to LDAP server at {LDAP_SERVER}")
                print_info("  Make sure LDAP server is running")
                self.failed += 1
            except Exception as e:
                print_warning(f"LDAP connection issue: {e}")
                self.warnings += 1
                
        except Exception as e:
            print_error(f"LDAP test failed: {e}")
            self.failed += 1
    
    def test_rabbitmq_connection(self):
        """Test 4: Verify RabbitMQ server connection"""
        print_test("RabbitMQ Message Broker")
        
        try:
            from rabbitmq_manager import MQ, RABBITMQ_HOST, RABBITMQ_USER
            
            print_info(f"RabbitMQ Host: {RABBITMQ_HOST}")
            print_info(f"RabbitMQ User: {RABBITMQ_USER}")
            
            try:
                # Try to connect
                mq = MQ("test_connection_user")
                print_success("Successfully connected to RabbitMQ")
                self.passed += 1
                
                # Test presence announcement
                mq.announce_presence('online')
                print_success("Presence announcement works")
                self.passed += 1
                
                # Close connection
                mq.close()
                print_success("Connection closed cleanly")
                self.passed += 1
                
            except ConnectionRefusedError:
                print_error(f"Cannot connect to RabbitMQ at {RABBITMQ_HOST}")
                print_info("  Solutions:")
                print_info("  1. Start RabbitMQ server")
                print_info("  2. Check firewall settings")
                print_info("  3. Verify RabbitMQ is listening on 0.0.0.0:5672")
                self.failed += 1
            except Exception as e:
                print_error(f"RabbitMQ connection failed: {e}")
                print_info(f"  Error type: {type(e).__name__}")
                self.failed += 1
                
        except Exception as e:
            print_error(f"RabbitMQ test failed: {e}")
            self.failed += 1
    
    def test_encryption(self):
        """Test 5: Verify RSA encryption/decryption"""
        print_test("RSA Encryption System")
        
        try:
            from crypto_manager import encrypt, decrypt
            from pki_manager import PKIManager, PKI_PATH
            
            pki = PKIManager()
            
            # Find a user certificate to test with
            user_certs = [f.stem for f in PKI_PATH.glob("*.crt") if f.stem != "ca"]
            
            if not user_certs:
                print_warning("No user certificates found - cannot test encryption")
                print_info("  Register a user first, then run this test again")
                self.warnings += 1
                return
            
            test_user = user_certs[0]
            print_info(f"Testing with user: {test_user}")
            
            # Get keys
            pub_key_path = pki.get_user_pubkey_path(test_user)
            priv_key_path = pki.get_user_key_path(test_user)
            
            if not Path(pub_key_path).exists() or not Path(priv_key_path).exists():
                print_error(f"Keys not found for user {test_user}")
                self.failed += 1
                return
            
            # Test encryption/decryption
            test_message = "Hello, this is a test message! 🔒"
            
            try:
                # Encrypt
                encrypted = encrypt(test_message, pub_key_path)
                print_success("Message encrypted successfully")
                print_info(f"  Original: {test_message}")
                print_info(f"  Encrypted length: {len(encrypted)} bytes")
                self.passed += 1
                
                # Decrypt
                decrypted = decrypt(encrypted, priv_key_path)
                print_success("Message decrypted successfully")
                print_info(f"  Decrypted: {decrypted}")
                self.passed += 1
                
                # Verify
                if decrypted == test_message:
                    print_success("Encryption/Decryption verified - messages match!")
                    self.passed += 1
                else:
                    print_error("Decrypted message doesn't match original!")
                    self.failed += 1
                    
            except Exception as e:
                print_error(f"Encryption test failed: {e}")
                self.failed += 1
                
        except Exception as e:
            print_error(f"Encryption system test failed: {e}")
            self.failed += 1
    
    def test_file_structure(self):
        """Test 6: Verify project file structure"""
        print_test("Project File Structure")
        
        required_files = [
            'main.py',
            'crypto_manager.py',
            'ldap_manager.py',
            'pki_manager.py',
            'rabbitmq_manager.py',
            'ui/__init__.py',
            'ui/login.py',
            'ui/chat.py',
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                print_success(f"Found: {file_path}")
                self.passed += 1
            else:
                print_error(f"Missing: {file_path}")
                self.failed += 1
    
    def test_network_configuration(self):
        """Test 7: Network connectivity tests"""
        print_test("Network Configuration")
        
        try:
            import socket
            from rabbitmq_manager import RABBITMQ_HOST
            from ldap_manager import LDAP_SERVER
            
            # Extract host from LDAP_SERVER (ldap://hostname)
            ldap_host = LDAP_SERVER.replace('ldap://', '').split(':')[0]
            
            # Test RabbitMQ connectivity
            print_info(f"Testing connection to RabbitMQ ({RABBITMQ_HOST}:5672)...")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((RABBITMQ_HOST, 5672))
                sock.close()
                
                if result == 0:
                    print_success(f"Port 5672 is open on {RABBITMQ_HOST}")
                    self.passed += 1
                else:
                    print_error(f"Cannot reach {RABBITMQ_HOST}:5672")
                    self.failed += 1
            except Exception as e:
                print_error(f"Network test failed: {e}")
                self.failed += 1
            
            # Test LDAP connectivity
            print_info(f"Testing connection to LDAP ({ldap_host}:389)...")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((ldap_host, 389))
                sock.close()
                
                if result == 0:
                    print_success(f"Port 389 is open on {ldap_host}")
                    self.passed += 1
                else:
                    print_error(f"Cannot reach {ldap_host}:389")
                    self.failed += 1
            except Exception as e:
                print_error(f"LDAP network test failed: {e}")
                self.failed += 1
                
        except Exception as e:
            print_error(f"Network configuration test failed: {e}")
            self.failed += 1
    
    def print_summary(self):
        """Print test results summary"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        total = self.passed + self.failed + self.warnings
        
        print(f"\n{GREEN}Passed:   {self.passed}{RESET}")
        print(f"{RED}Failed:   {self.failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"Total:    {total}")
        
        if self.failed == 0:
            print(f"\n{GREEN}{'='*60}")
            print(f"🎉 ALL CRITICAL TESTS PASSED!")
            print(f"{'='*60}{RESET}")
            
            if self.warnings > 0:
                print(f"\n{YELLOW}Note: {self.warnings} warning(s) - these are usually OK{RESET}")
        else:
            print(f"\n{RED}{'='*60}")
            print(f"❌ {self.failed} TEST(S) FAILED")
            print(f"{'='*60}{RESET}")
            print("\nPlease fix the failed tests before running the application.")
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{BLUE}{'='*60}")
        print(f"P2P Chat Room - System Test Suite")
        print(f"{'='*60}{RESET}\n")
        
        self.test_file_structure()
        self.test_imports()
        self.test_pki_setup()
        self.test_network_configuration()
        self.test_ldap_connection()
        self.test_rabbitmq_connection()
        self.test_encryption()
        
        self.print_summary()


def main():
    """Main test runner"""
    tester = ChatSystemTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Unexpected error during testing: {e}{RESET}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()