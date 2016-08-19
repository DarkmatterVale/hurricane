import pickle
import struct

def read_data(connection):
    """
    Read a data from a socket.

    @returns the data received from the socket
    """
    raw_msglen = connection.recv(4)
    msglen = struct.unpack('>I', raw_msglen)[0]

    data = connection.recv(msglen)
    data = pickle.loads(data)

    return data

def encode_data(data):
    """
    Encode data into a transmittable message.

    @returns the encoded data
    """
    msg = pickle.dumps(data)
    msg = struct.pack('>I', len(msg)) + msg

    return msg

class InitializeMessage:

    def __init__(self, **kwargs):
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
