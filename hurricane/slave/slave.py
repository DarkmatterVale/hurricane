import socket
import pickle
import struct

class SlaveNode:

    def __init__(self, **kwargs):
        self.port = kwargs.get('port', 12222)
        self.master_node_address = kwargs.get('master_node', '127.0.0.1')

        if self.socket == None:
            self.socket = socket.socket()

    def create_socket(self, host, port):
        """
        Initialize the socket & connect it to the host on the port port.
        """
        if self.socket == None:
            self.socket = socket.socket()

        self.port = port
        self.master_node_address = host

    def receive_data(self):
        """
        Receive data from the socket
        """
        try:
            self.socket.connect((self.master_node_address, self.port))

            raw_msglen = self.socket.recv(4)
            msglen = struct.unpack('>I', raw_msglen)[0]

            data = self.socket.recv(msglen)
            data = pickle.loads(data)

            self.socket.close()

            return data
        except:
            return "__ERROR__"
