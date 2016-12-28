import multiprocessing
from hurricane import SlaveNode

def run_node():
    client = SlaveNode(debug=True, master_node='127.0.0.1')

    client.initialize()
    client.wait_for_initialize()

    while True:
        task_data = client.wait_for_task()
        print("[*] Task name: " + str(task_data["name"]))
        client.finish_task(generated_data={"completion_status" : "success"})


if __name__ == '__main__':
    for node_num in range(multiprocessing.cpu_count()):
        print("[*] Starting another node...")
        node_process = multiprocessing.Process(target=run_node)
        node_process.start()
