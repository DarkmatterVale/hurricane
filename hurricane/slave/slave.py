import socket
import errno
import multiprocessing
from time import sleep
from hurricane.utils import scan_network
from hurricane.utils import simple_scan_network
from hurricane.utils import read_data
from hurricane.utils import create_active_socket
from hurricane.utils import create_listen_socket
from hurricane.utils import encode_data
from hurricane.utils import Task

class SlaveNode:

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.initialize_port = kwargs.get('initialize_port', 12222)
        self.master_node_address = kwargs.get('master_node', '')

        self.task_port = self.initialize_port + 1
        self.task_completion_port = self.task_port + 1
        self.scanning_process = None
        self.current_task = None
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
                    self.task_completion_port = data["task_completion_port"]

            self.scanning_process.terminate()

        if self.master_node_address != '':
            return True

        return False

    def wait_for_task(self):
        """
        Wait for a task to be sent on the data port.
        """

        while True:
            try:
                self.task_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.task_socket.bind(('', self.task_port))
                self.task_socket.listen(1)

                if self.debug:
                    print("[*] Waiting to receive a new task on port " + str(self.task_port) + "...")

                c, addr = self.task_socket.accept()

                if self.debug:
                    print("[*] Received a new task from " + str(addr))

                self.current_task = read_data(c)
                return self.current_task.get_data()
            except:
                sleep(0.5)

    def finish_task(self, **kwargs):
        """
        Send the task completion data back to the master node.
        """
        if self.current_task != None:
            if self.debug:
                print("[*] Completed task " + str(self.current_task.get_task_id()))

            self.current_task.set_generated_data(kwargs.get('generated_data', None))

            completion_socket = create_active_socket(self.master_node_address, self.task_completion_port)
            completion_socket.send(encode_data(self.current_task))
        else:
            if self.debug:
                print("[*] ERROR : No task to complete")

    def complete_network_scan(self):
        """
        Scan the local network & determine all of the active IP addresses.
        """
        while True:
            # Scan the network (if necessary)
            if self.master_node_address == '':
                if self.debug:
                    print("[*] Scanning the network to identify active hosts...")
                ip_addresses = simple_scan_network()
            else:
                ip_addresses = [self.master_node_address]

            # Identify the master node
            for address in ip_addresses:
                if self.debug:
                    print("[*] Attempting to connect to " + str(address) + "...")

                try:
                    initialize_socket = create_active_socket(address, self.initialize_port)
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
                        self.scanner_output.send({"task_port" : data["task_port"], "task_completion_port" : data["task_completion_port"]})

                        return
                except:
                    continue

            sleep(1)
