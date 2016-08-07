from hurricane import MasterNode
from time import sleep

server = MasterNode(debug=True, task_port=12224)
server.initialize()

server.wait_for_connection()
while True:
    server.send_task({"name" : "server"})
    sleep(5)
    server.send_task({"name" : "server2"})
    sleep(5)
