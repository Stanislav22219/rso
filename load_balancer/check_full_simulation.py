from simulator import Server, Task, run_simulation
from algorithms import RoundRobin, LeastConnections, ACLB


def make_servers():
    return [
        Server(1, speed=100, ram_total=8192, cpu_utilization=20),
        Server(2, speed=150, ram_total=16384, cpu_utilization=35),
        Server(3, speed=80, ram_total=8192, cpu_utilization=10),
    ]


def main():
    tasks = [
        Task(1, work=500, ram_required=1024, arrival_time=0),
        Task(2, work=300, ram_required=2048, arrival_time=0),
        Task(3, work=700, ram_required=1024, arrival_time=1),
        Task(4, work=200, ram_required=512, arrival_time=2),
        Task(5, work=600, ram_required=2048, arrival_time=3),
        Task(6, work=400, ram_required=1024, arrival_time=4),
    ]

    for name, algorithm in [
        ("Round Robin", RoundRobin()),
        ("Least Connections", LeastConnections()),
        ("ACLB", ACLB()),
    ]:
        result = run_simulation(make_servers(), tasks, algorithm)
        print(f"\n{name}")
        print("Метрики:")
        for key, value in result.metrics.items():
            if key != "server_metrics":
                print(f"  {key}: {value}")
        print("Завдання:")
        for row in result.task_records:
            print(row)

        assert result.metrics["completed_tasks"] == len(tasks)
        assert result.metrics["rejected_tasks"] == 0
        assert all(row["finish_time"] is not None for row in result.task_records)

    # Перевірка відхилення завдання, яке не поміщається в RAM жодного вузла.
    rejected_result = run_simulation(
        [Server(1, speed=100, ram_total=1024)],
        [Task(99, work=100, ram_required=2048)],
        RoundRobin(),
    )
    assert rejected_result.metrics["rejected_tasks"] == 1
    assert rejected_result.metrics["completed_tasks"] == 0

    print("\nУсі перевірки повної симуляції пройдено успішно.")


if __name__ == "__main__":
    main()
