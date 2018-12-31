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
