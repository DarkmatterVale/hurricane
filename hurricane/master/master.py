import socket
import multiprocessing
import errno
import sys
from queue import Empty
from time import sleep
from datetime import datetime
from hurricane.utils import *

class MasterNode:

    def __init__(self, **kwargs):
        self.initialize_port = kwargs.get('initialize_port', 12222)
        self.debug = kwargs.get('debug', False)
        self.max_disconnect_errors = kwargs.get('max_disconnect_errors', 3)

        self.nodes = {}
        self.max_connections = 20
        self.task_port = self.initialize_port + 1
        self.task_completion_port = self.initialize_port + 2
        self.scanner_input, self.scanner_output = multiprocessing.Pipe()
        self.completed_tasks_queue = multiprocessing.Queue()
        self.completed_tasks = []
        self.send_tasks_queue = multiprocessing.Queue()

    def initialize(self):
        """
        This method runs in the background and attempts to identify slaves to use.
        """
        if self.debug:
            print("[*] Initializing the master node")
            print("[*] Starting scanning process...")
        self.scanning_process = multiprocessing.Process(target=self.identify_slaves)
        self.scanning_process.start()

        if self.debug:
            print("[*] Starting node management process...")
        self.node_management_process = multiprocessing.Process(target=self.node_manager)
        self.node_management_process.daemon = True
        self.node_management_process.start()

    def node_manager(self):
        """
        This is the main node manager process. All of the task distribution as well
        as node "maintenance" is completed within this thread.
        """
        while True:
            sleep(0.1)

    def identify_slaves(self):
        """
        Identify slave nodes.
        """
        initialize_socket = create_listen_socket(self.initialize_port, self.max_connections)

        while True:
            connection, addr = initialize_socket.accept()
            self.update_available_ports()

            self.scanner_output.send({"address" : addr, "task_port" : self.task_port, "task_completion_port" : self.task_completion_port})

            task_completion_monitoring_process = multiprocessing.Process(target=self.complete_tasks, args=(self.task_completion_port,))
            task_completion_monitoring_process.daemon = True
            task_completion_monitoring_process.start()
            sleep(0.01)

            connection.send(encode_data(InitializeMessage(task_port=self.task_port, task_completion_port=self.task_completion_port)))
            connection.close()

    def complete_tasks(self, port):
        """
        Capture the data received data when a task is completed.
        """
        data_socket = create_listen_socket(port, self.max_connections)

        while True:
            c, addr = data_socket.accept()
            completed_task = read_data(c)
            c.close()

            if self.debug:
                print("[*] Received task completion for task " + str(completed_task.get_task_id()))

            self.completed_tasks_queue.put(completed_task)

    def update_completed_tasks_list(self):
        """
        Move all tasks in queue to completed tasks list.
        """
        while True:
            try:
                self.completed_tasks.append(self.completed_tasks_queue.get(block=False))
            except Empty:
                break

    def is_task_completed(self, task_id):
        """
        Returns "True, generated_data" if the task has been completed,
        "False, None" if it has not.
        """
        self.update_completed_tasks_list()

        for task in self.completed_tasks:
            if task_id == task.get_task_id():
                return True, task

        return False, None

    def wait_for_any_task_completion(self, timeout=-1):
        """
        Wait for any task to be completed
        """
        if timeout > 0:
            time = 0
            while time < timeout:
                if self.completed_tasks == []:
                    sleep(0.1)
                    time += 0.1
                else:
                    return self.completed_tasks[0]

            return None

        while True:
            if self.completed_tasks == []:
                sleep(0.1)
            else:
                return self.completed_tasks[0].get_generated_data()

    def wait_for_task_completion(self, task_id, timeout=-1):
        """
        Wait for the task with task_id to be completed.
        """
        if self.nodes == {}:
            if self.debug:
                print("[*] ERROR : No nodes are connected and no tasks can be completed")

            return None

        if self.debug:
            print("[*] Waiting for task " + str(task_id) + " to be completed")

        if timeout > 0:
            time = 0
            while time < timeout:
                completed, data = self.is_task_completed(task_id)
                if completed:
                    return data
                else:
                    sleep(0.1)
                    time += 0.1
        else:
            while True:
                completed, data = self.is_task_completed(task_id)
                if completed:
                    return data
                else:
                    sleep(0.1)

        return None

    def update_available_ports(self):
        """
        Update to get next available port to communicate on.
        """
        self.task_port += 2
        self.task_completion_port += 2

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
        while self.scanner_input.poll():
            new_node = []
            data = self.scanner_input.recv()
            new_node.extend(data["address"])

            new_node_compiled = new_node[0] + ":" + str(data["task_port"])
            if new_node_compiled not in self.nodes:
                self.nodes[new_node_compiled] = {"num_disconnects" : 0}

                if self.debug:
                    print("[*] Identified new node at " + new_node_compiled)

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

    def wait_for_connection(self, timeout=-1):
        """
        Block the current thread until there is a slave node to send tasks to
        """
        if self.debug:
            print("[*] Waiting for a connection...")

        if timeout > 0:
            time = 0
            while self.nodes == {} and time < timeout:
                self.manage_node_status()

                sleep(0.1)
                time += 0.1
        else:
            while self.nodes == {}:
                self.manage_node_status()

                sleep(0.1)

    def send_task(self, data):
        """
        Distribute a task to a slave node.
        """
        self.manage_node_status()
        if self.nodes == {}:
            if self.debug:
                print("[*] ERROR : No nodes are connected to send a task to")

            return

        new_task = Task(task_id=generate_task_id(), return_port=self.task_completion_port, data=data)
        did_error_occur = False
        for node, node_info in self.nodes.items():
            try:
                task_socket = create_active_socket(self.get_host(node), int(self.get_port(node)))

                if self.debug:
                    print("[*] Sending task " + str(new_task.get_task_id()) + " to " + node)

                task_socket.send(encode_data(new_task))
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
            return new_task.get_task_id()

        return None
