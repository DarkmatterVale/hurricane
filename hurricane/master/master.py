import socket
import multiprocessing
import errno
from time import sleep
from hurricane.utils import encode_data
from hurricane.utils import create_active_socket
from hurricane.utils import create_listen_socket

class MasterNode:

    def __init__(self, **kwargs):
        self.initialize_port = kwargs.get('initialize_port', 12222)
        self.task_port = kwargs.get('task_port', 12223)
        self.max_connections = kwargs.get('connections', 20)
        self.debug = kwargs.get('debug', False)
        self.max_disconnect_errors = kwargs.get('max_disconnect_errors', 3)

        self.hosts = []
        self.host_errors = {}
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
        initialize_socket = create_listen_socket(self.initialize_port, self.max_connections)

        data = {
            "is_connected" : True,
            "task_port" : self.task_port
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

    def manage_host_status(self):
        """
        If a host has disconnected, remove them from the known hosts list.
        """
        self.update_hosts()

        index = 0
        while index < len(self.hosts):
            host = self.hosts[index]

            if host not in self.host_errors:
                self.host_errors[host] = 0

            if self.host_errors[host] >= self.max_disconnect_errors:
                if self.debug:
                    print("[*] Connection with " + host + " has timed out...disconnecting from slave node")
                new_hosts = []
                new_host_errors = {}
                for inner_host in self.hosts:
                    if inner_host != host:
                        new_hosts.extend([inner_host])
                        new_host_errors[inner_host] = self.host_errors[inner_host]

                self.host_errors = new_host_errors
                self.hosts = new_hosts
                index -= 1

            index += 1

    def wait_for_connection(self):
        """
        Block the current thread until there is a slave node to send tasks to
        """
        if self.debug:
            print("[*] Waiting for a connection...")

        while self.hosts == []:
            self.manage_host_status()
            sleep(0.1)

    def send_task(self, data):
        """
        Distribute a task to a slave node.
        """
        self.manage_host_status()

        if self.hosts == []:
            return

        final_data = {
            "data" : data
        }

        for host in self.hosts:
            try:
                task_socket = create_active_socket(host, self.task_port)

                if self.debug:
                    print("[*] Sending a new task to " + str(host))

                task_socket.send(encode_data(final_data))
                task_socket.close()
            except socket.error as err:
                if err.errno == errno.ECONNREFUSED:
                    if self.debug:
                        print("[*] ERROR : Connection refused when attempting to send a task to " + host + ", try number " + str(self.host_errors[host] + 1))

                    self.host_errors[host] += 1
                elif err.errno == errno.EPIPE:
                    if self.debug:
                        print("[*] ERROR : Client connection from " + host + " disconnected early")
                else:
                    if self.debug:
                        print("[*] ERROR : Unknown error thrown when attempting to send a task to " + host)
