import pika
import sys
import logging
import yaml

logging.basicConfig(level=logging.WARNING)


def event(queue_name, data):
    with open("config.yaml", 'r') as stream:
        parameters = pika.URLParameters(yaml.load(stream)['AMQP_URI'])
    logging.info("emit message: {} to queue: {}".format(data, queue_name))
    connection = pika.BlockingConnection(parameters=parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange='', routing_key=queue_name, body=data)
    connection.close()


if __name__ == '__main__':
    event('queue3', sys.argv[1])
