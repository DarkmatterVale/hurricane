import socket
import errno
import multiprocessing
from time import sleep
from hurricane.utils import *

class SlaveNode:

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.initialize_port = kwargs.get('initialize_port', 12222)
        self.master_node_address = kwargs.get('master_node', '')
        self.max_disconnects = kwargs.get('max_disconnect_errors', 3)

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
                    self.task_port = data.get_task_port()
                    self.task_completion_port = data.get_task_completion_port()

            self.scanning_process.terminate()

        if self.master_node_address != '':
            return True

        return False

    def wait_for_task(self, timeout=5):
        """
        Wait for a task to be sent on the data port.
        """
        self.wait_for_initialize()

        num_disconnects = 0
        while True:
            try:
                self.task_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.task_socket.settimeout(timeout)
                self.task_socket.bind(('', self.task_port))
                self.task_socket.listen(1)

                if self.debug:
                    print("[*] Waiting to receive a new task on port " + str(self.task_port) + "...")

                c, addr = self.task_socket.accept()
                self.current_task = read_data(c)

                if self.debug:
                    print("[*] Received a new task " + str(self.current_task.get_task_id()) + " from " + str(addr))

                return self.current_task.get_data()
            except socket.error as err:
                if num_disconnects > self.max_disconnects:
                    if self.debug:
                        print("[*] Attempting to reconnect to master node...")
                    self.scanning_process = multiprocessing.Process(target=self.complete_network_scan)
                    self.scanning_process.start()
                    self.wait_for_initialize()

                    num_disconnects = 0
                else:
                    if err.errno == errno.ECONNREFUSED or err.args[0] == "timed out":
                        if self.debug:
                            print("[*] ERROR : Connection refused when attempting to connect to master node, try number " + str(num_disconnects + 1))

                        num_disconnects += 1

            sleep(0.1)

        if time > timeout:
            if self.debug:
                print("[*] Attempting to reconnect to the master node...")
            self.scanning_process = multiprocessing.Process(target=self.complete_network_scan)
            self.scanning_process.start()

            self.wait_for_initialize()

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

                    if self.debug:
                        print("[*] Successfully connected to " + str(address))

                    # Send the address of the master node to the parent thread
                    self.scanner_output.send({"address" : address})

                    if self.debug:
                        print("[*] Updated data port to port number " + str(data.get_task_port()))

                    # Update the data port
                    self.scanner_output.send(data)

                    return
                except:
                    continue

            sleep(1)
