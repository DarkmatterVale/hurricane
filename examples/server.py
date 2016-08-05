from hurricane import MasterNode

server = MasterNode()

while True:
    print("Sending data...")
    server.send_data({"name" : "server"})
