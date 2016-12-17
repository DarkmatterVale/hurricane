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

        self.max_connections = 20
        self.task_port = self.initialize_port + 1
        self.task_completion_port = self.initialize_port + 2
        self.scanner_input, self.scanner_output = multiprocessing.Pipe()
        self.has_connection_input, self.has_connection_output = multiprocessing.Pipe()
        self.completed_tasks_input, self.completed_tasks_output = multiprocessing.Pipe()
        self.has_connection_tf = False
        self.completed_tasks_queue = multiprocessing.Queue()
        self.completed_tasks = []
        self.send_tasks_queue = multiprocessing.Queue()

        self.exit_signal = multiprocessing.Event()

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
            print("[*] Starting task distribution process...")
        self.node_management_process = multiprocessing.Process(target=self.node_manager)
        self.node_management_process.daemon = True
        self.node_management_process.start()

    def stop(self):
        """
        Stop the server and kill all child processes
        """
        self.exit_signal.set()

    def node_manager(self):
        """
        This process manages task distribution within the node network.
        """
        nodes = {}
        tasks = []

        while not self.exit_signal.is_set():
            nodes = self.manage_node_status(nodes)

            while self.completed_tasks_input.poll():
                task_id = self.completed_tasks_input.recv()

                for node in nodes:
                    if nodes[node]["task"]:
                        if nodes[node]["task"].get_task_id() == task_id:
                            nodes[node]["task"] = None

            try:
                new_task = self.send_tasks_queue.get(block=False)
                tasks.append(new_task)
            except:
                pass

            for task_idx in range(0, len(tasks)):
                new_task = tasks[task_idx]

                for node in nodes:
                    if not nodes[node]["task"]:
                        did_error_occur = False

                        try:
                            task_socket = create_active_socket(self.get_host(node), int(self.get_port(node)))

                            if self.debug:
                                print("[*] Sending task " + str(new_task.get_task_id()) + " to " + node)

                            task_socket.send(encode_data(new_task))
                            task_socket.close()

                            nodes[node]["num_disconnects"] = 0
                        except socket.error as err:
                            did_error_occur = True

                            if err.errno == errno.ECONNREFUSED or err.args[0] == "timed out":
                                if self.debug:
                                    print("[*] ERROR : Connection refused when attempting to send a task to " + node + ", try number " + str(nodes[node]["num_disconnects"] + 1))

                                nodes[node]["num_disconnects"] += 1
                            elif err.errno == errno.EPIPE:
                                if self.debug:
                                    print("[*] ERROR : Client connection from " + node + " disconnected early")
                            else:
                                if self.debug:
                                    print("[*] ERROR : Unknown error \"" + err.args[0] + "\" thrown when attempting to send a task to " + node)

                        if not did_error_occur:
                            nodes[node]["task"] = new_task

                            updated_tasks = tasks[:task_idx]
                            updated_tasks.extend(tasks[task_idx + 1:])
                            tasks = updated_tasks

                            break
                    else:
                        pass

            sleep(0.1)

    def identify_slaves(self):
        """
        Identify slave nodes.
        """
        initialize_socket = create_listen_socket(self.initialize_port, self.max_connections)

        while not self.exit_signal.is_set():
            try:
                connection, addr = initialize_socket.accept()
                self.update_available_ports()

                self.scanner_output.send({"address" : addr, "task_port" : self.task_port, "task_completion_port" : self.task_completion_port})

                task_completion_monitoring_process = multiprocessing.Process(target=self.complete_tasks, args=(self.task_completion_port,))
                task_completion_monitoring_process.daemon = True
                task_completion_monitoring_process.start()
                sleep(0.01)

                connection.send(encode_data(InitializeMessage(task_port=self.task_port, task_completion_port=self.task_completion_port)))
                connection.close()
            except socket.error as err:
                if err.args[0] == "timed out":
                    pass

    def complete_tasks(self, port):
        """
        Capture the data received data when a task is completed.
        """
        data_socket = create_listen_socket(port, self.max_connections)

        while not self.exit_signal.is_set():
            c, addr = data_socket.accept()
            completed_task = read_data(c)
            c.close()

            if self.debug:
                print("[*] Received task completion for task " + str(completed_task.get_task_id()))

            self.completed_tasks_queue.put(completed_task)

    def is_task_completed(self, task_id):
        """
        Returns "True, generated_data" if the task has been completed,
        "False, None" if it has not.
        """
        self.update_completed_tasks()

        for task_idx in range(0, len(self.completed_tasks)):
            task = self.completed_tasks[task_idx]

            if task_id == task.get_task_id():
                updated_completed_tasks = self.completed_tasks[:task_idx]
                updated_completed_tasks.extend(self.completed_tasks[task_idx + 1:])
                self.completed_tasks = updated_completed_tasks

                return True, task

        return False, None

    def update_completed_tasks(self):
        """
        Update the completed tasks list from the completed tasks queue.
        """
        while True:
            try:
                self.completed_tasks.append(self.completed_tasks_queue.get(block=False))
            except Empty:
                break

    def wait_for_any_task_completion(self, timeout=-1):
        """
        Wait for any task to be completed
        """
        if timeout > 0:
            time = 0
            while time < timeout and not self.exit_signal.is_set():
                if self.completed_tasks == []:
                    self.update_completed_tasks()

                    sleep(0.1)
                    time += 0.1
                else:
                    self.completed_tasks_output.send(self.completed_tasks[0].get_task_id())
                    return self.completed_tasks[0]

            return None

        while not self.exit_signal.is_set():
            if self.completed_tasks == []:
                self.update_completed_tasks()

                sleep(0.1)
            else:
                return self.completed_tasks[0]

    def wait_for_task_completion(self, task_id, timeout=-1):
        """
        Wait for the task with task_id to be completed.
        """
        if self.has_connection() == False:
            if self.debug:
                print("[*] ERROR : No nodes are connected...please connect a node then send it a task")

            return None

        if self.debug:
            print("[*] Waiting for task " + str(task_id) + " to be completed")

        if timeout > 0:
            time = 0
            while time < timeout and not self.exit_signal.is_set():
                completed, data = self.is_task_completed(task_id)
                if completed:
                    self.completed_tasks_output.send(task_id)
                    return data
                else:
                    sleep(0.1)
                    time += 0.1
        else:
            while not self.exit_signal.is_set():
                completed, data = self.is_task_completed(task_id)
                if completed:
                    self.completed_tasks_output.send(task_id)
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

    def has_connection(self):
        """
        Returns whether this MasterNode has any slave nodes connected
        """
        while self.has_connection_input.poll():
            self.has_connection_tf = self.has_connection_input.recv()

        return self.has_connection_tf

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

    def manage_node_status(self, nodes):
        """
        If a host has disconnected, remove them from the known hosts list.
        """
        while self.scanner_input.poll():
            new_node = []
            data = self.scanner_input.recv()
            new_node.extend(data["address"])

            new_node_compiled = new_node[0] + ":" + str(data["task_port"])
            if new_node_compiled not in nodes:
                nodes[new_node_compiled] = {"num_disconnects" : 0, "task" : None}
                self.has_connection_output.send(True)

                if self.debug:
                    print("[*] Identified new node at " + new_node_compiled)

        should_update = False
        for node, node_info in nodes.items():
            if node_info["num_disconnects"] >= self.max_disconnect_errors:
                if self.debug:
                    print("[*] Connection with " + node + " has timed out...disconnecting from slave node")

                finish_task = Task(task_id=node_info["task"])
                self.completed_tasks_queue.put(finish_task)

                new_nodes = {}
                for inner_node, inner_node_info in nodes.items():
                    if inner_node != node:
                        new_nodes[inner_node] = inner_node_info

                nodes = new_nodes

        if nodes == {}:
            self.has_connection_output.send(False)

        return nodes

    def wait_for_connection(self, timeout=-1):
        """
        Block the current thread until there is a slave node to send tasks to
        """
        if self.debug:
            print("[*] Waiting for a connection...")

        if timeout > 0:
            time = 0
            while self.has_connection() == False and time < timeout:
                sleep(0.1)
                time += 0.1
        else:
            while self.has_connection() == False and not self.exit_signal.is_set():
                sleep(0.1)

    def send_task(self, data):
        """
        Distribute a task to a slave node.
        """
        if self.has_connection == False:
            if self.debug:
                print("[*] WARNING : No nodes are connected/available to send a task to...task will be queued until a node is available/connected")

        new_task = Task(task_id=generate_task_id(), return_port=self.task_completion_port, data=data)

        self.send_tasks_queue.put(new_task)

        return new_task.get_task_id()
