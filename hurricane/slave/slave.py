import socket
import errno
import multiprocessing
import logging
from time import sleep
from hurricane.utils import *
from hurricane.messages import HeartbeatMessage
from hurricane.messages import TaskMessage
from hurricane.messages import NodeInitializeMessage


class SlaveNode:

    def __init__(self, **kwargs):
        self.debug = kwargs.get('debug', False)
        self.initialize_port = kwargs.get('initialize_port', 12222)
        self.master_node_address = kwargs.get('master_node', '')
        self.max_disconnects = kwargs.get('max_disconnect_errors', 4)

        self.is_initialized = False
        self.task_port = self.initialize_port + 1
        self.task_completion_port = self.task_port + 1
        self.task_socket = None
        self.scanning_process = None
        self.current_task = None
        self.scanner_input, self.scanner_output= multiprocessing.Pipe()

        logging.basicConfig(format="%(asctime)s %(name)s [%(levelname)s] %(message)s", level=kwargs.get("level", logging.INFO))

    def initialize(self):
        """
        Initialize the slave node; scan the network and identify the master node.
        """
        logging.info("Initializing the node")

        self.scanning_process = multiprocessing.Process(target=self.complete_network_scan)
        self.scanning_process.start()

    def wait_for_initialize(self):
        """
        Pause the current thread until the initialize thread has finished running.
        """
        if not self.is_initialized:
            if self.scanning_process != None:
                self.scanning_process.join()

                self.master_node_init_status()

            self.is_initialized = True

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
                    self.task_socket = create_listen_socket_timer(self.task_port, 1, 5)

            self.scanning_process.terminate()

        if self.master_node_address != '':
            logging.info("Sending initialization information to the master node")

            completion_socket = create_active_socket(self.master_node_address, self.task_completion_port)
            completion_socket.send(encode_data(NodeInitializeMessage((None), multiprocessing.cpu_count())))

            return True

        return False

    def wait_for_task(self, timeout=5):
        """
        Wait for a task to be sent on the data port.
        """
        self.wait_for_initialize()

        num_disconnects = 0
        while True:
            if self.task_socket:
                try:
                    logging.info("Waiting to receive a new task on port " + str(self.task_port))

                    c, addr = self.task_socket.accept()
                    current_task = read_data(c)

                    if not isinstance(current_task, HeartbeatMessage):
                        self.current_task = current_task

                        logging.info("Received a new task " + str(self.current_task.get_task_id()) + " from " + str(addr))

                        return self.current_task.get_data()
                    else:
                        logging.info("Heartbeat received from " + str(addr))

                        num_disconnects = 0
                except socket.error as err:
                    if num_disconnects > self.max_disconnects:
                        logging.info("Attempting to reconnect to master node")
                        self.scanning_process = multiprocessing.Process(target=self.complete_network_scan)
                        self.scanning_process.start()
                        self.wait_for_initialize()

                        num_disconnects = 0
                    else:
                        if err.errno == errno.ECONNREFUSED:
                            logging.error("Connection refused when attempting to connect to master node, try number " + str(num_disconnects + 1))

                            num_disconnects += 1
                        elif err.args[0] == "timed out":
                            if num_disconnects >= 1:
                                logging.error("Connection timed out when attempting to connect to master node, try number " + str(num_disconnects + 1))

                            num_disconnects += 1

                if num_disconnects >= self.max_disconnects:
                    logging.info("Attempting to reconnect to the master node")
                    self.scanning_process = multiprocessing.Process(target=self.complete_network_scan)
                    self.scanning_process.start()
                    self.is_initialized = False

                    if self.task_socket:
                        self.task_socket.close()
                    self.wait_for_initialize()
                    num_disconnects = 0

            sleep(0.1)

    def finish_task(self, **kwargs):
        """
        Send the task completion data back to the master node.
        """
        if self.current_task != None:
            logging.info("Completed task " + str(self.current_task.get_task_id()))

            self.current_task.set_generated_data(kwargs.get('generated_data', None))

            completion_socket = create_active_socket(self.master_node_address, self.task_completion_port)
            completion_socket.send(encode_data(TaskMessage(self.current_task)))
        else:
            logging.error("No task to complete")

    def complete_network_scan(self):
        """
        Scan the local network & determine all of the active IP addresses.
        """
        while True:
            # Scan the network (if necessary)
            if self.master_node_address == '':
                logging.info("Scanning the network to identify active hosts")
                ip_addresses = simple_scan_network()
            else:
                ip_addresses = [self.master_node_address]

            # Identify the master node
            for address in ip_addresses:
                logging.info("Attempting to connect to " + str(address))

                try:
                    initialize_socket = create_active_socket(address, self.initialize_port)
                    data = read_data(initialize_socket)
                    initialize_socket.close()

                    logging.info("Successfully connected to " + str(address))

                    # Send the address of the master node to the parent thread
                    self.scanner_output.send({"address" : address})

                    logging.info("Updated data port to port number " + str(data.get_task_port()))

                    # Update the data port
                    self.scanner_output.send(data)

                    return
                except:
                    continue

            sleep(1)
