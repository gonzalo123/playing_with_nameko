from nameko.events import event_handler
import logging
from dotenv import load_dotenv
import os
from nameko.rpc import rpc

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path="{}/.env".format(current_dir))


class ListenerExample:
    name = "listener_example"

    @rpc
    def remote_method(self, payload):
        logging.info("listener_example received: {}".format(payload))

    @event_handler("listener_service", "event_type")
    def handle_event(self, payload):
        logging.info("listener_example received: {}".format(payload))
