from hurricane import SlaveNode

client = SlaveNode(debug=True, master_node='127.0.0.1')

client.initialize()
client.wait_for_initialize()

while True:
    client.wait_for_task()
