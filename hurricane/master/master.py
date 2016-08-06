import socket
from hurricane.utils import encode_data

class MasterNode:

    def __init__(self, **kwargs):
        self.initialize_port = kwargs.get('initialize_port', 12223)
        self.max_connections = kwargs.get('connections', 20)
        self.debug = kwargs.get('debug', False)

        self.data_port = 12222

        self.data_socket = socket.socket()
        self.data_socket.bind(('', self.data_port))
        self.data_socket.listen(self.max_connections)

    def send_data(self, message):
        """
        Send data to all hosts that have connected.
        """
        c, addr = self.data_socket.accept()

        if self.debug:
            print("Got connection from ", addr)

        c.send(encode_data(message))
        c.close()
