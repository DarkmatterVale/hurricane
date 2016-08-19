from hurricane import SlaveNode

if __name__ == '__main__':
    client = SlaveNode(debug=True, master_node='127.0.0.1')

    client.initialize()
    client.wait_for_initialize()

    while True:
        task_data = client.wait_for_task()
        print("[*] Task name: " + str(task_data["name"]))
        client.finish_task(generated_data={"completion_status" : "success"})
