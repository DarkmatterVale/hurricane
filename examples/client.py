from hurricane import SlaveNode

client = SlaveNode()

print(client.receive_data()["name"])
