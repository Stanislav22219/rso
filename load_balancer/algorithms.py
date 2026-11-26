
from simulator import Server, Task


class RoundRobin:
    """Алгоритм почергового розподілу завдань."""

    def __init__(self):
        self.current_index = 0

    def select_server(
        self,
        servers: list[Server],
        task: Task
    ) -> Server | None:
        if not servers:
            return None

        # Перевіряємо вузли по черзі, починаючи з поточного індексу
        for offset in range(len(servers)):
            index = (self.current_index + offset) % len(servers)
            server = servers[index]

            if server.can_accept(task):
                self.current_index = (index + 1) % len(servers)
                return server

        return None


class LeastConnections:
    """Вибір вузла з найменшою кількістю активних завдань."""

    def select_server(
        self,
        servers: list[Server],
        task: Task
    ) -> Server | None:
        available_servers = [
            server for server in servers
            if server.can_accept(task)
        ]

        if not available_servers:
            return None

        return min(
            available_servers,
            key=lambda server: (
                server.active_tasks,
                server.server_id
            )
        )


class ACLB:
    """
    Adaptive Composite Load Balancing.

    Адаптивний алгоритм на основі:
    - прогнозованого часу виконання;
    - завантаження CPU;
    - використання RAM.
    """

    def __init__(
        self,
        weight_work: float = 0.55,
        weight_cpu: float = 0.30,
        weight_ram: float = 0.15
    ):
        self.weight_work = weight_work
        self.weight_cpu = weight_cpu
        self.weight_ram = weight_ram

        if abs(
            weight_work + weight_cpu + weight_ram - 1.0
        ) > 0.000001:
            raise ValueError("Сума вагових коефіцієнтів має дорівнювати 1.")

    def select_server(
        self,
        servers: list[Server],
        task: Task
    ) -> Server | None:
        # Враховуємо лише вузли, які можуть прийняти завдання
        available_servers = [
            server for server in servers
            if server.can_accept(task)
        ]

        if not available_servers:
            return None

        # Прогнозований час виконання на кожному вузлі
        estimated_times = {
            server.server_id: server.estimated_completion_time(task)
            for server in available_servers
        }

        max_time = max(estimated_times.values())

        best_server = None
        best_score = float("inf")

        for server in available_servers:
            # Нормалізований показник прогнозованого часу
            if max_time > 0:
                normalized_work = (
                    estimated_times[server.server_id] / max_time
                )
            else:
                normalized_work = 0.0

            normalized_work = min(normalized_work, 1.0)

            # Поточне завантаження CPU
            cpu_load = server.cpu_utilization / 100

            # Прогнозоване використання RAM після призначення
            ram_load = (
                server.ram_used + task.ram_required
            ) / server.ram_total

            # Інтегральна оцінка вузла
            score = (
                self.weight_work * normalized_work
                + self.weight_cpu * cpu_load
                + self.weight_ram * ram_load
            )

            if score < best_score:
                best_score = score
                best_server = server

        return best_server
