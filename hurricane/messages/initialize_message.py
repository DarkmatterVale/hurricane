from hurricane.messages import Message
from hurricane.messages import MessageTypes

class InitializeMessage(Message):
    """
    Simple initialization message which is sent to inform of the
    task port and a task completion port
    """

    def __init__(self, **kwargs):
        """
        Initialize the InitializeMessage
        """
        super(InitializeMessage, self).__init__(MessageTypes.INITIALIZE_MSG)

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
