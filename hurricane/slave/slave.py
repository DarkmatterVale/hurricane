import socket
import errno
import multiprocessing
from time import sleep
from hurricane.utils import scan_network
from hurricane.utils import read_data

class SlaveNode:

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.task_port = kwargs.get('task_port', 12222)
        self.initialize_port = kwargs.get('initialize_port', 12223)
        self.master_node_address = kwargs.get('master_node', '')
        self.scanning_process = None
        self.scanner_input, self.scanner_output= multiprocessing.Pipe()

    def initialize(self):
        """
        Initialize the slave node; scan the network and identify the master node.
        """
        if self.debug:
            print("[*] Initializing the node...")

        self.scanning_process = multiprocessing.Process(target=self.complete_network_scan)
        self.scanning_process.start()

    def wait_for_initialize(self):
        """
        Pause the current thread until the initialize thread has finished running.
        """
        if self.scanning_process != None:
            self.scanning_process.join()

        self.master_node_init_status()

    def master_node_init_status(self):
        """
        Determine whether the master node has been identified.

        @returns True if the master node has been identified, False if not
        """
        if self.scanner_input.poll():
            while self.scanner_input.poll():
                data = self.scanner_input.recv()
                try:
                    self.master_node_address = data["address"]
                except:
                    self.task_port = data["task_port"]

            self.scanning_process.terminate()

        if self.master_node_address != '':
            return True

        return False

    def wait_for_task(self):
        """
        Wait for a task to be sent on the data port.
        """
        self.task_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.task_socket.bind(('', self.task_port))
        self.task_socket.listen(1)

        if self.debug:
            print("[*] Waiting to receive a new task on port " + str(self.task_port) + "...")

        c, addr = self.task_socket.accept()

        if self.debug:
            print("[*] Received a new task from " + str(addr))

        data = read_data(c)

        return data["data"]

    def complete_network_scan(self):
        """
        Scan the local network & determine all of the active IP addresses.
        """
        # Scan the network (if necessary)
        if self.master_node_address == '':
            if self.debug:
                print("[*] Scanning the network to identify active hosts...")
            ip_addresses = ['127.0.0.1']
            ip_addresses.extend(scan_network())
        else:
            ip_addresses = [self.master_node_address]

        # Identify the master node
        while True:
            for address in ip_addresses:
                initialize_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                if self.debug:
                    print("[*] Attempting to connect to " + str(address) + "...")

                try:
                    initialize_socket.connect((address, self.initialize_port))
                    data = read_data(initialize_socket)
                    initialize_socket.close()

                    if data["is_connected"] == True:
                        if self.debug:
                            print("[*] Successfully connected to " + str(address))

                        # Send the address of the master node to the upper thread
                        self.scanner_output.send({"address" : address})

                        if self.debug:
                            print("[*] Updated data port to port number " + str(data["task_port"]))

                        # Update the data port
                        self.scanner_output.send({"task_port" : data["task_port"]})

                        return
                except:
                    continue

            sleep(1)
