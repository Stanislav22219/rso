"""Розрахунок показників ефективності симулятора."""

from __future__ import annotations

from typing import Any


def jains_fairness(values: list[float]) -> float:
    """Індекс справедливості Джейна для невід'ємних значень."""
    if not values:
        return 0.0
    total = sum(max(0.0, value) for value in values)
    squares = sum(max(0.0, value) ** 2 for value in values)
    if squares == 0:
        return 1.0
    return (total * total) / (len(values) * squares)


def calculate_metrics(
    task_records: list[dict[str, Any]],
    server_history: list[dict[str, Any]],
    simulation_time: float,
    servers: list[Any],
) -> dict[str, Any]:
    completed = [r for r in task_records if r["result"] == "accepted" and r["status"] == "completed"]
    rejected = [r for r in task_records if r["result"] == "rejected"]
    response_times = [r["response_time"] for r in completed if r["response_time"] is not None]
    waiting_times = [r["waiting_time"] for r in completed if r["waiting_time"] is not None]

    cpu_by_server: dict[int, list[float]] = {s.server_id: [] for s in servers}
    ram_by_server: dict[int, list[float]] = {s.server_id: [] for s in servers}
    for point in server_history:
        cpu_by_server.setdefault(point["server_id"], []).append(point["cpu_utilization"])
        ram_by_server.setdefault(point["server_id"], []).append(point["ram_utilization"])

    avg_cpu_per_server = [
        sum(values) / len(values) for values in cpu_by_server.values() if values
    ]
    avg_ram_per_server = [
        sum(values) / len(values) for values in ram_by_server.values() if values
    ]
    all_cpu = [value for values in cpu_by_server.values() for value in values]
    all_ram = [value for values in ram_by_server.values() for value in values]

    return {
        "total_tasks": len(task_records),
        "completed_tasks": len(completed),
        "rejected_tasks": len(rejected),
        "average_response_time": sum(response_times) / len(response_times) if response_times else 0.0,
        "average_waiting_time": sum(waiting_times) / len(waiting_times) if waiting_times else 0.0,
        "throughput": len(completed) / simulation_time if simulation_time > 0 else 0.0,
        "average_cpu_utilization": sum(all_cpu) / len(all_cpu) if all_cpu else 0.0,
        "average_ram_utilization": sum(all_ram) / len(all_ram) if all_ram else 0.0,
        "jains_fairness_index": jains_fairness(avg_cpu_per_server),
        "simulation_time": simulation_time,
        "server_metrics": [
            {
                "server_id": server_id,
                "average_cpu_utilization": sum(cpu_by_server[server_id]) / len(cpu_by_server[server_id]) if cpu_by_server[server_id] else 0.0,
                "average_ram_utilization": sum(ram_by_server[server_id]) / len(ram_by_server[server_id]) if ram_by_server[server_id] else 0.0,
                "completed_tasks": sum(1 for task in completed if task["server_id"] == server_id),
            }
            for server_id in cpu_by_server
        ],
    }
