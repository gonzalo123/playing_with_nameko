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
