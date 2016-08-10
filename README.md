# hurricane
A supercomputing library for python

Hurricane is a simple to use peer-to-peer communication protocol built on top of Python 3.5. Hurricane allows for the distribution of tasks from a master node to slave nodes through a simple-to-use API.

## Features

- Slave node auto-discovery : Slave nodes on the local network are auto-discovered
- Automatic task distribution : The library determines which node to send a task to; no user input required!
- Simple API : Using the library is very simple but still flexible
- Multiple hurricane clusters can be run on a single network : As long as they are running on different initialization ports, multiple hurricane clusters will be able to be run within a single network
- Multiple nodes per device : As many nodes as you would like can be run on a single device, making it very easy to quickly deploy large numbers of nodes

## Requirements

For the hurricane cluster to work properly, a few conditions must be met:

- Standard LAN configuration (i.e. 192.168.1.x)
- All nodes are the same. Due to current limitations within the system, task distribution requires all nodes to be run with the same code

## How it works

Python's native socket library is used to create streams to multiple computers and send tasks between. When creating a hurricane cluster, simply start up a master node and a few slave nodes and start sending tasks! The library will do all the heavy lifting for you (managing the data flow, which node to send the data to, etc.).

## Installation

Clone this github repository, cd into the ```hurricane``` directory and run ```sudo -H pip3 install .```. Using ```sudo -H``` and ```pip3``` are requirements and must be used to successfully install the library.

## External Dependencies

The following must be installed externally to use this program on:

Mac OS X

```
brew install libdnet
```

Windows

```
winpcap
```

Python 3.5.x or higher must also be installed before attempting to use this library (I WILL NOT support any prior version of Python because they will eventually stop being supported).

## Usage

hurricane is broken into two main classes, ```hurricane.MasterNode``` and ```hurricane.SlaveNode```. The following examples demonstrate a simple program to communicate between a master node and multiple slave nodes.

When creating a master node, this is the class that is used. Here is a simple example of a MasterNode being used:

```
from hurricane import MasterNode
from time import sleep

server = MasterNode(debug=True, starting_task_port=12228)
server.initialize()

server.wait_for_connection()
while True:
    server.send_task({"name" : "server"})
    sleep(5)
```

When instantiating a MasterNode object, there are a number of settings which can be configured:

- ```debug``` : This can be set to either ```True``` or ```False```. If it is set to ```True``` debugging is enabled, and thorough logging is displayed to the console. By default, this option is set to ```False```
- ```initialize_port``` : This is the "unique identifier" for a hurricane cluster. The default port is ```12222```, but it can be changed to almost all ports. For example, to set the initialize_port to port number 13456 add the option - ```initialize_port=13456```. It is very important to note that the initialize port must be the same on both the master and slave nodes of a hurricane cluster. If they are not, a slave node will not be able to connect to the master node
- ```starting_task_port``` : By default, this port is set to one above the initialization port. You can manually set it to any port, and all ports above this port will be allowed to be used by the hurricane cluster to communicate with nodes
- ```max_disconnect_errors``` : This is the number of times the server will attempt to connect to a malfunctioning node of the cluster. By default, it is set to ```3```

Here is a simple slave node:

```
from hurricane import SlaveNode

client = SlaveNode(debug=True, master_node='127.0.0.1')

client.initialize()
client.wait_for_initialize()

while True:
    task = client.wait_for_task()
    print("[\*] Task name: " + str(task["name"]))
```

In this example, a slave node is configured to enable debugging as well as manually setting the address for the master node to ```127.0.0.1```. Below are all of the options that can be configured when instantiating a slave node.

- ```debug``` : This can be set to either ```True``` or ```False```. If it is set to ```True``` debugging is enabled, and thorough logging is displayed to the console. This option is defaulted to ```False```
- ```initialize_port``` : This is the port number used during initial communication with the master node of a hurricane cluster. As mentioned in the documentation for the MasterNode class, this must be the same as the master node's initialization_port. By default, this is set to ```12222```
- ```master_node``` : By setting the master node's address, you are changing a number of "behind-the-scenes" settings. First off, setting this parameter dramatically decreases the execution time of initialization of the slave node. When this parameter is not set, the node's auto-discover feature is enabled which requires the program to scan the local network for a master node. This scanning process will continue infinitely until a master node is found (it DOES take a significant portion of CPU power). Once the master node has been identified, the node resumes "normal" execution. It is also important to note that this is NOT a blocking operation, as in it is run in a separate thread to ensure the program maintaining the slave node is not stopped. By default, the master node's address is not set

Please see the documentation for in-depth information in using the hurricane library.

## Examples

Examples are located at https://github.com/DarkmatterVale/hurricane/tree/master/examples

## History

See release notes for changes https://github.com/DarkmatterVale/hurricane/releases
