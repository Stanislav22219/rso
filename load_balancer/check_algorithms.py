
from simulator import Server, Task
from algorithms import RoundRobin, LeastConnections, ACLB


def create_servers():
    """Створення однакових початкових вузлів для тестування."""
    return [
        Server(
            server_id=1,
            speed=100,
            ram_total=8192,
            cpu_utilization=20
        ),
        Server(
            server_id=2,
            speed=150,
            ram_total=16384,
            cpu_utilization=35
        ),
        Server(
            server_id=3,
            speed=80,
            ram_total=8192,
            cpu_utilization=10
        )
    ]


tasks = [
    Task(task_id=1, work=500, ram_required=1024),
    Task(task_id=2, work=300, ram_required=2048),
    Task(task_id=3, work=700, ram_required=1024),
    Task(task_id=4, work=200, ram_required=512),
    Task(task_id=5, work=600, ram_required=2048),
    Task(task_id=6, work=400, ram_required=1024),
]

algorithms = {
    "Round Robin": RoundRobin(),
    "Least Connections": LeastConnections(),
    "ACLB": ACLB()
}

for algorithm_name, algorithm in algorithms.items():
    servers = create_servers()

    print(f"\n--- {algorithm_name} ---")

    for task in tasks:
        server = algorithm.select_server(servers, task)

        if server is not None:
            server.add_task(task)
            print(
                f"Завдання {task.task_id} -> "
                f"Вузол {server.server_id}"
            )
        else:
            print(
                f"Завдання {task.task_id} -> "
                "немає доступного вузла"
            )

    print("\nПідсумковий розподіл:")

    for server in servers:
        print(
            f"Вузол {server.server_id}: "
            f"{server.active_tasks} завдань, "
            f"RAM: {server.ram_used:.0f} MB"
        )
