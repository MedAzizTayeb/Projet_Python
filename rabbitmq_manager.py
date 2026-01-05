import pika
import json

RABBITMQ_HOST = "192.168.92.1"
RABBITMQ_USER = "chatuser"  
RABBITMQ_PASS = "chat123" 

class MQ:
    def __init__(self, user):
        """Initialize RabbitMQ connection (AMQP protocol)"""
        self.username = user
        
        # Create credentials
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        
        # Connection parameters with authentication
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=5672,
            credentials=credentials,
            connection_attempts=3,
            retry_delay=2,
            socket_timeout=5
        )
        
        try:
            self.conn = pika.BlockingConnection(parameters)
            self.channel = self.conn.channel()
            
            # Create user's personal queue
            self.queue_name = f"user_{user}"
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
    
    def send_message(self, to_user, encrypted_msg):
        """Send encrypted message to another user via RabbitMQ"""
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
    
    def listen(self, callback):
        """Listen for incoming messages"""
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=callback,
            auto_ack=True
        )
        self.channel.start_consuming()
    
    def announce_presence(self, status='online'):
        """Announce user presence (online/offline)"""
        message = json.dumps({
            'user': self.username,
            'status': status
        })
        self.channel.basic_publish(
            exchange='chat_presence',
            routing_key='',
            body=message
        )
    
    def close(self):
        """Close RabbitMQ connection"""
        if self.conn and not self.conn.is_closed:
            self.announce_presence('offline')
            self.conn.close()