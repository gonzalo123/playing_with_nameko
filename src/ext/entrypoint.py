from nameko.extensions import Entrypoint
import pika
from functools import partial
import os


class QueueListener(Entrypoint):
    channel = None

    def __init__(self, queue, **kwargs):
        self.queue = queue
        super(QueueListener, self).__init__(**kwargs)

    def setup(self):
        pass

    def start(self):
        self.container.spawn_managed_thread(self.run, identifier="QueueListener.run")

    def run(self):
        broker_connection = pika.BlockingConnection(pika.URLParameters(os.getenv('AMQP_URI')))

        channel = broker_connection.channel()
        channel.queue_declare(queue=self.queue)

        channel.basic_consume(consumer_callback=self.handle_message,
                              queue=self.queue,
                              no_ack=False)
        channel.basic_qos(prefetch_count=1)
        channel.start_consuming()

    def handle_message(self, ch, method, properties, body):
        handle_result = partial(self.handle_result)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        args = (body,)
        kwargs = {}

        self.container.spawn_worker(
            self, args, kwargs, handle_result=handle_result
        )

    def handle_result(self, worker_ctx, result, exc_info):
        return result, exc_info


listener = QueueListener.decorator
