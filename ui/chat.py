import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime
from pathlib import Path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crypto_manager import encrypt, decrypt
from rabbitmq_manager import MQ
from pki_manager import PKIManager

class ChatApp:
    def __init__(self, username):
        self.username = username
        self.current_chat = None
        self.active_users = set()
        
        # Initialize managers
        self.pki = PKIManager()
        self.mq = MQ(username)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(f"Secure Chat - {username}")
        self.root.geometry("900x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup styles
        self.setup_styles()
        
        # Create UI
        self.create_widgets()
        
        # Start listening for messages
        self.start_message_listener()
        
        # Announce presence
        self.mq.announce_presence('online')
    
    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        self.bg_color = '#ecf0f1'
        self.sidebar_color = '#34495e'
        self.chat_bg = '#ffffff'
        self.sent_msg_color = '#3498db'
        self.recv_msg_color = '#95a5a6'
        
        style.configure('Sidebar.TFrame', background=self.sidebar_color)
        style.configure('Chat.TFrame', background=self.chat_bg)
        style.configure('UserList.TLabel', background=self.sidebar_color, 
                       foreground='white', font=('Arial', 12, 'bold'))
    
    def create_widgets(self):
        """Create chat interface widgets"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True)
        
        # Left sidebar (user list)
        self.create_sidebar(main_container)
        
        # Right side (chat area)
        self.create_chat_area(main_container)
    
    def create_sidebar(self, parent):
        """Create left sidebar with user list"""
        sidebar = ttk.Frame(parent, style='Sidebar.TFrame', width=200)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Header
        header = ttk.Label(sidebar, text=f"👤 {self.username}", 
                          style='UserList.TLabel', padding=15)
        header.pack(fill='x')
        
        # Active users label
        users_label = ttk.Label(sidebar, text="Active Users", 
                               style='UserList.TLabel', padding=10)
        users_label.pack(fill='x', pady=(20, 5))
        
        # User listbox
        list_frame = tk.Frame(sidebar, bg=self.sidebar_color)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.user_listbox = tk.Listbox(
            list_frame,
            bg='#2c3e50',
            fg='white',
            font=('Arial', 11),
            selectmode='single',
            yscrollcommand=scrollbar.set,
            highlightthickness=0,
            activestyle='none',
            selectbackground='#3498db'
        )
        self.user_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.user_listbox.yview)
        
        # Bind selection
        self.user_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        # Add some dummy users for testing
        self.add_test_users()
        
        # Refresh button
        refresh_btn = tk.Button(
            sidebar,
            text="🔄 Refresh Users",
            bg='#2c3e50',
            fg='white',
            font=('Arial', 10),
            command=self.refresh_users,
            relief='flat',
            cursor='hand2'
        )
        refresh_btn.pack(fill='x', padx=10, pady=10)
        
        # Logout button
        logout_btn = tk.Button(
            sidebar,
            text="🚪 Logout",
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10),
            command=self.logout,
            relief='flat',
            cursor='hand2'
        )
        logout_btn.pack(fill='x', padx=10, pady=(0, 10))
    
    def create_chat_area(self, parent):
        """Create right chat area"""
        chat_container = ttk.Frame(parent, style='Chat.TFrame')
        chat_container.pack(side='right', fill='both', expand=True)
        
        # Chat header
        self.chat_header = tk.Label(
            chat_container,
            text="Select a user to start chatting",
            bg='#3498db',
            fg='white',
            font=('Arial', 14, 'bold'),
            pady=15
        )
        self.chat_header.pack(fill='x')
        
        # Messages area
        messages_frame = tk.Frame(chat_container, bg=self.chat_bg)
        messages_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Scrolled text for messages
        self.messages_text = scrolledtext.ScrolledText(
            messages_frame,
            wrap=tk.WORD,
            state='disabled',
            bg=self.chat_bg,
            font=('Arial', 10),
            relief='flat',
            spacing3=10
        )
        self.messages_text.pack(fill='both', expand=True)
        
        # Configure tags for message styling
        self.messages_text.tag_configure('sent', 
            background=self.sent_msg_color, 
            foreground='white',
            lmargin1=200,
            lmargin2=200,
            rmargin=20,
            spacing1=5
        )
        self.messages_text.tag_configure('received', 
            background=self.recv_msg_color,
            foreground='white',
            lmargin1=20,
            lmargin2=20,
            rmargin=200,
            spacing1=5
        )
        self.messages_text.tag_configure('timestamp',
            foreground='#7f8c8d',
            font=('Arial', 8)
        )
        self.messages_text.tag_configure('info',
            foreground='#95a5a6',
            font=('Arial', 9, 'italic'),
            justify='center'
        )
        
        # Input area
        input_frame = tk.Frame(chat_container, bg=self.chat_bg)
        input_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        # Message entry
        self.message_entry = tk.Text(
            input_frame,
            height=3,
            wrap=tk.WORD,
            font=('Arial', 10),
            relief='solid',
            borderwidth=1
        )
        self.message_entry.pack(side='left', fill='both', expand=True)
        self.message_entry.bind('<Return>', self.on_send_shortcut)
        
        # Send button
        send_btn = tk.Button(
            input_frame,
            text="Send\n(Ctrl+Enter)",
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.send_message,
            relief='flat',
            cursor='hand2',
            width=12
        )
        send_btn.pack(side='right', fill='y', padx=(10, 0))
    
    def add_test_users(self):
        """Add some test users to the list"""
        # In production, this would fetch from RabbitMQ or a presence service
        test_users = ['alice', 'bob', 'charlie', 'diana']
        for user in test_users:
            if user != self.username:
                self.user_listbox.insert('end', f"🟢 {user}")
                self.active_users.add(user)
    
    def on_user_select(self, event):
        """Handle user selection from list"""
        selection = self.user_listbox.curselection()
        if selection:
            user_text = self.user_listbox.get(selection[0])
            # Remove emoji and spaces
            username = user_text.replace('🟢', '').strip()
            self.open_chat(username)
    
    def open_chat(self, username):
        """Open chat with selected user"""
        self.current_chat = username
        self.chat_header.config(text=f"💬 Chat with {username}")
        
        # Clear messages
        self.messages_text.config(state='normal')
        self.messages_text.delete(1.0, 'end')
        self.add_info_message(f"Started secure chat with {username}")
        self.add_info_message("All messages are encrypted with RSA")
        self.messages_text.config(state='disabled')
        
        # Focus on input
        self.message_entry.focus()
    
    def on_send_shortcut(self, event):
        """Handle Ctrl+Enter to send message"""
        if event.state & 0x4:  # Ctrl key pressed
            self.send_message()
            return 'break'
        return None
    
    def send_message(self):
        """Send encrypted message to current chat user"""
        if not self.current_chat:
            messagebox.showwarning("No Chat Selected", 
                                  "Please select a user to chat with")
            return
        
        # Get message
        message = self.message_entry.get(1.0, 'end').strip()
        if not message:
            return
        
        try:
            # Get recipient's public key from centralized PKI server
            recipient_pubkey = self.pki.get_user_pubkey_path(self.current_chat)
            
            # Encrypt message
            encrypted = encrypt(message, recipient_pubkey)
            
            # Send via RabbitMQ
            self.mq.send_message(self.current_chat, encrypted)
            
            # Display in chat
            timestamp = datetime.now().strftime("%H:%M")
            self.add_message(message, 'sent', timestamp)
            
            # Clear input
            self.message_entry.delete(1.0, 'end')
            
        except FileNotFoundError:
            messagebox.showerror("Key Error", 
                f"Public key not found for {self.current_chat}.\n"
                "Make sure they are registered on the server.")
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send message: {e}")
    
    def add_message(self, text, msg_type, timestamp):
        """Add message to chat display"""
        self.messages_text.config(state='normal')
        
        # Add newline if not first message
        if self.messages_text.get(1.0, 'end').strip():
            self.messages_text.insert('end', '\n')
        
        # Add message with styling
        if msg_type == 'sent':
            self.messages_text.insert('end', f"  {text}  ", 'sent')
        else:
            self.messages_text.insert('end', f"  {text}  ", 'received')
        
        self.messages_text.insert('end', f"\n{timestamp}", 'timestamp')
        
        self.messages_text.config(state='disabled')
        self.messages_text.see('end')
    
    def add_info_message(self, text):
        """Add info message to chat"""
        self.messages_text.config(state='normal')
        if self.messages_text.get(1.0, 'end').strip():
            self.messages_text.insert('end', '\n')
        self.messages_text.insert('end', f"ℹ️  {text}\n", 'info')
        self.messages_text.config(state='disabled')
        self.messages_text.see('end')
    
    def start_message_listener(self):
        """Start background thread to listen for messages"""
        def listen():
            def callback(ch, method, properties, body):
                try:
                    # Parse message
                    data = json.loads(body.decode())
                    sender = data['from']
                    encrypted_hex = data['message']
                    encrypted_msg = bytes.fromhex(encrypted_hex)
                    
                    # Decrypt message
                    my_privkey = self.pki.get_user_key_path(self.username)
                    decrypted = decrypt(encrypted_msg, my_privkey)
                    
                    # Display if from current chat
                    timestamp = datetime.now().strftime("%H:%M")
                    if sender == self.current_chat:
                        self.root.after(0, lambda: self.add_message(
                            decrypted, 'received', timestamp
                        ))
                    else:
                        # Show notification
                        self.root.after(0, lambda: self.show_notification(
                            sender, decrypted
                        ))
                        
                except Exception as e:
                    print(f"Error processing message: {e}")
            
            self.mq.listen(callback)
        
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
    
    def show_notification(self, sender, message):
        """Show notification for message from other user"""
        # Simple notification - you could use system notifications here
        preview = message[:30] + "..." if len(message) > 30 else message
        self.root.title(f"💬 New message from {sender}")
        self.root.after(3000, lambda: self.root.title(
            f"Secure Chat - {self.username}"
        ))
    
    def refresh_users(self):
        """Refresh active users list"""
        # In production, query RabbitMQ or presence service
        messagebox.showinfo("Refresh", "User list refreshed")
    
    def logout(self):
        """Logout and return to login screen"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.on_closing()
    
    def on_closing(self):
        """Handle window closing"""
        try:
            self.mq.announce_presence('offline')
            self.mq.close()
        except:
            pass
        self.root.destroy()
        
        # Restart login app
        from ui.login import LoginApp
        LoginApp().run()
    
    def run(self):
        """Start the chat application"""
        self.root.mainloop()

if __name__ == "__main__":
    # For testing
    import sys
    if len(sys.argv) > 1:
        app = ChatApp(sys.argv[1])
        app.run()
    else:
        print("Usage: python chat.py <username>")