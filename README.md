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

The following must be installed externally to use this program:

```
brew install libdnet
```

Python 3.5.x or higher must also be installed before attempting to use this library (I WILL NOT support any prior version of Python because they will eventually stop being supported).

## Examples

Examples are located at https://github.com/DarkmatterVale/hurricane/tree/master/examples

## History

See release notes for changes https://github.com/DarkmatterVale/hurricane/releases
