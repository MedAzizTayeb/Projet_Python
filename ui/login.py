import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ldap_manager import LDAPManager
from pki_manager import PKIManager
from ui.chat import ChatApp

class LoginApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Secure Chat - Login")
        self.root.geometry("400x600")  # Increased height from 500 to 600
        self.root.resizable(False, False)
        
        # Center window
        self.center_window()
        
        # Managers
        self.ldap = LDAPManager()
        self.pki = PKIManager()
        
        # Style
        self.setup_styles()
        
        # Create UI
        self.create_widgets()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 18, 'bold'), foreground='#2c3e50')
        style.configure('Subtitle.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10), padding=10)
        style.configure('TEntry', font=('Arial', 10))
    
    def create_widgets(self):
        """Create login interface widgets"""
        # Main container
        container = ttk.Frame(self.root, padding="40 30 40 30")
        container.pack(fill='both', expand=True)
        
        # Title
        title = ttk.Label(container, text="🔒 Secure Chat", style='Title.TLabel')
        title.pack(pady=(0, 5))
        
        subtitle = ttk.Label(container, text="PKI-based encrypted messaging", 
                            style='Subtitle.TLabel')
        subtitle.pack(pady=(0, 20))  # Reduced from 30 to 20
        
        # Notebook for Login/Register tabs
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill='both', expand=True, pady=5)  # Reduced from 10 to 5
        
        # Login Tab
        login_frame = ttk.Frame(self.notebook, padding="20 10 20 10")  # Reduced padding
        self.notebook.add(login_frame, text='Login')
        self.create_login_tab(login_frame)
        
        # Register Tab
        register_frame = ttk.Frame(self.notebook, padding="20 10 20 10")  # Reduced padding
        self.notebook.add(register_frame, text='Register')
        self.create_register_tab(register_frame)
    
    def create_login_tab(self, parent):
        """Create login form"""
        # Username
        ttk.Label(parent, text="Username:", font=('Arial', 9)).pack(anchor='w', pady=(10, 2))
        self.login_username = ttk.Entry(parent, width=30, font=('Arial', 10))
        self.login_username.pack(fill='x', pady=(0, 10))
        
        # Password
        ttk.Label(parent, text="Password:", font=('Arial', 9)).pack(anchor='w', pady=(0, 2))
        self.login_password = ttk.Entry(parent, width=30, show='*', font=('Arial', 10))
        self.login_password.pack(fill='x', pady=(0, 20))
        
        # Bind Enter key
        self.login_password.bind('<Return>', lambda e: self.handle_login())
        
        # Login button
        login_btn = ttk.Button(parent, text="Login", command=self.handle_login)
        login_btn.pack(fill='x', pady=5)
        
        # Status label
        self.login_status = ttk.Label(parent, text="", foreground='red', font=('Arial', 9))
        self.login_status.pack(pady=(10, 0))
    
    def create_register_tab(self, parent):
        """Create registration form"""
        # Username
        ttk.Label(parent, text="Username:", font=('Arial', 9)).pack(anchor='w', pady=(5, 2))
        self.reg_username = ttk.Entry(parent, width=30, font=('Arial', 10))
        self.reg_username.pack(fill='x', pady=(0, 10))
        
        # Email
        ttk.Label(parent, text="Email:", font=('Arial', 9)).pack(anchor='w', pady=(0, 2))
        self.reg_email = ttk.Entry(parent, width=30, font=('Arial', 10))
        self.reg_email.pack(fill='x', pady=(0, 10))
        
        # Password
        ttk.Label(parent, text="Password:", font=('Arial', 9)).pack(anchor='w', pady=(0, 2))
        self.reg_password = ttk.Entry(parent, width=30, show='*', font=('Arial', 10))
        self.reg_password.pack(fill='x', pady=(0, 10))
        
        # Confirm Password
        ttk.Label(parent, text="Confirm Password:", font=('Arial', 9)).pack(anchor='w', pady=(0, 2))
        self.reg_confirm = ttk.Entry(parent, width=30, show='*', font=('Arial', 10))
        self.reg_confirm.pack(fill='x', pady=(0, 15))
        
        # Bind Enter key to register
        self.reg_confirm.bind('<Return>', lambda e: self.handle_register())
        
        # Register button - same style as Login
        register_btn = ttk.Button(parent, text="Register", command=self.handle_register)
        register_btn.pack(fill='x', pady=5)
        
        # Status label
        self.reg_status = ttk.Label(parent, text="", foreground='red', font=('Arial', 9))
        self.reg_status.pack(pady=(10, 0))
    
    def handle_login(self):
        """Handle login button click"""
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        # Validation
        if not username or not password:
            self.login_status.config(text="Please fill all fields", foreground='red')
            return
        
        # Show loading
        self.login_status.config(text="Authenticating...", foreground='blue')
        self.root.update()
        
        print(f"Attempting login for user: {username}")
        
        # Authenticate via LDAP
        if self.ldap.authenticate(username, password):
            print(f"LDAP authentication successful for: {username}")
            
            # Verify PKI certificate exists
            if not self.pki.verify_cert(username):
                print(f"Certificate not found or invalid for: {username}")
                self.login_status.config(
                    text="Certificate missing. Generating new certificate...", 
                    foreground='orange'
                )
                self.root.update()
                
                # Create certificate if missing
                if self.pki.create_user_cert(username):
                    print(f"Certificate created successfully for: {username}")
                else:
                    self.login_status.config(
                        text="Failed to create certificate. Check PKI server.", 
                        foreground='red'
                    )
                    return
            
            # Success - open chat
            self.login_status.config(text="Login successful!", foreground='green')
            self.root.update()
            self.root.after(500, lambda: self.open_chat(username))
        else:
            print(f"LDAP authentication failed for: {username}")
            self.login_status.config(
                text="Invalid username or password", 
                foreground='red'
            )
    
    def handle_register(self):
        """Handle registration button click"""
        username = self.reg_username.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        
        # Validation
        if not username or not email or not password:
            self.reg_status.config(text="Please fill all fields", foreground='red')
            return
        
        if len(username) < 3:
            self.reg_status.config(text="Username too short (min 3 chars)", 
                                  foreground='red')
            return
        
        if len(password) < 6:
            self.reg_status.config(text="Password too short (min 6 chars)", 
                                  foreground='red')
            return
        
        if password != confirm:
            self.reg_status.config(text="Passwords don't match", foreground='red')
            return
        
        if '@' not in email:
            self.reg_status.config(text="Invalid email address", foreground='red')
            return
        
        # Check if user exists
        if self.ldap.user_exists(username):
            self.reg_status.config(text="Username already exists", foreground='red')
            return
        
        # Show loading
        self.reg_status.config(text="Creating account...", foreground='blue')
        self.root.update()
        
        # Register in LDAP
        if self.ldap.register_user(username, password, email):
            # Create PKI certificate
            if self.pki.create_user_cert(username):
                self.reg_status.config(
                    text="Registration successful! Please login.", 
                    foreground='green'
                )
                
                # Clear form
                self.reg_username.delete(0, 'end')
                self.reg_email.delete(0, 'end')
                self.reg_password.delete(0, 'end')
                self.reg_confirm.delete(0, 'end')
                
                # Switch to login tab
                self.root.after(1500, lambda: self.notebook.select(0))
            else:
                self.reg_status.config(
                    text="Error creating certificate", 
                    foreground='red'
                )
        else:
            self.reg_status.config(
                text="Registration failed. Please try again.", 
                foreground='red'
            )
    
    def open_chat(self, username):
        """Open chat window and close login"""
        self.root.destroy()
        chat = ChatApp(username)
        chat.run()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = LoginApp()
    app.run()