import socket
import pickle
import struct

class MasterNode:

    def __init__(self, **kwargs):
        self.data_port = kwargs.get('data_port', 12222)
        self.hosts = kwargs.get('hosts', '')
        self.connections = kwargs.get('connections', 20)

        self.listen_socket = socket.socket()
        self.listen_socket.bind(('', self.data_port))
        self.listen_socket.listen(self.connections)

    def send_data(self, message):
        """
        Send data to all hosts that have connected.
        """
        c, addr = self.listen_socket.accept()
        print("Got connection from ", addr)
        msg = pickle.dumps(message)
        msg = struct.pack('>I', len(msg)) + msg
        c.send(msg)
        c.close()
