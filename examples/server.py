from hurricane import MasterNode

server = MasterNode()

while True:
    print("Waiting for a connection...")
    server.send_data({"name" : "server"})
