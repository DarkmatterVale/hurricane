from __future__ import absolute_import, division, print_function

import sys
if "win" in sys.platform:
    from scapy.all import *

import scapy.config
import scapy.layers.l2
import scapy.route
import socket
import math

def simple_scan_network():
    """
    Do a simple network scan, which only works if your network configuration
    is 192.168.1.x
    """
    base_ip = "192.168.1."
    addresses = ['127.0.0.1']

    for index in range(1, 255):
        addresses.extend([base_ip + str(index)])

    return addresses

def scan_network():
    """
    Scan the LAN and identify active IP addressses.

    @returns the list of active IP addresses
    """
    ip_addresses = ['127.0.0.1']

    for network, netmask, _, interface, address in scapy.config.conf.route.routes:
        # skip loopback network and default gw
        if network == 0 or interface == 'lo' or address == '0.0.0.0':
            continue

        if netmask <= 0 or netmask == 0xFFFFFFFF:
            continue

        net = to_CIDR_notation(network, netmask)

        if interface != scapy.config.conf.iface:
            continue

        if net:
            ip_addresses.extend(scan_and_print_neighbors(net, interface))

    return ip_addresses

def long2net(arg):
    return 32 - int(round(math.log(0xFFFFFFFF - arg, 2)))

def to_CIDR_notation(bytes_network, bytes_netmask):
    network = scapy.utils.ltoa(bytes_network)
    netmask = long2net(bytes_netmask)
    net = "%s/%s" % (network, netmask)
    if netmask < 16:
        return None

    return net

def scan_and_print_neighbors(net, interface, timeout=50):
    addresses = []

    try:
        ans, unans = scapy.layers.l2.arping(net, iface=interface, timeout=timeout, verbose=False)
        for s, r in ans.res:
            line = r.sprintf("%ARP.psrc%")
            addresses.append(line)
    except socket.error as e:
        pass

    return addresses
