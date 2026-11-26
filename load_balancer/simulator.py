"""Подієва модель виконання завдань на віртуальних серверах."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from math import inf
from typing import Any


@dataclass
class Task:
    """Обчислювальне завдання, що надходить до системи."""

    task_id: int
    work: float
    ram_required: float
    arrival_time: float = 0.0
    remaining_work: float = field(init=False)
    start_time: float | None = None
    finish_time: float | None = None
    assigned_server: int | None = None
    status: str = "pending"

    def __post_init__(self) -> None:
        if self.work <= 0:
            raise ValueError("Обсяг роботи завдання має бути більшим за 0.")
        if self.ram_required < 0:
            raise ValueError("Потреба в RAM не може бути від'ємною.")
        if self.arrival_time < 0:
            raise ValueError("Час надходження не може бути від'ємним.")
        self.work = float(self.work)
        self.ram_required = float(self.ram_required)
        self.arrival_time = float(self.arrival_time)
        self.remaining_work = self.work

    @property
    def response_time(self) -> float | None:
        if self.finish_time is None:
            return None
        return self.finish_time - self.arrival_time

    @property
    def waiting_time(self) -> float | None:
        if self.start_time is None:
            return None
        return self.start_time - self.arrival_time


class Server:
    """Віртуальний сервер з одним обчислювальним каналом і FIFO-чергою."""

    def __init__(
        self,
        server_id: int,
        speed: float,
        ram_total: float,
        cpu_utilization: float = 0.0,
    ) -> None:
        if speed <= 0:
            raise ValueError("Швидкість сервера має бути більшою за 0.")
        if ram_total <= 0:
            raise ValueError("Обсяг RAM має бути більшим за 0.")
        if not 0 <= cpu_utilization < 100:
            raise ValueError("Початкове завантаження CPU має бути в межах [0; 100).")

        self.server_id = server_id
        self.speed = float(speed)
        self.ram_total = float(ram_total)
        self.base_cpu_utilization = float(cpu_utilization)
        self._queue: deque[Task] = deque()
        self.completed_tasks: list[Task] = []
        self.current_time = 0.0

    @property
    def active_tasks(self) -> int:
        return len(self._queue)

    @property
    def ram_used(self) -> float:
        return sum(task.ram_required for task in self._queue)

    @property
    def ram_utilization(self) -> float:
        return 100.0 * self.ram_used / self.ram_total

    @property
    def cpu_utilization(self) -> float:
        # Базове навантаження плюс навантаження від активної роботи.
        workload_load = 0.0 if not self._queue else 25.0 + 8.0 * (len(self._queue) - 1)
        return min(95.0, self.base_cpu_utilization + workload_load)

    @property
    def effective_speed(self) -> float:
        # Для розрахунку швидкості враховується поточне навантаження CPU.
        return max(self.speed * (1.0 - self.cpu_utilization / 100.0), self.speed * 0.01)

    @property
    def running_task(self) -> Task | None:
        return self._queue[0] if self._queue else None

    def can_accept(self, task: Task) -> bool:
        return self.ram_used + task.ram_required <= self.ram_total

    def add_task(self, task: Task) -> bool:
        if not self.can_accept(task):
            return False
        if any(item.task_id == task.task_id for item in self._queue):
            raise ValueError(f"Завдання з ID {task.task_id} вже призначене серверу.")
        self._queue.append(task)
        task.assigned_server = self.server_id
        task.status = "queued"
        if len(self._queue) == 1:
            task.status = "running"
            task.start_time = self.current_time
        return True

    def remove_task(self, task_id: int) -> bool:
        """Видаляє завдання з черги та звільняє зарезервовану RAM."""
        for task in tuple(self._queue):
            if task.task_id == task_id:
                was_running = task is self._queue[0]
                self._queue.remove(task)
                task.status = "cancelled"
                if was_running and self._queue:
                    self._queue[0].status = "running"
                    self._queue[0].start_time = self.current_time
                return True
        return False

    def estimated_completion_time(self, task: Task) -> float:
        pending_work = sum(item.remaining_work for item in self._queue)
        return (pending_work + task.work) / self.effective_speed

    def time_to_completion(self) -> float:
        if not self._queue:
            return inf
        return self._queue[0].remaining_work / self.effective_speed

    def advance(self, duration: float) -> list[Task]:
        """Просуває модельний час; може завершити кілька FIFO-завдань."""
        if duration < 0:
            raise ValueError("Інтервал моделювання не може бути від'ємним.")
        remaining_time = float(duration)
        finished: list[Task] = []

        while self._queue and remaining_time > 1e-12:
            task = self._queue[0]
            rate = self.effective_speed
            required_time = task.remaining_work / rate

            if required_time <= remaining_time + 1e-12:
                consumed = min(required_time, remaining_time)
                task.remaining_work = 0.0
                remaining_time -= consumed
                self.current_time += consumed
                task.finish_time = self.current_time
                task.status = "completed"
                self._queue.popleft()
                self.completed_tasks.append(task)
                finished.append(task)
                if self._queue:
                    self._queue[0].status = "running"
                    if self._queue[0].start_time is None:
                        self._queue[0].start_time = self.current_time
            else:
                task.remaining_work -= rate * remaining_time
                self.current_time += remaining_time
                remaining_time = 0.0

        # Сервер без активних завдань також просуває власний годинник.
        if not self._queue and remaining_time > 1e-12:
            self.current_time += remaining_time
        return finished

    def reset(self) -> None:
        self._queue.clear()
        self.completed_tasks.clear()
        self.current_time = 0.0

    def snapshot(self, timestamp: float) -> dict[str, Any]:
        return {
            "time": float(timestamp),
            "server_id": self.server_id,
            "active_tasks": self.active_tasks,
            "cpu_utilization": self.cpu_utilization,
            "ram_used": self.ram_used,
            "ram_total": self.ram_total,
            "ram_utilization": self.ram_utilization,
            "effective_speed": self.effective_speed,
        }


@dataclass
class SimulationResult:
    task_records: list[dict[str, Any]]
    server_history: list[dict[str, Any]]
    metrics: dict[str, Any]
    simulation_time: float


def run_simulation(
    servers: list[Server],
    tasks: list[Task],
    algorithm: Any,
) -> SimulationResult:
    """Виконує подієву симуляцію надходження, призначення та завершення задач."""
    if not servers:
        raise ValueError("Для симуляції потрібен хоча б один сервер.")

    # Кожен запуск починається з однакового чистого стану вузлів.
    for server in servers:
        server.reset()

    ordered_tasks = sorted(tasks, key=lambda item: (item.arrival_time, item.task_id))
    if len({task.task_id for task in ordered_tasks}) != len(ordered_tasks):
        raise ValueError("ID завдань мають бути унікальними.")
    for task in ordered_tasks:
        task.remaining_work = task.work
        task.start_time = None
        task.finish_time = None
        task.assigned_server = None
        task.status = "pending"

    history: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    index = 0
    now = 0.0

    def save_snapshot(timestamp: float) -> None:
        history.extend(server.snapshot(timestamp) for server in servers)

    save_snapshot(now)

    while index < len(ordered_tasks) or any(server.active_tasks for server in servers):
        next_arrival = (
            ordered_tasks[index].arrival_time
            if index < len(ordered_tasks)
            else inf
        )
        next_completion_delta = min(
            (server.time_to_completion() for server in servers),
            default=inf,
        )
        next_completion = now + next_completion_delta
        next_event = min(next_arrival, next_completion)

        if next_event == inf:
            break

        delta = max(0.0, next_event - now)
        if delta > 0:
            for server in servers:
                server.advance(delta)
            now = next_event
            save_snapshot(now)

        # Усі завершення на поточному моменті вже оброблені advance().
        while index < len(ordered_tasks) and ordered_tasks[index].arrival_time <= now + 1e-12:
            task = ordered_tasks[index]
            selected = algorithm.select_server(servers, task)
            if selected is not None and selected.add_task(task):
                task.status = "running" if selected.running_task is task else "queued"
                records.append(_task_record(task, "accepted"))
            else:
                task.status = "rejected"
                records.append(_task_record(task, "rejected"))
            index += 1
            save_snapshot(now)

        # Захист від зациклення на події без просування часу.
        if delta == 0 and next_arrival > now + 1e-12:
            break

    simulation_time = max(
        now,
        max((task.finish_time or task.arrival_time for task in ordered_tasks), default=0.0),
    )

    # Оновлюємо записи після завершення: часи були невідомі під час призначення.
    record_by_id = {record["task_id"]: record for record in records}
    for task in ordered_tasks:
        record = record_by_id[task.task_id]
        record.update(_task_record(task, record["result"]))

    from metrics import calculate_metrics

    metrics = calculate_metrics(records, history, simulation_time, servers)
    return SimulationResult(records, history, metrics, simulation_time)


def _task_record(task: Task, result: str) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "work": task.work,
        "ram_required": task.ram_required,
        "arrival_time": task.arrival_time,
        "start_time": task.start_time,
        "finish_time": task.finish_time,
        "response_time": task.response_time,
        "waiting_time": task.waiting_time,
        "server_id": task.assigned_server,
        "status": task.status,
        "result": result,
    }
