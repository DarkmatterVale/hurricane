import socket

def create_active_socket(host, port):
    """
    Connect to a host on a specific port.

    @returns the new active socket
    """
    active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    active_socket.settimeout(5)
    active_socket.connect((host, port))

    return active_socket

def create_listen_socket(port, max_connections):
    """
    Create a socket to listen on a port with max_connections.
    """
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(('', port))
    listen_socket.listen(max_connections)
    listen_socket.settimeout(10)

    return listen_socket
