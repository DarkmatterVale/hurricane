from hurricane import SlaveNode

client = SlaveNode(debug=True)#, master_node='127.0.0.1')

print("[*] Initializing the node...")
client.initialize()
client.wait_for_initialize()

print("[*] Printing data gathered from the node:")
data = client.receive_data()
if data != None:
    print(data["name"])
else:
    print("Can't get data...please retry")
