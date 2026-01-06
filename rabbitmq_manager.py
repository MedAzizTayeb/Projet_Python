import pika
import json
import threading
import time
from queue import Queue

RABBITMQ_HOST = "192.168.92.1"
RABBITMQ_USER = "chatuser"  
RABBITMQ_PASS = "chat123" 

class MQ:
    def __init__(self, user):
        """Initialize RabbitMQ connection (AMQP protocol)"""
        self.username = user
        self.conn = None
        self.channel = None
        self.consuming = False
        self._lock = threading.Lock()
        self._send_queue = Queue()
        self._send_thread = None
        
        self._connect()
        self._start_send_worker()
    
    def _start_send_worker(self):
        """Start background thread to handle sending messages"""
        def worker():
            while True:
                try:
                    # Get message from queue (blocking with timeout)
                    item = self._send_queue.get(timeout=1)
                    
                    if item is None:  # Shutdown signal
                        break
                    
                    to_user, encrypted_msg = item
                    self._send_message_internal(to_user, encrypted_msg)
                    self._send_queue.task_done()
                    
                    # Small delay to prevent overwhelming connection
                    time.sleep(0.05)
                    
                except Exception as e:
                    if "Empty" not in str(type(e).__name__):
                        print(f"Send worker error: {e}")
                    continue
        
        self._send_thread = threading.Thread(target=worker, daemon=True)
        self._send_thread.start()
    
    def _connect(self):
        """Create connection to RabbitMQ with better parameters"""
        try:
            # Create credentials
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            
            # Connection parameters with improved settings
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=5672,
                credentials=credentials,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10,
                heartbeat=300,
                blocked_connection_timeout=300,
                frame_max=131072
            )
            
            self.conn = pika.BlockingConnection(parameters)
            self.channel = self.conn.channel()
            
            # Set QoS to prevent overwhelming
            self.channel.basic_qos(prefetch_count=10)
            
            # Create user's personal queue
            self.queue_name = f"user_{self.username}"
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Create presence exchange
            self.channel.exchange_declare(
                exchange='chat_presence',
                exchange_type='fanout',
                durable=False
            )
            
            print(f"✓ Connected to RabbitMQ as {RABBITMQ_USER}")
            
        except pika.exceptions.ProbableAuthenticationError:
            raise Exception(
                f"RabbitMQ Authentication Failed!\n\n"
                f"Current credentials:\n"
                f"  Username: {RABBITMQ_USER}\n"
                f"  Password: {RABBITMQ_PASS}\n\n"
                f"Solutions:\n"
                f"1. Use default guest/guest (only works on localhost)\n"
                f"2. Create a new user on RabbitMQ host:\n"
                f"   rabbitmqctl add_user myuser mypassword\n"
                f"   rabbitmqctl set_permissions -p / myuser '.*' '.*' '.*'\n"
                f"3. Update RABBITMQ_USER and RABBITMQ_PASS in rabbitmq_manager.py"
            )
        except pika.exceptions.AMQPConnectionError as e:
            raise Exception(
                f"Cannot connect to RabbitMQ at {RABBITMQ_HOST}:5672\n\n"
                f"Please check:\n"
                f"1. RabbitMQ is running\n"
                f"2. Firewall allows port 5672\n"
                f"3. RabbitMQ is listening on 0.0.0.0:5672\n\n"
                f"Error: {e}"
            )
    
    def _ensure_connection(self):
        """Ensure connection is alive, reconnect if needed"""
        with self._lock:
            try:
                if self.conn is None or self.conn.is_closed or not self.conn.is_open:
                    print("Connection closed, reconnecting...")
                    self._connect()
                elif self.channel is None or self.channel.is_closed or not self.channel.is_open:
                    print("Channel closed, recreating...")
                    self.channel = self.conn.channel()
                    self.channel.basic_qos(prefetch_count=10)
            except Exception as e:
                print(f"Reconnection error: {e}")
                time.sleep(1)
                raise
    
    def send_message(self, to_user, encrypted_msg):
        """Queue message for sending (non-blocking)"""
        self._send_queue.put((to_user, encrypted_msg))
    
    def _send_message_internal(self, to_user, encrypted_msg):
        """Internal method to actually send message"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self._ensure_connection()
                
                to_queue = f"user_{to_user}"
                self.channel.queue_declare(queue=to_queue, durable=True)
                
                message = json.dumps({
                    'from': self.username,
                    'message': encrypted_msg.hex()
                })
                
                self.channel.basic_publish(
                    exchange='',
                    routing_key=to_queue,
                    body=message,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                return  # Success
                
            except Exception as e:
                retry_count += 1
                print(f"Send error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    time.sleep(0.5)
                    try:
                        self._connect()
                    except:
                        pass
                else:
                    print(f"Failed to send message after {max_retries} attempts")
    
    def listen(self, callback):
        """Listen for incoming messages with improved error handling"""
        self.consuming = True
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.consuming:
            try:
                self._ensure_connection()
                
                def safe_callback(ch, method, properties, body):
                    try:
                        callback(ch, method, properties, body)
                    except Exception as e:
                        print(f"Error in message callback: {e}")
                
                consumer_tag = self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=safe_callback,
                    auto_ack=True
                )
                
                print(f"Listening on queue: {self.queue_name}")
                consecutive_errors = 0
                
                while self.consuming:
                    try:
                        self.conn.process_data_events(time_limit=1)
                        
                        if self.conn.is_closed:
                            print("Connection closed during listening")
                            break
                            
                    except KeyboardInterrupt:
                        print("Interrupted by user")
                        self.consuming = False
                        break
                    except Exception as e:
                        print(f"Error during message processing: {e}")
                        break
                
                try:
                    if self.channel and self.channel.is_open:
                        self.channel.basic_cancel(consumer_tag)
                except:
                    pass
                    
            except Exception as e:
                consecutive_errors += 1
                print(f"Listen error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print("Too many consecutive errors, stopping listener")
                    break
                
                if self.consuming:
                    wait_time = min(3 * consecutive_errors, 15)
                    print(f"Reconnecting in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    break
    
    def announce_presence(self, status='online'):
        """Announce user presence (online/offline)"""
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self._ensure_connection()
                
                message = json.dumps({
                    'user': self.username,
                    'status': status
                })
                
                self.channel.basic_publish(
                    exchange='chat_presence',
                    routing_key='',
                    body=message,
                    properties=pika.BasicProperties(
                        delivery_mode=1,
                        content_type='application/json'
                    )
                )
                return
                
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(0.5)
                    try:
                        self._connect()
                    except:
                        pass
    
    def close(self):
        """Close RabbitMQ connection gracefully"""
        self.consuming = False
        
        # Stop send worker
        if self._send_thread and self._send_thread.is_alive():
            self._send_queue.put(None)  # Shutdown signal
            self._send_thread.join(timeout=2)
        
        try:
            if self.conn and self.conn.is_open:
                self.announce_presence('offline')
                time.sleep(0.2)
        except Exception as e:
            print(f"Error announcing offline status: {e}")
        
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
        except:
            pass
        
        try:
            if self.conn and self.conn.is_open:
                self.conn.close()
        except:
            pass