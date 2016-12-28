from hurricane.messages import Message
from hurricane.messages import MessageTypes

class TaskManagementMessage(Message):
    """
    Simple initialization message which is sent to inform of the
    task port and a task completion port
    """

    def __init__(self, **kwargs):
        """
        Initialize the InitializeMessage
        """
        super(TaskManagementMessage, self).__init__(MessageTypes.INITIALIZE_MSG)

        self.task_port = kwargs.get("task_port", None)
        self.task_completion_port = kwargs.get("task_completion_port", None)

    def get_task_port(self):
        """
        Returns the task port.
        """
        return self.task_port

    def get_task_completion_port(self):
        """
        Returns the task completion port.
        """
        return self.task_completion_port

class NodeInitializeMessage(Message):
    """
    Initialization message that is sent from a slove node to a master
    node to provide necessary information
    """

    def __init__(self, addr, cpu_count):
        """
        Initialize the NodeInitializeMessage
        """
        super(NodeInitializeMessage, self).__init__(MessageTypes.INITIALIZE_NODE)

        self.addr = addr
        self.cpu_count = cpu_count

    def get_addr(self):
        """
        Return the addr
        """
        return self.addr

    def get_cpu_count(self):
        """
        Returns the CPU count of the node
        """
        return self.cpu_count
