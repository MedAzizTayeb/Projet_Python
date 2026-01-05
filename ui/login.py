import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ldap_manager import LDAPManager
from pki_manager import PKIManager

class LoginApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Secure Chat - Login")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        self.ldap = LDAPManager()
        self.pki = PKIManager()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create login interface"""
        container = ttk.Frame(self.root, padding="40")
        container.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(container, text="🔒 Secure Chat", 
                 font=('Arial', 18, 'bold')).pack(pady=(0, 5))
        ttk.Label(container, text="PKI-based encrypted messaging",
                 font=('Arial', 10)).pack(pady=(0, 20))
        
        # Tabs for Login/Register
        notebook = ttk.Notebook(container)
        notebook.pack(fill='both', expand=True, pady=10)
        
        # Login Tab
        login_frame = ttk.Frame(notebook, padding="20")
        notebook.add(login_frame, text='Login')
        self.create_login_tab(login_frame)
        
        # Register Tab
        register_frame = ttk.Frame(notebook, padding="20")
        notebook.add(register_frame, text='Register')
        self.create_register_tab(register_frame)
    
    def create_login_tab(self, parent):
        """Create login form"""
        ttk.Label(parent, text="Username:").pack(anchor='w', pady=(10, 2))
        self.login_username = ttk.Entry(parent, width=30)
        self.login_username.pack(fill='x', pady=(0, 10))
        
        ttk.Label(parent, text="Password:").pack(anchor='w', pady=(0, 2))
        self.login_password = ttk.Entry(parent, width=30, show='*')
        self.login_password.pack(fill='x', pady=(0, 20))
        self.login_password.bind('<Return>', lambda e: self.handle_login())
        
        ttk.Button(parent, text="Login", 
                  command=self.handle_login).pack(fill='x')
        
        self.login_status = ttk.Label(parent, text="", foreground='red')
        self.login_status.pack(pady=(10, 0))
    
    def create_register_tab(self, parent):
        """Create registration form"""
        ttk.Label(parent, text="Username:").pack(anchor='w', pady=(5, 2))
        self.reg_username = ttk.Entry(parent, width=30)
        self.reg_username.pack(fill='x', pady=(0, 10))
        
        ttk.Label(parent, text="Email:").pack(anchor='w', pady=(0, 2))
        self.reg_email = ttk.Entry(parent, width=30)
        self.reg_email.pack(fill='x', pady=(0, 10))
        
        ttk.Label(parent, text="Password:").pack(anchor='w', pady=(0, 2))
        self.reg_password = ttk.Entry(parent, width=30, show='*')
        self.reg_password.pack(fill='x', pady=(0, 10))
        
        ttk.Label(parent, text="Confirm Password:").pack(anchor='w', pady=(0, 2))
        self.reg_confirm = ttk.Entry(parent, width=30, show='*')
        self.reg_confirm.pack(fill='x', pady=(0, 15))
        self.reg_confirm.bind('<Return>', lambda e: self.handle_register())
        
        ttk.Button(parent, text="Register",
                  command=self.handle_register).pack(fill='x')
        
        self.reg_status = ttk.Label(parent, text="", foreground='red')
        self.reg_status.pack(pady=(10, 0))
    
    def handle_login(self):
        """Handle login - authenticate via LDAP"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            self.login_status.config(text="Please fill all fields")
            return
        
        self.login_status.config(text="Authenticating...", foreground='blue')
        self.root.update()
        
        # Authenticate via LDAP
        try:
            if self.ldap.authenticate(username, password):
                # Verify certificate exists
                if not self.pki.verify_cert(username):
                    self.login_status.config(text="Creating certificate...", foreground='blue')
                    self.root.update()
                    self.pki.create_user_cert(username)
                
                # Try to open chat
                try:
                    from ui.chat import ChatApp
                    self.root.destroy()
                    ChatApp(username).run()
                except Exception as e:
                    # Detailed connection error handling
                    error_msg = str(e)
                    error_type = type(e).__name__
                    
                    if "AMQPConnectionError" in error_type or "ConnectionRefusedError" in error_type:
                        messagebox.showerror(
                            "RabbitMQ Connection Error",
                            "❌ Cannot connect to RabbitMQ server!\n\n"
                            "Troubleshooting steps:\n\n"
                            "1. Check RabbitMQ is running on host:\n"
                            "   - Windows: Check Services for 'RabbitMQ'\n"
                            "   - Linux: sudo systemctl status rabbitmq-server\n\n"
                            "2. Verify it's listening on all interfaces:\n"
                            "   - Run: netstat -an | findstr :5672\n"
                            "   - Should show: 0.0.0.0:5672 (not 127.0.0.1)\n\n"
                            "3. Check Windows Firewall:\n"
                            "   - Allow port 5672 for VMnet8\n\n"
                            "4. Verify host IP in rabbitmq_manager.py:\n"
                            f"   - Current: 192.168.92.1\n"
                            f"   - Can you ping it from VM?"
                        )
                    elif "timeout" in error_msg.lower():
                        messagebox.showerror(
                            "Connection Timeout",
                            "⏱️ Connection timed out!\n\n"
                            "Possible causes:\n"
                            "- Firewall blocking port 5672\n"
                            "- RabbitMQ not listening on correct interface\n"
                            "- Network configuration issue\n\n"
                            f"Error: {error_msg}"
                        )
                    else:
                        messagebox.showerror(
                            "Connection Error", 
                            f"Failed to start chat:\n\n{error_type}: {error_msg}"
                        )
                    
                    # Recreate login window since we destroyed it
                    LoginApp().run()
                    return
            else:
                self.login_status.config(
                    text="❌ Invalid username or password",
                    foreground='red'
                )
        except ConnectionRefusedError:
            self.login_status.config(
                text="❌ Cannot connect to LDAP server",
                foreground='red'
            )
            messagebox.showerror(
                "LDAP Connection Error",
                "Cannot connect to LDAP server!\n\n"
                f"Server: {self.ldap.LDAP_SERVER}\n\n"
                "Please verify:\n"
                "1. LDAP server is running\n"
                "2. Server IP is correct\n"
                "3. Network connectivity"
            )
        except Exception as e:
            self.login_status.config(
                text=f"❌ Login error",
                foreground='red'
            )
            messagebox.showerror("Error", f"Login failed:\n{type(e).__name__}: {e}")
    
    def handle_register(self):
        """Handle registration - add to LDAP and create PKI certificate"""
        username = self.reg_username.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        
        # Validation
        if not username or not email or not password:
            self.reg_status.config(text="❌ Please fill all fields")
            return
        
        if len(username) < 3:
            self.reg_status.config(text="❌ Username too short (min 3 chars)")
            return
        
        if len(password) < 6:
            self.reg_status.config(text="❌ Password too short (min 6 chars)")
            return
        
        if password != confirm:
            self.reg_status.config(text="❌ Passwords don't match")
            return
        
        if '@' not in email:
            self.reg_status.config(text="❌ Invalid email address")
            return
        
        # Check if user already exists (IMPROVED)
        self.reg_status.config(text="Checking username...", foreground='blue')
        self.root.update()
        
        try:
            if self.ldap.user_exists(username):
                self.reg_status.config(
                    text="❌ Username already taken",
                    foreground='red'
                )
                messagebox.showwarning(
                    "Username Exists",
                    f"The username '{username}' is already registered.\n\n"
                    "Please choose a different username or login if this is your account."
                )
                return
        except ConnectionRefusedError:
            self.reg_status.config(text="❌ Cannot connect to LDAP", foreground='red')
            messagebox.showerror(
                "LDAP Connection Error",
                "Cannot connect to LDAP server to check username!\n\n"
                f"Server: {self.ldap.LDAP_SERVER}\n\n"
                "Please verify the server is running and accessible."
            )
            return
        except Exception as e:
            self.reg_status.config(text="❌ Error checking username", foreground='red')
            messagebox.showerror("Error", f"Failed to check username:\n{type(e).__name__}: {e}")
            return
        
        # Proceed with registration
        self.reg_status.config(text="Creating account...", foreground='blue')
        self.root.update()
        
        try:
            # Register in LDAP
            if self.ldap.register_user(username, password, email):
                # Create PKI certificate (signed by CA)
                self.reg_status.config(text="Creating certificate...", foreground='blue')
                self.root.update()
                
                if self.pki.create_user_cert(username):
                    self.reg_status.config(
                        text="✅ Registration successful! Please login.",
                        foreground='green'
                    )
                    messagebox.showinfo(
                        "Registration Successful",
                        f"Account created successfully!\n\n"
                        f"Username: {username}\n"
                        f"Email: {email}\n\n"
                        "You can now login with your credentials."
                    )
                    # Clear form
                    self.reg_username.delete(0, 'end')
                    self.reg_email.delete(0, 'end')
                    self.reg_password.delete(0, 'end')
                    self.reg_confirm.delete(0, 'end')
                else:
                    self.reg_status.config(text="❌ Certificate creation failed", foreground='red')
                    messagebox.showerror(
                        "Certificate Error",
                        "Account created but certificate generation failed.\n\n"
                        "You may need to contact an administrator."
                    )
            else:
                self.reg_status.config(text="❌ Registration failed", foreground='red')
                messagebox.showerror(
                    "Registration Failed",
                    "Failed to create account in LDAP.\n\n"
                    "This could be due to:\n"
                    "- LDAP server connection issue\n"
                    "- Invalid user data\n"
                    "- Permission problems"
                )
        except ConnectionRefusedError:
            self.reg_status.config(text="❌ Cannot connect to LDAP", foreground='red')
            messagebox.showerror(
                "LDAP Connection Error",
                "Cannot connect to LDAP server!\n\n"
                f"Server: {self.ldap.LDAP_SERVER}\n\n"
                "Please verify the server is running."
            )
        except Exception as e:
            self.reg_status.config(text="❌ Registration error", foreground='red')
            messagebox.showerror(
                "Registration Error",
                f"An error occurred during registration:\n\n{type(e).__name__}: {e}"
            )
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    LoginApp().run()