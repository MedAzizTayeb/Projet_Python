import pika
import json
import threading
import time

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
        
        self._connect()
    
    def _connect(self):
        """Create connection to RabbitMQ"""
        try:
            # Create credentials
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            
            # Connection parameters with authentication
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=5672,
                credentials=credentials,
                connection_attempts=3,
                retry_delay=2,
                socket_timeout=10,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.conn = pika.BlockingConnection(parameters)
            self.channel = self.conn.channel()
            
            # Create user's personal queue
            self.queue_name = f"user_{self.username}"
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Create presence exchange
            self.channel.exchange_declare(
                exchange='chat_presence',
                exchange_type='fanout'
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
            if self.conn is None or self.conn.is_closed:
                print("Reconnecting to RabbitMQ...")
                self._connect()
    
    def send_message(self, to_user, encrypted_msg):
        """Send encrypted message to another user via RabbitMQ"""
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
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as e:
            print(f"Send error: {e}")
            # Try to reconnect and send again
            try:
                self._connect()
                self.channel.basic_publish(
                    exchange='',
                    routing_key=to_queue,
                    body=message,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            except:
                raise
    
    def listen(self, callback):
        """Listen for incoming messages"""
        self.consuming = True
        
        while self.consuming:
            try:
                self._ensure_connection()
                
                # Set up consumer
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=callback,
                    auto_ack=True
                )
                
                # Start consuming with timeout
                print(f"Listening on queue: {self.queue_name}")
                while self.consuming and not self.conn.is_closed:
                    self.conn.process_data_events(time_limit=1)
                    
            except Exception as e:
                print(f"Listen error: {e}")
                if self.consuming:
                    print("Reconnecting in 5 seconds...")
                    time.sleep(5)
                else:
                    break
    
    def announce_presence(self, status='online'):
        """Announce user presence (online/offline)"""
        try:
            self._ensure_connection()
            
            message = json.dumps({
                'user': self.username,
                'status': status
            })
            self.channel.basic_publish(
                exchange='chat_presence',
                routing_key='',
                body=message
            )
        except Exception as e:
            print(f"Presence announcement error: {e}")
    
    def close(self):
        """Close RabbitMQ connection"""
        self.consuming = False
        try:
            if self.conn and not self.conn.is_closed:
                self.announce_presence('offline')
                self.conn.close()
        except:
            pass