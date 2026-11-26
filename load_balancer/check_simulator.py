
from simulator import Server, Task

server = Server(
    server_id=1,
    speed=100,
    ram_total=8192,
    cpu_utilization=20
)

task1 = Task(
    task_id=1,
    work=500,
    ram_required=1024
)

task2 = Task(
    task_id=2,
    work=300,
    ram_required=2048
)

print("Додавання першого завдання:", server.add_task(task1))
print("Додавання другого завдання:", server.add_task(task2))

print("Кількість завдань:", server.active_tasks)
print("Завантаження RAM:", round(server.ram_utilization, 2), "%")
print("Ефективна швидкість:", round(server.effective_speed, 2))
print(
    "Орієнтовний час виконання:",
    round(server.estimated_completion_time(
        Task(task_id=3, work=200, ram_required=512)
    ), 2)
)

server.remove_task(1)
print("Завдань після видалення:", server.active_tasks)
