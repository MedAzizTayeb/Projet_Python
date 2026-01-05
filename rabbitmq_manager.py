import pika
import json

RABBITMQ_HOST = "192.168.92.1"

class MQ:
    def __init__(self, user):
        """Initialize RabbitMQ connection for user"""
        self.username = user
        self.conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST)
        )
        self.channel = self.conn.channel()
        
        # Declare user's personal queue
        self.queue_name = f"user_{user}"
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        
        # Declare presence exchange for active users
        self.channel.exchange_declare(
            exchange='chat_presence',
            exchange_type='fanout'
        )
    
    def send_message(self, to_user, encrypted_msg):
        """Send encrypted message to another user"""
        to_queue = f"user_{to_user}"
        
        # Ensure recipient queue exists
        self.channel.queue_declare(queue=to_queue, durable=True)
        
        # Create message with metadata
        message = json.dumps({
            'from': self.username,
            'message': encrypted_msg.hex(),  # Convert bytes to hex string
            'timestamp': None  # Will be added by receiver
        })
        
        self.channel.basic_publish(
            exchange='',
            routing_key=to_queue,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
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
    
    def get_active_users(self):
        """
        Get list of active users by checking existing queues.
        Note: This is a simplified version. In production, 
        you'd use a proper presence system.
        """
        # This requires RabbitMQ Management API or a dedicated presence service
        # For now, return empty list - implement with management API if needed
        return []
    
    def close(self):
        """Close connection"""
        if self.conn and not self.conn.is_closed:
            self.announce_presence('offline')
            self.conn.close()