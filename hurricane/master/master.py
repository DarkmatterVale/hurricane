import socket
import multiprocessing
import errno
from time import sleep
from datetime import datetime
from hurricane.utils import encode_data
from hurricane.utils import read_data
from hurricane.utils import create_active_socket
from hurricane.utils import create_listen_socket
from hurricane.utils import generate_task_id

class MasterNode:

    def __init__(self, **kwargs):
        self.initialize_port = kwargs.get('initialize_port', 12222)
        self.current_port = kwargs.get('starting_task_port', self.initialize_port + 2)
        self.task_completion_port = kwargs.get('task_completion_port', self.initialize_port + 1)
        self.debug = kwargs.get('debug', False)
        self.max_disconnect_errors = kwargs.get('max_disconnect_errors', 3)

        self.nodes = {}
        self.max_connections = 20
        self.scanner_input, self.scanner_output= multiprocessing.Pipe()

    def initialize(self):
        """
        This method runs in the background and attempts to identify slaves to use.
        """
        if self.debug:
            print("[*] Initializing the master node...")
            print("[*] Starting up scanning process...")
        self.scanning_process = multiprocessing.Process(target=self.identify_slaves)
        self.scanning_process.daemon = True
        self.scanning_process.start()

        if self.debug:
            print("[*] Starting up task completion monitoring process...")
        self.task_completion_monitoring_process = multiprocessing.Process(target=self.complete_tasks)
        self.task_completion_monitoring_process.daemon = True
        self.task_completion_monitoring_process.start()

    def identify_slaves(self):
        """
        Identify slave nodes.
        """
        initialize_socket = create_listen_socket(self.initialize_port, self.max_connections)

        while True:
            c, addr = initialize_socket.accept()
            self.update_available_ports()
            data = {
                "is_connected" : True,
                "task_port" : self.current_port,
                "task_completion_port" : self.task_completion_port
            }
            self.scanner_output.send({"address" : addr, "task_port" : self.current_port})

            c.send(encode_data(data))
            c.close()

    def complete_tasks(self):
        """
        Capture the data received data when a task is completed.
        """
        data_socket = create_listen_socket(self.task_completion_port, self.max_connections)

        while True:
            c, addr = data_socket.accept()
            data = read_data(c)
            c.close()

            if self.debug:
                print("[*] Completed a task and received the following data: ")

            print(data)

    def update_available_ports(self):
        """
        Update to get next available port to communicate on.
        """
        self.current_port += 1

    def update_nodes(self):
        """
        Check the initialization thread pipe to see if any new clients have been
        discovered.
        """
        while self.scanner_input.poll():
            new_node = []
            data = self.scanner_input.recv()
            new_node.extend(data["address"])

            new_node_compiled = new_node[0] + ":" + str(data["task_port"])
            if new_node_compiled not in self.nodes:
                self.nodes[new_node_compiled] = {"num_disconnects" : 0}

                if self.debug:
                    print("[*] Identified new node at " + new_node_compiled)

    def get_host(self, id):
        """
        Read the host from the id.
        """
        return id.split(":")[0]

    def get_port(self, id):
        """
        Read the port from the id.
        """
        return id.split(":")[1]

    def manage_node_status(self):
        """
        If a host has disconnected, remove them from the known hosts list.
        """
        self.update_nodes()

        should_update = False
        for node, node_info in self.nodes.items():
            if node_info["num_disconnects"] >= self.max_disconnect_errors:
                if self.debug:
                    print("[*] Connection with " + node + " has timed out...disconnecting from slave node")
                new_nodes = {}
                for inner_node, inner_node_info in self.nodes.items():
                    if inner_node != node:
                        new_nodes[inner_node] = inner_node_info

                self.nodes = new_nodes

    def wait_for_connection(self):
        """
        Block the current thread until there is a slave node to send tasks to
        """
        if self.debug:
            print("[*] Waiting for a connection...")

        while self.nodes == {}:
            self.manage_node_status()
            sleep(0.1)

    def send_task(self, data):
        """
        Distribute a task to a slave node.
        """
        self.manage_node_status()

        if self.nodes == {}:
            return

        task_id = generate_task_id()
        final_data = {
            "start_time" : datetime.now(),
            "task_id" : task_id,
            "return_port" : self.task_completion_port,
            "data" : data
        }

        did_error_occur = False
        for node, node_info in self.nodes.items():
            try:
                task_socket = create_active_socket(self.get_host(node), int(self.get_port(node)))

                if self.debug:
                    print("[*] Sending task " + str(task_id) + " to " + node)

                task_socket.send(encode_data(final_data))
                task_socket.close()

                self.nodes[node]["num_disconnects"] = 0
            except socket.error as err:
                did_error_occur = True

                if err.errno == errno.ECONNREFUSED or err.args[0] == "timed out":
                    if self.debug:
                        print("[*] ERROR : Connection refused when attempting to send a task to " + node + ", try number " + str(self.nodes[node]["num_disconnects"] + 1))

                    self.nodes[node]["num_disconnects"] += 1
                elif err.errno == errno.EPIPE:
                    if self.debug:
                        print("[*] ERROR : Client connection from " + node + " disconnected early")
                else:
                    if self.debug:
                        print("[*] ERROR : Unknown error \"" + err.args[0] + "\" thrown when attempting to send a task to " + node)

        if not did_error_occur:
            return task_id

        return None
