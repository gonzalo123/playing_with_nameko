## Communications between nameko microservices and non-python microservices asynchronously.

In my last projects I've playing with microservices. Mostly written in Python. Months ago I discovered nameko. It's great. I've written a couple of posts about it. Nameko relies on RabbitMQ and basically it does the common operations that I normally do when I work with microservices in a very clean way. That's cool but I sometimes need to work with other services (micro or macro) that they aren't written in Python. With nameko I can create easily http gateways. And also we can send http requests from our nameko microservices to the rest of the world. It works but it's synchronous. If synchronous way fits to your needs it's perfect, but sometimes we need asynchronous way. What can we do?

Since nameko relies on RabbitMQ we can use nameko's queues and exchanges outside nameko. It should be possible but afaik nameko encapsulates its messages with one kind of encoder that I don't understand. Years ago I've tried to do one kind of reverse engineering to figure out how to encode those messages. But now I'm getting older and I don't want to spend so much time trying to discover it. Let me show you how I've done it

### From nameko to another services
Here we only need to send one RabbitMQ message. To do it, I've created a simple dependency Provider in Nameko

```python
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

```

Here a simple example of nameko microservice that sends a meesage to one queue each 3 seconds

```python
from nameko.timer import timer
from ext.rabbit import RabbitService, Rabbit
from dotenv import load_dotenv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path="{}/.env".format(current_dir))


class Timer:
    name = 'timer_service'

    rabbit: Rabbit = RabbitService()

    @timer(interval=3)
    def ping(self):
        self.rabbit.publish_to_queue(queue_name='queue3',
                                     data='ping').close()
```

### From another services to nameko

In the opposite way I've found two possible solutions. 

The first one is to create a simple RabbitMQ consumer listening to one queue (acting as a proxy) and redirecting messages to nameko.
 
```python
import pika
import logging
import yaml
from nameko.standalone.rpc import ClusterRpcProxy

logging.basicConfig(level=logging.WARNING)
queue_name = 'queue3'

with open("config.yaml", 'r') as stream:
    amqp_uri = yaml.load(stream)['AMQP_URI']

parameters = pika.URLParameters(amqp_uri)

config = {'AMQP_URI': amqp_uri}

def callback(ch, method, properties, body):
    logging.warning("rabbit receive: {}".format(body))
    with ClusterRpcProxy(config) as rpc:
        rpc.listener_example.remote_method(body.decode('utf-8'))


broker_connection = pika.BlockingConnection(parameters=parameters)
channel = broker_connection.channel()
channel.queue_declare(queue=queue_name)

channel.basic_consume(consumer_callback=callback,
                      queue=queue_name,
                      no_ack=True)
channel.basic_qos(prefetch_count=1)
channel.start_consuming()
```

The other way is using a Nameko Entrypoint

```python
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
```

Now we can use a nameko service listening to the queue via our nameko entrypoint

```python
from nameko.events import EventDispatcher
from ext.entrypoint import listener
import logging
from dotenv import load_dotenv
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path="{}/.env".format(current_dir))


class Listener:
    name = 'listener_service'
    dispatcher = EventDispatcher()

    @listener(queue='queue3')
    def handle(self, body):
        logging.info("listener_service listen via entrypoint: {}".format(body))
        self.dispatcher("event_type", body.decode('utf-8'))
```