from hurricane import MasterNode

server = MasterNode(debug=True)

print ("[*] Server initialized")

while True:
    print("[*] Waiting for a connection...")
    server.send_data({"name" : "server"})
