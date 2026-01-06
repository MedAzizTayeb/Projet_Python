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
        self.active_users = {}  # Changed to dict to track online status
        
        self.pki = PKIManager()
        self.mq = MQ(username)
        
        self.root = tk.Tk()
        self.root.title(f"P2P Chat Room - {username}")
        self.root.geometry("900x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.create_widgets()
        self.start_message_listener()
        self.start_presence_listener()
        
        # Announce presence after UI is ready
        self.root.after(500, lambda: self.mq.announce_presence('online'))
    
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
        
        # Active users label
        tk.Label(sidebar, text="Users",
                bg='#34495e', fg='white',
                font=('Arial', 11, 'bold'),
                pady=10).pack(fill='x')
        
        # User list
        list_frame = tk.Frame(sidebar, bg='#34495e')
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.user_listbox = tk.Listbox(
            list_frame,
            bg='#2c3e50',
            fg='white',
            font=('Arial', 11),
            selectbackground='#3498db',
            highlightthickness=0
        )
        self.user_listbox.pack(fill='both', expand=True)
        self.user_listbox.bind('<<ListboxSelect>>', self.on_user_select)
        
        # Refresh users button
        tk.Button(sidebar, text="🔄 Refresh Users",
                 bg='#2c3e50', fg='white',
                 font=('Arial', 10),
                 command=self.refresh_users,
                 relief='flat').pack(fill='x', padx=10, pady=(10, 5))
        
        # Logout button
        tk.Button(sidebar, text="🚪 Logout",
                 bg='#e74c3c', fg='white',
                 font=('Arial', 10),
                 command=self.logout,
                 relief='flat').pack(fill='x', padx=10, pady=5)
    
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
        self.chat_header.pack(fill='x')
        
        # Status indicator
        self.status_label = tk.Label(
            chat,
            text="",
            bg='#ecf0f1',
            fg='#7f8c8d',
            font=('Arial', 9),
            pady=5
        )
        self.status_label.pack(fill='x')
        
        # Messages area
        self.messages_text = scrolledtext.ScrolledText(
            chat,
            wrap=tk.WORD,
            state='disabled',
            bg='#ffffff',
            font=('Arial', 10),
            relief='flat',
            spacing3=10
        )
        self.messages_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Message styling
        self.messages_text.tag_configure('sent',
            background='#3498db',
            foreground='white',
            lmargin1=200, lmargin2=200, rmargin=20
        )
        self.messages_text.tag_configure('received',
            background='#95a5a6',
            foreground='white',
            lmargin1=20, lmargin2=20, rmargin=200
        )
        self.messages_text.tag_configure('time',
            foreground='#7f8c8d',
            font=('Arial', 8)
        )
        self.messages_text.tag_configure('info',
            foreground='#95a5a6',
            font=('Arial', 9, 'italic')
        )
        self.messages_text.tag_configure('warning',
            foreground='#e67e22',
            font=('Arial', 9, 'italic')
        )
        
        # Input area
        input_frame = tk.Frame(chat, bg='#ecf0f1')
        input_frame.pack(fill='x', padx=20, pady=20)
        
        self.message_entry = tk.Text(
            input_frame,
            height=3,
            font=('Arial', 10),
            relief='solid',
            borderwidth=1,
            wrap='word'
        )
        self.message_entry.pack(side='left', fill='both', expand=True)
        self.message_entry.bind('<Return>', self.on_enter_key)
        self.message_entry.bind('<Shift-Return>', lambda e: None)
        
        tk.Button(input_frame, text="Send",
                 bg='#3498db', fg='white',
                 font=('Arial', 10, 'bold'),
                 command=self.send_message,
                 width=10).pack(side='right', fill='y', padx=(10, 0))
    
    def on_enter_key(self, event):
        """Handle Enter key - send message (Shift+Enter for newline)"""
        # Check if Shift key is pressed
        if event.state & 0x0001:  # Shift is pressed
            return  # Allow default behavior (insert newline)
        else:
            # Send message and prevent default newline
            self.send_message()
            return 'break'
    
    def refresh_users(self):
        """Get list of registered users from PKI directory"""
        self.user_listbox.delete(0, 'end')
        
        try:
            # Get all user certificates from PKI directory
            from pki_manager import PKI_PATH
            
            users = set()
            for file in PKI_PATH.glob("*.crt"):
                username = file.stem
                if username != "ca" and username != self.username:
                    users.add(username)
            
            # Add to listbox with online/offline status
            for user in sorted(users):
                # Check if we know their online status
                is_online = self.active_users.get(user, False)
                icon = "🟢" if is_online else "⚫"
                self.user_listbox.insert('end', f"{icon} {user}")
                
                # Store in active_users dict
                if user not in self.active_users:
                    self.active_users[user] = False
            
            if not users:
                messagebox.showinfo("No Users", 
                    "No other users found.\n"
                    "Users need to register first.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh users: {e}")
    
    def update_user_status(self, username, online):
        """Update user's online/offline status in the list"""
        if username == self.username:
            return
        
        self.active_users[username] = online
        
        # Update listbox
        for i in range(self.user_listbox.size()):
            item = self.user_listbox.get(i)
            user = item.replace('🟢', '').replace('⚫', '').strip()
            
            if user == username:
                icon = "🟢" if online else "⚫"
                self.user_listbox.delete(i)
                self.user_listbox.insert(i, f"{icon} {username}")
                
                # Update chat header if this is current chat
                if self.current_chat == username:
                    self.update_chat_status()
                break
        else:
            # User not in list yet, add them
            icon = "🟢" if online else "⚫"
            self.user_listbox.insert('end', f"{icon} {username}")
    
    def update_chat_status(self):
        """Update the status label for current chat"""
        if not self.current_chat:
            self.status_label.config(text="")
            return
        
        is_online = self.active_users.get(self.current_chat, False)
        if is_online:
            self.status_label.config(
                text="🟢 Online - Messages delivered instantly",
                fg='#27ae60'
            )
        else:
            self.status_label.config(
                text="⚫ Offline - Messages will be delivered when they come online",
                fg='#7f8c8d'
            )
    
    def on_user_select(self, event):
        """Handle user selection - open discussion area"""
        selection = self.user_listbox.curselection()
        if selection:
            user_text = self.user_listbox.get(selection[0])
            username = user_text.replace('🟢', '').replace('⚫', '').strip()
            self.open_chat(username)
    
    def open_chat(self, username):
        """Open chat with selected user"""
        self.current_chat = username
        self.chat_header.config(text=f"💬 Chat with {username}")
        self.update_chat_status()
        
        self.messages_text.config(state='normal')
        self.messages_text.delete(1.0, 'end')
        self.add_info_message(f"Started chat with {username}")
        self.add_info_message("🔒 Messages encrypted with RSA")
        
        # Show offline warning if user is offline
        if not self.active_users.get(username, False):
            self.messages_text.insert('end', 
                "\n⚠️  User is currently offline. Your messages will be delivered when they come online.\n",
                'warning'
            )
        
        self.messages_text.config(state='disabled')
        self.message_entry.focus()
    
    def send_message(self):
        """Send encrypted message using RSA"""
        if not self.current_chat:
            messagebox.showwarning("No Chat", "Please select a user")
            return
        
        message = self.message_entry.get(1.0, 'end').strip()
        if not message:
            return
        
        try:
            # Get recipient's public key
            recipient_pubkey = self.pki.get_user_pubkey_path(self.current_chat)
            
            # Encrypt with RSA
            encrypted = encrypt(message, recipient_pubkey)
            
            # Send via RabbitMQ (will be queued if user is offline)
            self.mq.send_message(self.current_chat, encrypted)
            
            # Display with date/time
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.add_message(message, 'sent', timestamp)
            
            # Show delivery status
            is_online = self.active_users.get(self.current_chat, False)
            if is_online:
                self.add_info_message("✓ Delivered")
            else:
                self.add_info_message("✓ Sent (will be delivered when user comes online)")
            
            self.message_entry.delete(1.0, 'end')
            
        except FileNotFoundError:
            messagebox.showerror("Error",
                f"Public key not found for {self.current_chat}\n"
                f"Make sure they are registered.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send: {e}")
    
    def add_message(self, text, msg_type, timestamp):
        """Add message with date/time"""
        self.messages_text.config(state='normal')
        
        if self.messages_text.get(1.0, 'end').strip():
            self.messages_text.insert('end', '\n')
        
        # Add message
        self.messages_text.insert('end', f"  {text}  ", msg_type)
        # Add date/time
        self.messages_text.insert('end', f"\n{timestamp}", 'time')
        
        self.messages_text.config(state='disabled')
        self.messages_text.see('end')
    
    def add_info_message(self, text):
        """Add info message"""
        self.messages_text.config(state='normal')
        if self.messages_text.get(1.0, 'end').strip():
            self.messages_text.insert('end', '\n')
        self.messages_text.insert('end', f"ℹ️  {text}\n", 'info')
        self.messages_text.config(state='disabled')
    
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
                    
                    # Display with date/time
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if sender == self.current_chat:
                        self.root.after(0, lambda: self.add_message(
                            decrypted, 'received', timestamp
                        ))
                    else:
                        # Show notification
                        self.root.after(0, lambda: self.show_notification(sender))
                        
                except Exception as e:
                    print(f"Error receiving message: {e}")
            
            self.mq.listen(callback)
        
        threading.Thread(target=listen, daemon=True).start()
    
    def start_presence_listener(self):
        """Listen for presence announcements (online/offline)"""
        def listen():
            try:
                # Create separate connection for presence
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
                        self.root.after(0, lambda: self.update_user_status(user, is_online))
                        
                    except Exception as e:
                        print(f"Error processing presence: {e}")
                
                channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
                print("Listening for presence updates...")
                channel.start_consuming()
                
            except Exception as e:
                print(f"Presence listener error: {e}")
        
        threading.Thread(target=listen, daemon=True).start()
    
    def show_notification(self, sender):
        """Show notification for new message"""
        self.root.title(f"💬 New message from {sender}")
        self.root.after(3000, lambda: self.root.title(f"P2P Chat Room - {self.username}"))
        
        # Play system bell
        self.root.bell()
    
    def logout(self):
        """Disconnect and exit application"""
        if messagebox.askyesno("Logout", "Exit application?"):
            self.on_closing()
    
    def on_closing(self):
        """Close and return to login"""
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