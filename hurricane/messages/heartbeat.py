from hurricane.messages import Message
from hurricane.messages import MessageTypes

class HeartbeatMessage(Message):
    """
    Simple heartbeat reminder that tells the slave node to send a
    HeartbeatResponseMessage object to inform the master node
    that it is still connected to the network
    """

    def __init__(self):
        """
        Initialize the HeartbeatMessage
        """
        super(HeartbeatMessage, self).__init__(MessageTypes.HEARTBEAT)

class HeartbeatResponseMessage(Message):
    """
    Simple heartbeat response message which is sent when a
    HeartbeatMessage is sent to a node
    """

    def __init__(self):
        """
        Initialize the HeartbeatResponseMessage
        """
        super(HeartbeatResponseMessage, self).__init__(MessageTypes.HEARTBEAT_RESPONSE)
