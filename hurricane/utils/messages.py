import pickle
import struct

def read_data(connection):
    """
    Read a data from a socket.

    @returns the data received from the socket
    """
    raw_msglen = connection.recv(4)
    msglen = struct.unpack('>I', raw_msglen)[0]

    data = connection.recv(msglen)
    data = pickle.loads(data)

    return data

def encode_data(data):
    """
    Encode data into a transmittable message.

    @returns the encoded data
    """
    msg = pickle.dumps(data)
    msg = struct.pack('>I', len(msg)) + msg

    return msg
