from hurricane import MasterNode
from time import sleep

if __name__ == '__main__':
    server = MasterNode(debug=True, starting_task_port=12228)
    server.initialize()

    server.wait_for_connection()
    while True:
        task_id = server.send_task({"name" : "server"})
        server.wait_for_task_to_be_completed(task_id)
        sleep(3)
        task_id_2 = server.send_task({"name" : "server2"})
        server.wait_for_task_to_be_completed(task_id_2)
        sleep(3)
