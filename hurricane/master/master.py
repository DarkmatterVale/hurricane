import socket
import multiprocessing
import errno
from time import sleep
from hurricane.utils import encode_data

class MasterNode:

    def __init__(self, **kwargs):
        self.initialize_port = kwargs.get('initialize_port', 12223)
        self.data_port = kwargs.get('data_port', 12222)
        self.max_connections = kwargs.get('connections', 20)
        self.debug = kwargs.get('debug', False)

        self.hosts = []
        self.scanner_input, self.scanner_output= multiprocessing.Pipe()

    def initialize(self):
        """
        This method runs in the background and attempts to identify slaves to use.
        """
        if self.debug:
            print("[*] Initializing the master node...")
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

            self.scanner_output.send(addr)

            c.send(encode_data(data))
            c.close()

    def update_hosts(self):
        """
        Check the initialization thread pipe to see if any new clients have been
        discovered.
        """
        while self.scanner_input.poll():
            new_node = []
            new_node.extend(self.scanner_input.recv())
            self.hosts.extend([new_node[0]])

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

    def wait_for_connection(self):
        """
        Block the current thread until there is a slave node to send tasks to
        """
        if self.debug:
            print("[*] Waiting for a connection...")

        while self.hosts == []:
            self.update_hosts()
            sleep(0.1)

    def send_task(self, data):
        """
        Distribute a task to a slave node.
        """
        if self.hosts == []:
            return

        final_data = {
            "data" : data
        }

        try:
            task_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            task_socket.connect((self.hosts[0], self.data_port))
            task_socket.send(encode_data(final_data))
            task_socket.close()
        except socket.error as err:
            if err.errno == errno.ECONNREFUSED:
                if self.debug:
                    print("[*] ERROR : Connection refused when attempting to send a task to " + self.hosts[0])
            else:
                if self.debug:
                    print("[*] ERROR : Unknown error thrown when attempting to send a task to " + self.hosts[0])
