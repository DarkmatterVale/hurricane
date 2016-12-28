from hurricane.messages import MessageTypes
from hurricane.messages import Message

class NewNodeMessage(Message):
    """
    Provides a wrapper class for new node identification
    """

    def __init__(self, addr, task_port, task_completion_port):
        """
        Initialize the new node message
        """
        super(NewNodeMessage, self).__init__(MessageTypes.NEW_NODE)

        self.addr = addr
        self.task_port = task_port
        self.task_completion_port = task_completion_port

    def get_addr(self):
        """
        Return the addr
        """
        return self.addr

    def get_task_port(self):
        """
        Return the task port
        """
        return self.task_port

    def get_task_completion_port(self):
        """
        Return the task completion port
        """
        return self.task_completion_port
