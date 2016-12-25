from hurricane import MasterNode
from time import sleep

if __name__ == '__main__':
    server = MasterNode(debug=True, starting_task_port=12228)
    server.initialize()

    server.wait_for_connection()
    while True:
        if server.has_connection():
            task_id = server.send_task({"name" : "server"})
            generated_data = server.wait_for_task_completion(task_id)
            if generated_data:
                if generated_data.get_generated_data(): print(generated_data.get_generated_data())
            sleep(3)

            task_id_2 = server.send_task({"name" : "server2"})
            generated_data_2 = server.wait_for_task_completion(task_id_2)
            if generated_data_2:
                if generated_data_2.get_generated_data(): print(generated_data_2.get_generated_data())
            sleep(3)
        else:
            sleep(0.1)
