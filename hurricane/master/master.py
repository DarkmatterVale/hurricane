import socket
import multiprocessing
from hurricane.utils import encode_data

class MasterNode:

    def __init__(self, **kwargs):
        self.initialize_port = kwargs.get('initialize_port', 12223)
        self.data_port = kwargs.get('data_port', 12222)
        self.max_connections = kwargs.get('connections', 20)
        self.debug = kwargs.get('debug', False)

        self.hosts = []
        self.scanner_input, self.scanner_output= multiprocessing.Pipe()

        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket.bind(('', self.data_port))
        self.data_socket.listen(self.max_connections)

    def initialize(self):
        """
        This method runs in the background and attempts to identify slaves to use.
        """
        self.scanning_process = multiprocessing.Process(target=self.identify_slaves)
        self.scanning_process.daemon = True
        self.scanning_process.start()

    def identify_slaves(self):
        """
        Identify slave nodes.
        """
        initialize_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        initialize_socket.bind(('', self.initialize_port))
        initialize_socket.listen(self.max_connections)

        data = {
            "is_connected" : True,
            "data_port" : self.data_port
        }

        while True:
            c, addr = initialize_socket.accept()

            if self.debug:
                print("[*] Identified new node at " + str(addr))

            self.scanner_output.send(str(addr))

            c.send(encode_data(data))
            c.close()

    def update_hosts(self):
        """
        Check the initialization thread pipe to see if any new clients have been
        discovered.
        """
        while self.scanner_input.poll():
            self.hosts.extend(self.scanner_input.recv())

    def send_data(self, data):
        """
        Send data to all hosts that have connected.
        """
        self.update_hosts()

        c, addr = self.data_socket.accept()

        if self.debug:
            print("[*] Got connection from ", addr)

        c.send(encode_data(data))
        c.close()
