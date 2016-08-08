import uuid

def generate_task_id():
    """
    Generate a unique id (in integer format).
    """
    new_id = uuid.uuid4()

    return new_id % 10000000
