from hurricane import SlaveNode

client = SlaveNode()

print("[*] Initializing the node...")
client.initialize()
client.wait_for_initialize()

print("[*] Printing data gathered from the node:")
print(client.receive_data()["name"])
