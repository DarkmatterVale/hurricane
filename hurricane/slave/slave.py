import socket
import pickle
import errno
import struct
import multiprocessing
from .utils import scan_network

class SlaveNode:

    def __init__(self, **kwargs):
        if kwargs.get('debug') == None:
            self.debug = False
        else:
            self.debug = True

        self.data_port = kwargs.get('data_port', 12222)
        self.initialize_port = kwargs.get('initialize_port', 12223)
        self.master_node_address = kwargs.get('master_node', '')
        self.socket = socket.socket()
        self.scanning_process = None
        self.scanner_input, self.scanner_output= multiprocessing.Pipe()

    def initialize(self):
        """
        Initialize the slave node; scan the network and identify the master node.
        """
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
        if self.scanning_process != None:
            if self.scanner_input.poll():
                self.master_node_address = self.scanner_input.recv()
                self.scanning_process = None

        if self.master_node_address != '':
            return True

        print("RETURNING FALSE FOR master_node_init_status")

        return False

    def create_socket(self, host, port):
        """
        Initialize the socket & connect it to the host on the port port.
        """
        if self.socket == None:
            self.socket = socket.socket()

        self.port = port
        self.master_node_address = host

    def receive_data(self):
        """
        Receive data from the socket.
        """
        if not self.master_node_init_status():
            return None

        try:
            self.socket = socket.socket()
            self.socket.connect((self.master_node_address, self.data_port))

            raw_msglen = self.socket.recv(4)
            msglen = struct.unpack('>I', raw_msglen)[0]

            data = self.socket.recv(msglen)
            data = pickle.loads(data)

            self.socket.close()
        except socket.error as err:
            if err.errno == errno.ECONNREFUSED:
                if self.debug:
                    print("[*] ERROR : Connection refused when attempting to connect to " + self.master_node_address + " on port " + str(self.data_port))
                return None
            else:
                if self.debug:
                    print("[*] ERROR : Unknown error thrown when attempting to connect to " + self.master_node_address + " on port " + str(self.data_port))
                return None

        return data

    def complete_network_scan(self):
        """
        Scan the local network & determine all of the active IP addresses.
        """
        # Scan the network (if necessary)
        if self.master_node_address == '':
            if self.debug:
                print("[*] Scanning the network to identify active hosts...")
            ip_addresses = scan_network()
            ip_addresses.extend(['127.0.0.1'])
        else:
            ip_addresses = [self.master_node_address]

        # Identify the master node
        for address in ip_addresses:
            self.socket = socket.socket()

            if self.debug:
                print("[*] Attempting to connect to " + str(address) + " on port " + str(self.initialize_port) + "...")

            try:
                self.socket.connect((address, self.initialize_port))

                raw_msglen = self.socket.recv(4)
                msglen = struct.unpack('>I', raw_msglen)[0]
                data = self.socket.recv(msglen)
                data = pickle.loads(data)

                self.socket.close()

                if data["message"] == "connected":
                    # Send the address of the master node to the upper thread
                    self.scanner_output.send(address)

                    break
            except:
                continue

        self.scanner_output.send('127.0.0.1')
