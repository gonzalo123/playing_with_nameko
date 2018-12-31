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
