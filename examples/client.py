from hurricane import SlaveNode

if __name__ == '__main__':
    client = SlaveNode(debug=True, master_node='127.0.0.1')

    client.initialize()
    client.wait_for_initialize()

    while True:
        task = client.wait_for_task()
        print("[*] Task name: " + str(task["name"]))
