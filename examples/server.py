from hurricane import MasterNode

server = MasterNode()

print ("[*] Server initialized")

while True:
    print("[*] Waiting for a connection...")
    server.send_data({"name" : "server"})
