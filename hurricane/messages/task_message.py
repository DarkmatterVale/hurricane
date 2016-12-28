from hurricane.messages import Message
from hurricane.messages import MessageTypes

class TaskMessage(Message):
    """
    Provides a class that acts as a wrapper class for sending tasks
    between nodes on a network
    """

    def __init__(self, task):
        """
        Initialize the TaskMessage
        """
        super(TaskMessage, self).__init__(MessageTypes.TASK)

        self.task = task

    def get_task(self):
        """
        Return the task that this class is acting as a wrapper for
        """
        return self.task
