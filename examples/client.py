from hurricane import SlaveNode

if __name__ == '__main__':
    client = SlaveNode(debug=True)

    client.initialize()
    client.wait_for_initialize()

    while True:
        task = client.wait_for_task()
        print("[*] Task name: " + str(task["name"]))
