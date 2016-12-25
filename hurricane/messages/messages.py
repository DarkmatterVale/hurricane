from abc import ABCMeta
from abc import abstractmethod

class Message(object):
    """
    Provide an abstract base class for all messages to extend
    """

    __metaclass__ = ABCMeta

    def __init__(self, message):
        """
        Provide a default interface for instantiating with
        a message
        """
        self.message = message

    def get_message(self):
        """
        Returns the message that this message contains
        """
        return self.message

class MessageTypes:
    HEARTBEAT          = "HEARTBEAT_REQUESTED"
    HEARTBEAT_RESPONSE = "RECOGNIZE_HEARTBEAT"

    INITIALIZE_MSG     = "INITIALIZE"
