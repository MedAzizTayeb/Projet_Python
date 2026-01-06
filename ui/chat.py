import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from datetime import datetime
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
        self.active_users = {}
        self.message_history = {}  # Store messages per user
        
        self.pki = PKIManager()
        self.mq = MQ(username)
        
        self.root = tk.Tk()
        self.root.title(f"P2P Chat Room - {username}")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.create_widgets()
        self.start_message_listener()
        self.start_presence_listener()
        
        # Announce presence and refresh users
        self.root.after(500, self.initial_setup)
    
    def initial_setup(self):
        """Initial setup after UI is ready"""
        # Announce presence once initially
        self.mq.announce_presence('online')
        
        self.refresh_users()
        
        # Start periodic presence announcements every 30 seconds
        self.announce_presence_periodically()
    
    def create_widgets(self):
        """Create chat interface"""
        main = ttk.Frame(self.root)
        main.pack(fill='both', expand=True)
        
        # Left sidebar - Active users list
        self.create_sidebar(main)
        
        # Right side - Chat area
        self.create_chat_area(main)
    
    def create_sidebar(self, parent):
        """Create sidebar with active users"""
        sidebar = tk.Frame(parent, bg='#34495e', width=200)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Header
        tk.Label(sidebar, text=f"👤 {self.username}",
                bg='#34495e', fg='white',
                font=('Arial', 12, 'bold'),
                pady=15).pack(fill='x')
        
        # Group Chat Button (NEW)
        tk.Button(sidebar, text="💬 Group Chat",
                 bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'),
                 command=self.open_group_chat,
                 relief='flat',
                 cursor='hand2',
                 pady=12).pack(fill='x', padx=10, pady=(5, 10))
        
        # Active users label
        tk.Label(sidebar, text="Available Users",
                bg='#34495e', fg='white',
                font=('Arial', 11, 'bold'),
                pady=10).pack(fill='x')
        
        # User list with custom styling
        list_frame = tk.Frame(sidebar, bg='#34495e')
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create a frame for each user entry instead of Listbox
        self.users_container = tk.Frame(list_frame, bg='#2c3e50')
        self.users_container.pack(fill='both', expand=True)
        
        # Keep track of user buttons
        self.user_buttons = {}
        
        # Refresh users button
        tk.Button(sidebar, text="🔄 Refresh Users",
                 bg='#2c3e50', fg='white',
                 font=('Arial', 10),
                 command=self.refresh_users,
                 relief='flat',
                 cursor='hand2').pack(fill='x', padx=10, pady=(10, 5))
        
        # Logout button
        tk.Button(sidebar, text="🚪 Logout",
                 bg='#e74c3c', fg='white',
                 font=('Arial', 10),
                 command=self.logout,
                 relief='flat',
                 cursor='hand2').pack(fill='x', padx=10, pady=5)
    
    def create_chat_area(self, parent):
        """Create chat area"""
        chat = tk.Frame(parent, bg='#ecf0f1')
        chat.pack(side='right', fill='both', expand=True)
        
        # Header
        self.chat_header = tk.Label(
            chat,
            text="Select a user to start chatting",
            bg='#3498db',
            fg='white',
            font=('Arial', 14, 'bold'),
            pady=15
        )
        self.chat_header.pack(fill='x', side='top')
        
        # Status indicator
        self.status_label = tk.Label(
            chat,
            text="",
            bg='#ecf0f1',
            fg='#7f8c8d',
            font=('Arial', 9),
            pady=5
        )
        self.status_label.pack(fill='x', side='top')
        
        # Input area - PACK FIRST (at bottom) so it's always visible
        input_container = tk.Frame(chat, bg='#ecf0f1')
        input_container.pack(fill='x', padx=20, pady=15, side='bottom')
        
        # Input frame with visible border
        input_frame = tk.Frame(input_container, bg='#bdc3c7', relief='solid', bd=2)
        input_frame.pack(fill='x')
        
        # Text entry
        self.message_entry = tk.Text(
            input_frame,
            height=3,
            font=('Arial', 11),
            relief='flat',
            wrap='word',
            bg='#ffffff',
            fg='#2c3e50',
            insertbackground='#3498db',
            padx=10,
            pady=10
        )
        self.message_entry.pack(side='left', fill='both', expand=True)
        self.message_entry.bind('<Return>', self.on_enter_key)
        self.message_entry.bind('<Shift-Return>', lambda e: None)
        
        # Send button
        self.send_button = tk.Button(
            input_frame, 
            text="Send\n📤",
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            command=self.send_message,
            width=8,
            relief='flat',
            cursor='hand2'
        )
        self.send_button.pack(side='right', fill='y', padx=2, pady=2)
        
        # Messages area - PACK LAST so it fills remaining space
        self.messages_text = scrolledtext.ScrolledText(
            chat,
            wrap=tk.WORD,
            state='disabled',
            bg='#ffffff',
            font=('Arial', 10),
            relief='flat',
            spacing3=10
        )
        self.messages_text.pack(fill='both', expand=True, padx=20, pady=(10, 0), side='top')
        
        # Message styling - IMPROVED ALIGNMENT
        # Sent messages (right-aligned) - push to the right edge
        self.messages_text.tag_configure('sent',
            background='#3498db',
            foreground='white',
            lmargin1=400,  # Large left margin pushes message to the right
            lmargin2=400,
            rmargin=10,    # Small right margin
            justify='right'
        )
        
        # Received messages (left-aligned)
        self.messages_text.tag_configure('received',
            background='#95a5a6',
            foreground='white',
            lmargin1=10,   # Small left margin
            lmargin2=10,
            rmargin=400,   # Large right margin leaves space on the right
            justify='left'
        )
        
        # Timestamp styling
        self.messages_text.tag_configure('time_sent',
            foreground='#7f8c8d',
            font=('Arial', 8),
            lmargin1=400,
            rmargin=10,
            justify='right'
        )
        
        self.messages_text.tag_configure('time_received',
            foreground='#7f8c8d',
            font=('Arial', 8),
            lmargin1=10,
            rmargin=400,
            justify='left'
        )
        
        # Info and warning messages (centered)
        self.messages_text.tag_configure('info',
            foreground='#95a5a6',
            font=('Arial', 9, 'italic'),
            justify='center'
        )
        self.messages_text.tag_configure('warning',
            foreground='#e67e22',
            font=('Arial', 9, 'italic'),
            justify='center'
        )
        
        # Placeholder text
        self.input_placeholder = "Select a user to start typing..."
        self.message_entry.insert('1.0', self.input_placeholder)
        self.message_entry.config(fg='#95a5a6', state='disabled')
        self.send_button.config(bg='#95a5a6', state='disabled')
    
    def on_enter_key(self, event):
        """Handle Enter key - send message (Shift+Enter for newline)"""
        if not self.current_chat:
            return 'break'
        
        # Check if Shift key is pressed
        if event.state & 0x0001:  # Shift is pressed
            return  # Allow default behavior (insert newline)
        else:
            # Send message and prevent default newline
            self.send_message()
            return 'break'
    
    def refresh_users(self):
        """Get list of registered users from PKI directory"""
        # Clear existing user buttons
        for widget in self.users_container.winfo_children():
            widget.destroy()
        self.user_buttons.clear()
        
        try:
            from pki_manager import PKI_PATH
            
            users = set()
            for file in PKI_PATH.glob("*.crt"):
                username = file.stem
                if username != "ca" and username != self.username:
                    users.add(username)
            
            if not users:
                tk.Label(
                    self.users_container,
                    text="No users found",
                    bg='#2c3e50',
                    fg='#95a5a6',
                    font=('Arial', 10, 'italic'),
                    pady=10
                ).pack()
                self.add_info_message_to_chat("No other users registered yet.")
                return
            
            # Create button for each user
            for user in sorted(users):
                is_online = self.active_users.get(user, False)
                
                # Create user button
                user_frame = tk.Frame(self.users_container, bg='#2c3e50')
                user_frame.pack(fill='x', padx=5, pady=2)
                
                # Status indicator (colored circle)
                status_color = '#27ae60' if is_online else '#95a5a6'
                status_canvas = tk.Canvas(user_frame, width=12, height=12, 
                                         bg='#2c3e50', highlightthickness=0)
                status_canvas.pack(side='left', padx=(5, 8))
                status_canvas.create_oval(2, 2, 10, 10, fill=status_color, outline=status_color)
                
                # Username button
                btn = tk.Button(
                    user_frame,
                    text=user,
                    bg='#2c3e50',
                    fg='white',
                    font=('Arial', 10),
                    relief='flat',
                    anchor='w',
                    cursor='hand2',
                    command=lambda u=user: self.open_chat(u)
                )
                btn.pack(side='left', fill='x', expand=True)
                
                # Store references
                self.user_buttons[user] = {
                    'frame': user_frame,
                    'canvas': status_canvas,
                    'button': btn
                }
                
                if user not in self.active_users:
                    self.active_users[user] = False
            
            # Add info to chat
            self.add_info_message_to_chat(f"Found {len(users)} registered user(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh users: {e}")
            print(f"Refresh users error: {e}")
    
    def add_info_message_to_chat(self, text):
        """Add info message to chat area"""
        if not self.current_chat:  # Only show if no chat selected
            self.messages_text.config(state='normal')
            if self.messages_text.get(1.0, 'end').strip():
                self.messages_text.insert('end', '\n')
            self.messages_text.insert('end', f"ℹ️  {text}\n", 'info')
            self.messages_text.config(state='disabled')
    
    def update_user_status(self, username, online):
        """Update user's online/offline status in the list"""
        if username == self.username:
            return
        
        self.active_users[username] = online
        
        # Update user button if it exists
        if username in self.user_buttons:
            try:
                status_color = '#27ae60' if online else '#95a5a6'
                canvas = self.user_buttons[username]['canvas']
                
                # Check if canvas still exists
                if canvas.winfo_exists():
                    canvas.delete('all')
                    canvas.create_oval(2, 2, 10, 10, fill=status_color, outline=status_color)
                else:
                    # Canvas was destroyed, remove from tracking
                    del self.user_buttons[username]
            except tk.TclError:
                # Widget was destroyed, remove from tracking
                if username in self.user_buttons:
                    del self.user_buttons[username]
            
            # Update chat header if this is current chat
            if self.current_chat == username:
                self.update_chat_status()
        else:
            # User not in list yet, refresh to add them
            if online:
                self.refresh_users()
    
    def update_chat_status(self):
        """Update the status label for current chat"""
        if not self.current_chat:
            self.status_label.config(text="")
            self.chat_header.config(bg='#3498db')  # Reset to default blue
            return
        
        # Group chat has special status
        if self.current_chat == "__GROUP_CHAT__":
            self.status_label.config(
                text="● Public room - All users can see your messages",
                fg='#27ae60'
            )
            self.chat_header.config(bg='#27ae60')
            return
        
        # Regular private chat
        self.chat_header.config(bg='#3498db')
        is_online = self.active_users.get(self.current_chat, False)
        if is_online:
            self.status_label.config(
                text="● Online - Messages delivered instantly",
                fg='#27ae60'
            )
        else:
            self.status_label.config(
                text="● Offline - Messages will be delivered when they come online",
                fg='#95a5a6'
            )
    
    def open_chat(self, username):
        """Open chat with selected user - preserves message history"""
        # Don't reload if already in this chat
        if self.current_chat == username:
            return
            
        self.current_chat = username
        self.chat_header.config(text=f"💬 Chat with {username}")
        self.update_chat_status()
        
        # Enable input and clear placeholder
        self.message_entry.config(state='normal', fg='#2c3e50')
        self.message_entry.delete(1.0, 'end')
        self.send_button.config(state='normal', bg='#3498db')
        
        # Clear and restore messages from history
        self.messages_text.config(state='normal')
        self.messages_text.delete(1.0, 'end')
        
        # Initialize history for this user if doesn't exist
        if username not in self.message_history:
            self.message_history[username] = []
            self.add_info_message(f"Started chat with {username}")
            self.add_info_message("🔒 Messages encrypted with RSA")
            
            # Show offline warning if user is offline
            if not self.active_users.get(username, False):
                self.messages_text.insert('end', 
                    "\n⚠️  User is currently offline. Your messages will be delivered when they come online.\n",
                    'warning'
                )
        else:
            # Restore message history
            for msg_data in self.message_history[username]:
                msg_type = msg_data['type']
                if msg_type == 'info':
                    self.messages_text.insert('end', f"ℹ️  {msg_data['text']}\n", 'info')
                elif msg_type == 'warning':
                    self.messages_text.insert('end', f"{msg_data['text']}\n", 'warning')
                else:
                    # Regular message
                    if self.messages_text.get(1.0, 'end').strip():
                        self.messages_text.insert('end', '\n')
                    
                    # Use appropriate timestamp tag based on message type
                    time_tag = 'time_sent' if msg_type == 'sent' else 'time_received'
                    
                    self.messages_text.insert('end', f"  {msg_data['text']}  ", msg_type)
                    self.messages_text.insert('end', f"\n{msg_data['timestamp']}\n", time_tag)
        
        self.messages_text.config(state='disabled')
        self.messages_text.see('end')
        self.message_entry.focus()
    
    def open_group_chat(self):
        """Open group chat room where everyone can see messages"""
        # Use special identifier for group chat
        if self.current_chat == "__GROUP_CHAT__":
            return
        
        self.current_chat = "__GROUP_CHAT__"
        self.chat_header.config(text="💬 Group Chat", bg='#27ae60')
        self.status_label.config(
            text="● Public room - All users can see your messages",
            fg='#27ae60'
        )
        
        # Enable input
        self.message_entry.config(state='normal', fg='#2c3e50')
        self.message_entry.delete(1.0, 'end')
        self.send_button.config(state='normal', bg='#27ae60')
        
        # Clear and restore messages from history
        self.messages_text.config(state='normal')
        self.messages_text.delete(1.0, 'end')
        
        # Initialize history for group chat if doesn't exist
        if "__GROUP_CHAT__" not in self.message_history:
            self.message_history["__GROUP_CHAT__"] = []
            self.add_info_message("Welcome to Group Chat!")
            self.add_info_message("📢 Everyone can see messages here")
        else:
            # Restore group chat history
            for msg_data in self.message_history["__GROUP_CHAT__"]:
                msg_type = msg_data['type']
                if msg_type == 'info':
                    self.messages_text.insert('end', f"ℹ️  {msg_data['text']}\n", 'info')
                elif msg_type == 'warning':
                    self.messages_text.insert('end', f"{msg_data['text']}\n", 'warning')
                elif msg_type == 'group':
                    # Group message with sender name
                    if self.messages_text.get(1.0, 'end').strip():
                        self.messages_text.insert('end', '\n')
                    
                    sender = msg_data.get('sender', 'Unknown')
                    
                    # Show sender name for group messages
                    if sender == self.username:
                        self.messages_text.insert('end', f"You: {msg_data['text']}  ", 'sent')
                        self.messages_text.insert('end', f"\n{msg_data['timestamp']}\n", 'time_sent')
                    else:
                        self.messages_text.insert('end', f"{sender}: {msg_data['text']}  ", 'received')
                        self.messages_text.insert('end', f"\n{msg_data['timestamp']}\n", 'time_received')
        
        self.messages_text.config(state='disabled')
        self.messages_text.see('end')
        self.message_entry.focus()
    
    def send_message(self):
        """Send encrypted message using RSA"""
        if not self.current_chat:
            messagebox.showwarning("No Chat", "Please select a user first")
            return
        
        message = self.message_entry.get(1.0, 'end').strip()
        if not message:
            return
        
        # Handle group chat differently
        if self.current_chat == "__GROUP_CHAT__":
            self.send_group_message(message)
            return
        
        try:
            # Get recipient's public key
            recipient_pubkey = self.pki.get_user_pubkey_path(self.current_chat)
            
            if not os.path.exists(recipient_pubkey):
                messagebox.showerror("Error",
                    f"Public key not found for {self.current_chat}\n"
                    f"They may need to register first.")
                return
            
            # Encrypt with RSA
            encrypted = encrypt(message, recipient_pubkey)
            
            # Send via RabbitMQ (queued by background worker)
            self.mq.send_message(self.current_chat, encrypted)
            
            # Display with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_message(message, 'sent', timestamp)
            
            # Show delivery status
            is_online = self.active_users.get(self.current_chat, False)
            if is_online:
                self.add_info_message("✓ Delivered")
            else:
                self.add_info_message("✓ Sent (queued for delivery)")
            
            # Clear input
            self.message_entry.delete(1.0, 'end')
            
            print(f"[SENT] To {self.current_chat}: {message}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message:\n{e}")
            print(f"Send error: {e}")
            import traceback
            traceback.print_exc()
    
    def send_group_message(self, message):
        """Send message to group chat (broadcasts to all users)"""
        try:
            # Get all registered users
            from pki_manager import PKI_PATH
            
            users = set()
            for file in PKI_PATH.glob("*.crt"):
                username = file.stem
                if username != "ca" and username != self.username:
                    users.add(username)
            
            if not users:
                self.add_info_message("⚠️ No other users registered")
                return
            
            # Broadcast to all users
            sent_count = 0
            for user in users:
                try:
                    # Get user's public key
                    user_pubkey = self.pki.get_user_pubkey_path(user)
                    
                    if os.path.exists(user_pubkey):
                        # Create group message with sender info
                        group_msg = f"[GROUP] {self.username}: {message}"
                        encrypted = encrypt(group_msg, user_pubkey)
                        self.mq.send_message(user, encrypted)
                        sent_count += 1
                except Exception as e:
                    print(f"Failed to send to {user}: {e}")
            
            # Display with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save to history with sender info
            if "__GROUP_CHAT__" not in self.message_history:
                self.message_history["__GROUP_CHAT__"] = []
            
            self.message_history["__GROUP_CHAT__"].append({
                'type': 'group',
                'sender': self.username,
                'text': message,
                'timestamp': timestamp
            })
            
            # Display in chat
            self.messages_text.config(state='normal')
            if self.messages_text.get(1.0, 'end').strip():
                self.messages_text.insert('end', '\n')
            self.messages_text.insert('end', f"You: {message}  ", 'sent')
            self.messages_text.insert('end', f"\n{timestamp}\n", 'time_sent')
            self.messages_text.config(state='disabled')
            self.messages_text.see('end')
            
            # Show status
            self.add_info_message(f"✓ Sent to {sent_count} user(s)")
            
            # Clear input
            self.message_entry.delete(1.0, 'end')
            
            print(f"[GROUP] Broadcast to {sent_count} users: {message}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send group message:\n{e}")
            print(f"Group send error: {e}")
            import traceback
            traceback.print_exc()
    
    def add_message(self, text, msg_type, timestamp):
        """Add message with timestamp and save to history"""
        self.messages_text.config(state='normal')
        
        if self.messages_text.get(1.0, 'end').strip():
            self.messages_text.insert('end', '\n')
        
        # Use appropriate timestamp tag
        time_tag = 'time_sent' if msg_type == 'sent' else 'time_received'
        
        # Add message bubble
        self.messages_text.insert('end', f"  {text}  ", msg_type)
        # Add timestamp with appropriate alignment
        self.messages_text.insert('end', f"\n{timestamp}\n", time_tag)
        
        self.messages_text.config(state='disabled')
        self.messages_text.see('end')
        
        # Save to history
        if self.current_chat:
            if self.current_chat not in self.message_history:
                self.message_history[self.current_chat] = []
            
            self.message_history[self.current_chat].append({
                'type': msg_type,
                'text': text,
                'timestamp': timestamp
            })
    
    def add_info_message(self, text):
        """Add info message and save to history"""
        self.messages_text.config(state='normal')
        if self.messages_text.get(1.0, 'end').strip():
            self.messages_text.insert('end', '\n')
        self.messages_text.insert('end', f"ℹ️  {text}\n", 'info')
        self.messages_text.config(state='disabled')
        
        # Save to history
        if self.current_chat:
            if self.current_chat not in self.message_history:
                self.message_history[self.current_chat] = []
            
            self.message_history[self.current_chat].append({
                'type': 'info',
                'text': text,
                'timestamp': None
            })
    
    def announce_presence_periodically(self):
        """Periodically announce presence to keep everyone updated"""
        try:
            self.mq.announce_presence('online')
        except Exception as e:
            print(f"Presence announcement error: {e}")
        
        # Re-announce every 30 seconds
        self.root.after(30000, self.announce_presence_periodically)
    
    def start_message_listener(self):
        """Listen for incoming messages in background"""
        def listen():
            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body.decode())
                    sender = data['from']
                    encrypted_hex = data['message']
                    encrypted_msg = bytes.fromhex(encrypted_hex)
                    
                    # Decrypt with RSA
                    my_privkey = self.pki.get_user_key_path(self.username)
                    decrypted = decrypt(encrypted_msg, my_privkey)
                    
                    # Check if it's a group message
                    is_group_msg = decrypted.startswith("[GROUP] ")
                    
                    if is_group_msg:
                        # Parse group message
                        # Format: [GROUP] sender: message
                        decrypted = decrypted[8:]  # Remove "[GROUP] " prefix
                        
                        # Display with timestamp
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        print(f"[GROUP RECEIVED] {decrypted}")
                        
                        # Store in group chat history
                        if "__GROUP_CHAT__" not in self.message_history:
                            self.message_history["__GROUP_CHAT__"] = []
                        
                        self.message_history["__GROUP_CHAT__"].append({
                            'type': 'group',
                            'sender': sender,
                            'text': decrypted.split(': ', 1)[1] if ': ' in decrypted else decrypted,
                            'timestamp': timestamp
                        })
                        
                        # Display if in group chat
                        if self.current_chat == "__GROUP_CHAT__":
                            self.root.after(0, lambda d=decrypted, t=timestamp: self.add_group_message(d, t))
                        else:
                            # Show notification
                            self.root.after(0, lambda: self.show_notification("Group Chat"))
                    else:
                        # Regular private message
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        print(f"[RECEIVED] From {sender}: {decrypted}")
                        
                        # Store message in history even if not in current chat
                        if sender not in self.message_history:
                            self.message_history[sender] = []
                        
                        self.message_history[sender].append({
                            'type': 'received',
                            'text': decrypted,
                            'timestamp': timestamp
                        })
                        
                        # Display if this is the current chat
                        if sender == self.current_chat:
                            self.root.after(0, lambda: self.add_message(
                                decrypted, 'received', timestamp
                            ))
                        else:
                            # Show notification
                            self.root.after(0, lambda: self.show_notification(sender))
                        
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    import traceback
                    traceback.print_exc()
            
            self.mq.listen(callback)
        
        threading.Thread(target=listen, daemon=True).start()
    
    def add_group_message(self, full_message, timestamp):
        """Add group message to chat display"""
        self.messages_text.config(state='normal')
        
        if self.messages_text.get(1.0, 'end').strip():
            self.messages_text.insert('end', '\n')
        
        # Display group message
        self.messages_text.insert('end', f"{full_message}  ", 'received')
        self.messages_text.insert('end', f"\n{timestamp}\n", 'time_received')
        
        self.messages_text.config(state='disabled')
        self.messages_text.see('end')
    
    def start_presence_listener(self):
        """Listen for presence announcements"""
        def listen():
            try:
                import pika
                from rabbitmq_manager import RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS
                
                credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
                parameters = pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=5672,
                    credentials=credentials,
                    heartbeat=600
                )
                
                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()
                
                # Bind to presence exchange
                channel.exchange_declare(exchange='chat_presence', exchange_type='fanout')
                result = channel.queue_declare(queue='', exclusive=True)
                queue_name = result.method.queue
                channel.queue_bind(exchange='chat_presence', queue=queue_name)
                
                def callback(ch, method, properties, body):
                    try:
                        data = json.loads(body.decode())
                        user = data['user']
                        status = data['status']
                        
                        is_online = (status == 'online')
                        
                        print(f"Presence update: {user} is now {status}")
                        
                        # Update UI in main thread
                        self.root.after(0, lambda: self.update_user_status(user, is_online))
                        
                    except Exception as e:
                        print(f"Error processing presence: {e}")
                
                channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
                print("✓ Listening for presence updates...")
                channel.start_consuming()
                
            except Exception as e:
                print(f"Presence listener error: {e}")
        
        threading.Thread(target=listen, daemon=True).start()
    
    def show_notification(self, sender):
        """Show notification for new message"""
        self.root.title(f"💬 New message from {sender}")
        self.root.after(3000, lambda: self.root.title(f"P2P Chat Room - {self.username}"))
        self.root.bell()
    
    def logout(self):
        """Logout and return to login"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.on_closing()
    
    def on_closing(self):
        """Handle window close"""
        try:
            self.mq.announce_presence('offline')
            self.mq.close()
        except:
            pass
        
        self.root.destroy()
        
        from ui.login import LoginApp
        LoginApp().run()
    
    def run(self):
        """Start chat application"""
        self.root.mainloop()