from hurricane import MasterNode
from time import sleep

server = MasterNode(debug=True)
server.initialize()

server.wait_for_connection()
server.send_task({"name" : "server"})
sleep(5)
server.send_task({"name" : "server2"})
