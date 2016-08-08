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
        self.current_port = kwargs.get('starting_task_port', self.initialize_port + 1)
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
        self.scanning_process = multiprocessing.Process(target=self.identify_slaves)
        self.scanning_process.daemon = True
        self.scanning_process.start()

    def identify_slaves(self):
        """
        Identify slave nodes.
        """
        initialize_socket = create_listen_socket(self.initialize_port, self.max_connections)

        while True:
            c, addr = initialize_socket.accept()
            new_node_port = self.get_next_available_port()
            data = {
                "is_connected" : True,
                "task_port" : new_node_port
            }
            self.scanner_output.send({"address" : addr, "task_port" : new_node_port})

            c.send(encode_data(data))
            c.close()

    def get_next_available_port(self):
        """
        Return the next available port to communicate on.
        """
        self.current_port += 1

        return self.current_port

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

        final_data = {
            "data" : data
        }

        for node, node_info in self.nodes.items():
            try:
                task_socket = create_active_socket(self.get_host(node), int(self.get_port(node)))

                if self.debug:
                    print("[*] Sending a new task to " + node)

                task_socket.send(encode_data(final_data))
                task_socket.close()

                self.nodes[node]["num_disconnects"] = 0
            except socket.error as err:
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
