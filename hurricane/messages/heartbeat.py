from hurricane.messages import Message
from hurricane.messages import MessageTypes

class HeartbeatMessage(Message):
    """
    Simple heartbeat reminder that allows the master node to determine if
    the slave node is still connected to the hurricane network
    """

    def __init__(self):
        """
        Initialize the HeartbeatMessage
        """
        super(HeartbeatMessage, self).__init__(MessageTypes.HEARTBEAT)
