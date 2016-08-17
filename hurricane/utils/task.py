from datetime import datetime

class Task:

    def __init__(self, **kwargs):
        self.starttime = kwargs.get('starttime', datetime.now())
        self.return_port = kwargs.get('return_port', None)
        self.task_id = kwargs.get('task_id', None)
        self.data = kwargs.get('data', None)

        self.generated_data = None

    def get_generated_data(self):
        """
        Return the generated data for this task.
        """
        return self.generated_data

    def set_generated_data(self, generated_data):
        """
        Set the generated data for this task.
        """
        self.generated_data = generated_data

    def get_starttime(self):
        """
        Return the start time for this task.
        """
        return self.starttime

    def get_task_id(self):
        """
        Return the task id for this task.
        """
        return self.task_id

    def get_data(self):
        """
        Return the data for this task.
        """
        return self.data

    def get_return_port(self):
        """
        Return the port that data should be sent back to once the task has
        been completed.
        """
        return self.return_port
