from hurricane import MasterNode
from time import sleep

if __name__ == '__main__':
    server = MasterNode(debug=True, starting_task_port=12228)
    server.initialize()

    server.wait_for_connection()
    while True:
        task_id = server.send_task({"name" : "server"})
        generated_data = server.wait_for_task_to_be_completed(task_id)
        print(generated_data)
        sleep(3)
        task_id_2 = server.send_task({"name" : "server2"})
        generated_data_2 = server.wait_for_task_to_be_completed(task_id_2)
        print(generated_data_2)
        sleep(3)
