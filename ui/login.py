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
        self.root.title("P2P Chat Room")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#ecf0f1')
        
        self.ldap = LDAPManager()
        self.pki = PKIManager()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create modern login interface"""
        # Header
        header = tk.Frame(self.root, bg='#3498db', height=120)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🔒 P2P Chat Room", 
                 font=('Arial', 24, 'bold'),
                 bg='#3498db', fg='white').pack(pady=(30, 5))
        tk.Label(header, text="PKI-based Encrypted Messaging",
                 font=('Arial', 11),
                 bg='#3498db', fg='#ecf0f1').pack()
        
        # Main container
        container = tk.Frame(self.root, bg='#ecf0f1')
        container.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Tab buttons frame
        tab_frame = tk.Frame(container, bg='#ecf0f1')
        tab_frame.pack(fill='x', pady=(0, 20))
        
        self.login_tab_btn = tk.Button(
            tab_frame, text="Login",
            font=('Arial', 11, 'bold'),
            bg='#3498db', fg='white',
            relief='flat', bd=0,
            command=lambda: self.switch_tab('login'),
            cursor='hand2'
        )
        self.login_tab_btn.pack(side='left', fill='x', expand=True, ipady=10)
        
        self.register_tab_btn = tk.Button(
            tab_frame, text="Register",
            font=('Arial', 11),
            bg='#bdc3c7', fg='#2c3e50',
            relief='flat', bd=0,
            command=lambda: self.switch_tab('register'),
            cursor='hand2'
        )
        self.register_tab_btn.pack(side='left', fill='x', expand=True, ipady=10)
        
        # Content frame
        self.content_frame = tk.Frame(container, bg='#ffffff', relief='flat', bd=0)
        self.content_frame.pack(fill='both', expand=True)
        
        # Create both forms
        self.login_form = self.create_login_form(self.content_frame)
        self.register_form = self.create_register_form(self.content_frame)
        
        # Show login by default
        self.switch_tab('login')
    
    def switch_tab(self, tab):
        """Switch between login and register tabs"""
        if tab == 'login':
            self.login_tab_btn.config(bg='#3498db', fg='white', font=('Arial', 11, 'bold'))
            self.register_tab_btn.config(bg='#bdc3c7', fg='#2c3e50', font=('Arial', 11))
            self.register_form.pack_forget()
            self.login_form.pack(fill='both', expand=True, padx=30, pady=30)
        else:
            self.register_tab_btn.config(bg='#3498db', fg='white', font=('Arial', 11, 'bold'))
            self.login_tab_btn.config(bg='#bdc3c7', fg='#2c3e50', font=('Arial', 11))
            self.login_form.pack_forget()
            self.register_form.pack(fill='both', expand=True, padx=30, pady=30)
    
    def create_login_form(self, parent):
        """Create login form with modern styling"""
        form = tk.Frame(parent, bg='#ffffff')
        
        tk.Label(form, text="Username", 
                 font=('Arial', 10, 'bold'),
                 bg='#ffffff', fg='#2c3e50').pack(anchor='w', pady=(10, 5))
        
        self.login_username = tk.Entry(
            form, font=('Arial', 11),
            relief='solid', bd=1,
            highlightthickness=1,
            highlightbackground='#bdc3c7',
            highlightcolor='#3498db'
        )
        self.login_username.pack(fill='x', ipady=8, pady=(0, 15))
        
        tk.Label(form, text="Password", 
                 font=('Arial', 10, 'bold'),
                 bg='#ffffff', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        self.login_password = tk.Entry(
            form, font=('Arial', 11), show='●',
            relief='solid', bd=1,
            highlightthickness=1,
            highlightbackground='#bdc3c7',
            highlightcolor='#3498db'
        )
        self.login_password.pack(fill='x', ipady=8, pady=(0, 25))
        self.login_password.bind('<Return>', lambda e: self.handle_login())
        
        tk.Button(
            form, text="Login",
            font=('Arial', 11, 'bold'),
            bg='#3498db', fg='white',
            relief='flat', bd=0,
            command=self.handle_login,
            cursor='hand2'
        ).pack(fill='x', ipady=12)
        
        self.login_status = tk.Label(
            form, text="", 
            font=('Arial', 9),
            bg='#ffffff', fg='#e74c3c'
        )
        self.login_status.pack(pady=(15, 0))
        
        return form
    
    def create_register_form(self, parent):
        """Create registration form with modern styling"""
        form = tk.Frame(parent, bg='#ffffff')
        
        tk.Label(form, text="Username", 
                 font=('Arial', 10, 'bold'),
                 bg='#ffffff', fg='#2c3e50').pack(anchor='w', pady=(5, 5))
        
        self.reg_username = tk.Entry(
            form, font=('Arial', 11),
            relief='solid', bd=1,
            highlightthickness=1,
            highlightbackground='#bdc3c7',
            highlightcolor='#3498db'
        )
        self.reg_username.pack(fill='x', ipady=8, pady=(0, 12))
        
        tk.Label(form, text="Email", 
                 font=('Arial', 10, 'bold'),
                 bg='#ffffff', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        self.reg_email = tk.Entry(
            form, font=('Arial', 11),
            relief='solid', bd=1,
            highlightthickness=1,
            highlightbackground='#bdc3c7',
            highlightcolor='#3498db'
        )
        self.reg_email.pack(fill='x', ipady=8, pady=(0, 12))
        
        tk.Label(form, text="Password", 
                 font=('Arial', 10, 'bold'),
                 bg='#ffffff', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        self.reg_password = tk.Entry(
            form, font=('Arial', 11), show='●',
            relief='solid', bd=1,
            highlightthickness=1,
            highlightbackground='#bdc3c7',
            highlightcolor='#3498db'
        )
        self.reg_password.pack(fill='x', ipady=8, pady=(0, 12))
        
        tk.Label(form, text="Confirm Password", 
                 font=('Arial', 10, 'bold'),
                 bg='#ffffff', fg='#2c3e50').pack(anchor='w', pady=(0, 5))
        
        self.reg_confirm = tk.Entry(
            form, font=('Arial', 11), show='●',
            relief='solid', bd=1,
            highlightthickness=1,
            highlightbackground='#bdc3c7',
            highlightcolor='#3498db'
        )
        self.reg_confirm.pack(fill='x', ipady=8, pady=(0, 20))
        self.reg_confirm.bind('<Return>', lambda e: self.handle_register())
        
        tk.Button(
            form, text="Register",
            font=('Arial', 11, 'bold'),
            bg='#3498db', fg='white',
            relief='flat', bd=0,
            command=self.handle_register,
            cursor='hand2'
        ).pack(fill='x', ipady=12)
        
        self.reg_status = tk.Label(
            form, text="", 
            font=('Arial', 9),
            bg='#ffffff', fg='#e74c3c'
        )
        self.reg_status.pack(pady=(15, 0))
        
        return form
    
    def handle_login(self):
        """Handle login - authenticate via LDAP"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if not username or not password:
            self.login_status.config(text="Please fill all fields")
            return
        
        self.login_status.config(text="Authenticating...", foreground='#3498db')
        self.root.update()
        
        # Authenticate via LDAP
        try:
            if self.ldap.authenticate(username, password):
                # Verify certificate exists
                if not self.pki.verify_cert(username):
                    self.login_status.config(text="Creating certificate...", foreground='#3498db')
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
                    foreground='#e74c3c'
                )
        except ConnectionRefusedError:
            self.login_status.config(
                text="❌ Cannot connect to LDAP server",
                foreground='#e74c3c'
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
                foreground='#e74c3c'
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
        
        # Check if user already exists
        self.reg_status.config(text="Checking username...", foreground='#3498db')
        self.root.update()
        
        try:
            if self.ldap.user_exists(username):
                self.reg_status.config(
                    text="❌ Username already taken",
                    foreground='#e74c3c'
                )
                messagebox.showwarning(
                    "Username Exists",
                    f"The username '{username}' is already registered.\n\n"
                    "Please choose a different username or login if this is your account."
                )
                return
        except ConnectionRefusedError:
            self.reg_status.config(text="❌ Cannot connect to LDAP", foreground='#e74c3c')
            messagebox.showerror(
                "LDAP Connection Error",
                "Cannot connect to LDAP server to check username!\n\n"
                f"Server: {self.ldap.LDAP_SERVER}\n\n"
                "Please verify the server is running and accessible."
            )
            return
        except Exception as e:
            self.reg_status.config(text="❌ Error checking username", foreground='#e74c3c')
            messagebox.showerror("Error", f"Failed to check username:\n{type(e).__name__}: {e}")
            return
        
        # Proceed with registration
        self.reg_status.config(text="Creating account...", foreground='#3498db')
        self.root.update()
        
        try:
            # Register in LDAP
            if self.ldap.register_user(username, password, email):
                # Create PKI certificate
                self.reg_status.config(text="Creating certificate...", foreground='#3498db')
                self.root.update()
                
                if self.pki.create_user_cert(username):
                    self.reg_status.config(
                        text="✅ Registration successful! Please login.",
                        foreground='#27ae60'
                    )
                    messagebox.showinfo(
                        "Registration Successful",
                        f"Account created successfully!\n\n"
                        f"Username: {username}\n"
                        f"Email: {email}\n\n"
                        "You can now login with your credentials."
                    )
                    # Clear form and switch to login
                    self.reg_username.delete(0, 'end')
                    self.reg_email.delete(0, 'end')
                    self.reg_password.delete(0, 'end')
                    self.reg_confirm.delete(0, 'end')
                    self.switch_tab('login')
                else:
                    self.reg_status.config(text="❌ Certificate creation failed", foreground='#e74c3c')
                    messagebox.showerror(
                        "Certificate Error",
                        "Account created but certificate generation failed.\n\n"
                        "You may need to contact an administrator."
                    )
            else:
                self.reg_status.config(text="❌ Registration failed", foreground='#e74c3c')
                messagebox.showerror(
                    "Registration Failed",
                    "Failed to create account in LDAP.\n\n"
                    "This could be due to:\n"
                    "- LDAP server connection issue\n"
                    "- Invalid user data\n"
                    "- Permission problems"
                )
        except ConnectionRefusedError:
            self.reg_status.config(text="❌ Cannot connect to LDAP", foreground='#e74c3c')
            messagebox.showerror(
                "LDAP Connection Error",
                "Cannot connect to LDAP server!\n\n"
                f"Server: {self.ldap.LDAP_SERVER}\n\n"
                "Please verify the server is running."
            )
        except Exception as e:
            self.reg_status.config(text="❌ Registration error", foreground='#e74c3c')
            messagebox.showerror(
                "Registration Error",
                f"An error occurred during registration:\n\n{type(e).__name__}: {e}"
            )
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    LoginApp().run()