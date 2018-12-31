from nameko.extensions import DependencyProvider
from pika.adapters.blocking_connection import BlockingConnection
import pika


class Rabbit:
    def __init__(self, conn: BlockingConnection):
        self.conn = conn

    def get_connection(self) -> BlockingConnection:
        return self.conn

    def close(self):
        self.conn.close()

    def publish_to_queue(self, queue_name, data, headers=None):
        headers = headers if headers is None else {}
        channel = self.conn.channel()
        channel.queue_declare(queue=queue_name)

        channel.basic_publish(exchange='',
                              routing_key=queue_name,
                              body=data,
                              properties=pika.BasicProperties(
                                  headers=headers
                              ))
        return self


class RabbitService(DependencyProvider):

    def get_dependency(self, worker_ctx):
        uri = self.container.config['AMQP_URI']
        return Rabbit(pika.BlockingConnection(pika.URLParameters(uri)))
