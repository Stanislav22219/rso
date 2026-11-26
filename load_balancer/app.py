
"""
Load Balancer
tor
Вебінтерфейс для моделювання та порівняння алгоритмів балансування.
Python 3.12, Streamlit, Plotly.
"""

from __future__ import annotations

import random
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from simulator import Server, Task, run_simulation
from algorithms import RoundRobin, LeastConnections, ACLB


# ---------------------------------------------------------
# Налаштування сторінки
# ---------------------------------------------------------

st.set_page_config(
    page_title="Load Balancer Simulator",
    page_icon="⚖️",
    layout="wide",
)

st.title("Load Balancer Simulator")
st.caption(
    "Симулятор динамічного розподілу обчислювальних завдань "
    "між віртуальними серверами"
)


# ---------------------------------------------------------
# Допоміжні функції
# ---------------------------------------------------------

def generate_tasks(
    count: int,
    seed: int,
    work_min: int,
    work_max: int,
    ram_min: int,
    ram_max: int,
    arrival_interval: float,
) -> list[dict[str, Any]]:
    """
    Генерує набір завдань.
    Повертає словники, щоб для кожного алгоритму
    можна було створити незалежні об'єкти Task.
    """

    rng = random.Random(seed)
    tasks = []
    arrival_time = 0.0

    for task_id in range(1, count + 1):
        if task_id > 1:
            arrival_time += rng.uniform(
                0.1,
                max(0.1, arrival_interval),
            )

        tasks.append(
            {
                "task_id": task_id,
                "work": rng.randint(work_min, work_max),
                "ram_required": rng.randint(ram_min, ram_max),
                "arrival_time": arrival_time,
            }
        )

    return tasks


def create_servers(
    server_configs: list[dict[str, Any]],
) -> list[Server]:
    """Створює нові сервери для окремого запуску алгоритму."""

    return [
        Server(
            server_id=config["server_id"],
            speed=config["speed"],
            ram_total=config["ram_total"],
            cpu_utilization=config["cpu_utilization"],
        )
        for config in server_configs
    ]


def create_task_objects(
    task_configs: list[dict[str, Any]],
) -> list[Task]:
    """Створює нові об'єкти завдань для окремої симуляції."""

    return [
        Task(
            task_id=item["task_id"],
            work=item["work"],
            ram_required=item["ram_required"],
            arrival_time=item["arrival_time"],
        )
        for item in task_configs
    ]


def run_all_algorithms(
    task_configs: list[dict[str, Any]],
    server_configs: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Запускає всі алгоритми на однакових початкових даних.
    Для кожного запуску створюються незалежні сервери та завдання.
    """

    algorithms = {
        "Round Robin": RoundRobin,
        "Least Connections": LeastConnections,
        "ACLB": ACLB,
    }

    results = {}

    for name, algorithm_class in algorithms.items():
        servers = create_servers(server_configs)
        tasks = create_task_objects(task_configs)
        algorithm = algorithm_class()

        result = run_simulation(
            servers=servers,
            tasks=tasks,
            algorithm=algorithm,
        )

        results[name] = {
            "metrics": result.metrics,
            "task_records": result.task_records,
            "server_history": result.server_history,
            "simulation_time": result.simulation_time,
        }

    return results


def build_comparison_table(
    results: dict[str, Any],
) -> pd.DataFrame:
    """Формує таблицю порівняння показників алгоритмів."""

    rows = []

    for name, result in results.items():
        metrics = result["metrics"]

        rows.append(
            {
                "Алгоритм": name,
                "Всього завдань": metrics["total_tasks"],
                "Виконано": metrics["completed_tasks"],
                "Відхилено": metrics["rejected_tasks"],
                "Середній час відповіді": round(
                    metrics["average_response_time"], 3
                ),
                "Середній час очікування": round(
                    metrics["average_waiting_time"], 3
                ),
                "Пропускна здатність": round(
                    metrics["throughput"], 4
                ),
                "Середній CPU, %": round(
                    metrics["average_cpu_utilization"], 2
                ),
                "Середній RAM, %": round(
                    metrics["average_ram_utilization"], 2
                ),
                "Індекс Джейна": round(
                    metrics["jains_fairness_index"], 4
                ),
                "Час симуляції": round(
                    metrics["simulation_time"], 3
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------
# Бічна панель: параметри симуляції
# ---------------------------------------------------------

st.sidebar.header("Параметри симуляції")

server_count = st.sidebar.slider(
    "Кількість серверів",
    min_value=2,
    max_value=6,
    value=3,
)

task_count = st.sidebar.slider(
    "Кількість завдань",
    min_value=5,
    max_value=200,
    value=30,
    step=5,
)

seed = st.sidebar.number_input(
    "Seed генератора випадкових чисел",
    min_value=0,
    max_value=999999,
    value=42,
    step=1,
)

arrival_interval = st.sidebar.slider(
    "Максимальний інтервал надходження завдань",
    min_value=0.1,
    max_value=10.0,
    value=2.0,
    step=0.1,
)

st.sidebar.subheader("Характеристики завдань")

work_min = st.sidebar.number_input(
    "Мінімальна складність завдання",
    min_value=10,
    max_value=10000,
    value=200,
)

work_max = st.sidebar.number_input(
    "Максимальна складність завдання",
    min_value=10,
    max_value=20000,
    value=1000,
)

ram_min = st.sidebar.number_input(
    "Мінімальна потреба в RAM (MB)",
    min_value=0,
    max_value=16000,
    value=512,
    step=128,
)

ram_max = st.sidebar.number_input(
    "Максимальна потреба в RAM (MB)",
    min_value=0,
    max_value=32000,
    value=2048,
    step=128,
)


# ---------------------------------------------------------
# Налаштування серверів
# ---------------------------------------------------------

st.sidebar.subheader("Конфігурація серверів")

server_configs = []

for server_id in range(1, server_count + 1):
    with st.sidebar.expander(
        f"Сервер {server_id}",
        expanded=(server_id == 1),
    ):
        speed = st.number_input(
            f"Швидкість сервера {server_id}",
            min_value=10,
            max_value=1000,
            value=100 + (server_id - 1) * 25,
            step=10,
            key=f"speed_{server_id}",
        )

        ram_total = st.selectbox(
            f"Обсяг RAM сервера {server_id} (MB)",
            options=[4096, 8192, 16384, 32768],
            index=1,
            key=f"ram_{server_id}",
        )

        cpu_utilization = st.slider(
            f"Початковий CPU сервера {server_id}, %",
            min_value=0,
            max_value=90,
            value=min(20 + (server_id - 1) * 5, 90),
            key=f"cpu_{server_id}",
        )

        server_configs.append(
            {
                "server_id": server_id,
                "speed": speed,
                "ram_total": ram_total,
                "cpu_utilization": cpu_utilization,
            }
        )


# ---------------------------------------------------------
# Запуск симуляції
# ---------------------------------------------------------

run_button = st.sidebar.button(
    "Запустити симуляцію",
    type="primary",
    use_container_width=True,
)

if run_button:
    if work_min > work_max:
        st.sidebar.error(
            "Мінімальна складність не може бути більшою за максимальну."
        )
    elif ram_min > ram_max:
        st.sidebar.error(
            "Мінімальна потреба в RAM не може бути більшою за максимальну."
        )
    else:
        with st.spinner("Виконується моделювання..."):
            task_configs = generate_tasks(
                count=task_count,
                seed=int(seed),
                work_min=int(work_min),
                work_max=int(work_max),
                ram_min=int(ram_min),
                ram_max=int(ram_max),
                arrival_interval=float(arrival_interval),
            )

            st.session_state["simulation_results"] = (
                run_all_algorithms(
                    task_configs=task_configs,
                    server_configs=server_configs,
                )
            )

            st.session_state["task_configs"] = task_configs
            st.session_state["server_configs"] = server_configs

        st.success("Симуляцію успішно завершено.")


# ---------------------------------------------------------
# Відображення результатів
# ---------------------------------------------------------

if "simulation_results" not in st.session_state:
    st.info(
        "Налаштуйте параметри серверів і завдань у бічній панелі, "
        "після чого натисніть «Запустити симуляцію»."
    )

else:
    results = st.session_state["simulation_results"]

    tab_comparison, tab_servers, tab_tasks, tab_method = st.tabs(
        [
            "Порівняння алгоритмів",
            "Сервери",
            "Журнал завдань",
            "Методика",
        ]
    )

    # -----------------------------------------------------
    # Вкладка 1. Порівняння алгоритмів
    # -----------------------------------------------------

    with tab_comparison:
        st.subheader("Порівняння показників ефективності")

        comparison_df = build_comparison_table(results)

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Середній час відповіді")

        response_df = comparison_df[
            ["Алгоритм", "Середній час відповіді"]
        ]

        fig_response = px.bar(
            response_df,
            x="Алгоритм",
            y="Середній час відповіді",
            color="Алгоритм",
            title="Середній час відповіді завдань",
        )

        st.plotly_chart(
            fig_response,
            use_container_width=True,
        )

        st.subheader("Пропускна здатність")

        throughput_df = comparison_df[
            ["Алгоритм", "Пропускна здатність"]
        ]

        fig_throughput = px.bar(
            throughput_df,
            x="Алгоритм",
            y="Пропускна здатність",
            color="Алгоритм",
            title="Кількість виконаних завдань за одиницю часу",
        )

        st.plotly_chart(
            fig_throughput,
            use_container_width=True,
        )

        st.subheader("Рівномірність розподілу навантаження")

        fairness_df = comparison_df[
            ["Алгоритм", "Індекс Джейна"]
        ]

        fig_fairness = px.bar(
            fairness_df,
            x="Алгоритм",
            y="Індекс Джейна",
            color="Алгоритм",
            range_y=[0, 1],
            title="Індекс справедливості Джейна",
        )

        st.plotly_chart(
            fig_fairness,
            use_container_width=True,
        )

        st.caption(
            "Вищий індекс Джейна відповідає рівномірнішому "
            "розподілу відповідного показника навантаження."
        )

    # -----------------------------------------------------
    # Вкладка 2. Сервери
    # -----------------------------------------------------

    with tab_servers:
        st.subheader("Динаміка завантаження серверів")

        selected_algorithm = st.selectbox(
            "Оберіть алгоритм",
            options=list(results.keys()),
            key="server_algorithm",
        )

        history = results[selected_algorithm]["server_history"]

        if history:
            history_df = pd.DataFrame(history)

            fig_cpu = px.line(
                history_df,
                x="time",
                y="cpu_utilization",
                color="server_id",
                markers=True,
                title="Зміна завантаження CPU",
                labels={
                    "time": "Модельний час",
                    "cpu_utilization": "CPU, %",
                    "server_id": "Сервер",
                },
            )

            st.plotly_chart(
                fig_cpu,
                use_container_width=True,
            )

            fig_ram = px.line(
                history_df,
                x="time",
                y="ram_utilization",
                color="server_id",
                markers=True,
                title="Зміна використання оперативної пам'яті",
                labels={
                    "time": "Модельний час",
                    "ram_utilization": "RAM, %",
                    "server_id": "Сервер",
                },
            )

            st.plotly_chart(
                fig_ram,
                use_container_width=True,
            )

            fig_active = px.line(
                history_df,
                x="time",
                y="active_tasks",
                color="server_id",
                markers=True,
                title="Кількість активних завдань на серверах",
                labels={
                    "time": "Модельний час",
                    "active_tasks": "Активні завдання",
                    "server_id": "Сервер",
                },
            )

            st.plotly_chart(
                fig_active,
                use_container_width=True,
            )

        server_metrics = results[selected_algorithm]["metrics"][
            "server_metrics"
        ]

        st.subheader("Підсумкові показники серверів")

        server_df = pd.DataFrame(server_metrics)

        if not server_df.empty:
            server_df = server_df.rename(
                columns={
                    "server_id": "ID сервера",
                    "average_cpu_utilization": "Середній CPU, %",
                    "average_ram_utilization": "Середній RAM, %",
                    "completed_tasks": "Виконано завдань",
                }
            )

            st.dataframe(
                server_df.round(2),
                use_container_width=True,
                hide_index=True,
            )

    # -----------------------------------------------------
    # Вкладка 3. Журнал завдань
    # -----------------------------------------------------

    with tab_tasks:
        st.subheader("Журнал виконання завдань")

        selected_task_algorithm = st.selectbox(
            "Оберіть алгоритм для перегляду журналу",
            options=list(results.keys()),
            key="task_algorithm",
        )

        task_records = results[selected_task_algorithm]["task_records"]

        task_df = pd.DataFrame(task_records)

        if not task_df.empty:
            task_df = task_df.rename(
                columns={
                    "task_id": "ID завдання",
                    "work": "Обчислювальна складність",
                    "ram_required": "Потреба RAM (MB)",
                    "arrival_time": "Час надходження",
                    "start_time": "Час початку",
                    "finish_time": "Час завершення",
                    "response_time": "Час відповіді",
                    "waiting_time": "Час очікування",
                    "server_id": "ID сервера",
                    "status": "Статус",
                    "result": "Результат призначення",
                }
            )

            st.dataframe(
                task_df,
                use_container_width=True,
                hide_index=True,
            )

            csv_data = task_df.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                label="Завантажити журнал у CSV",
                data=csv_data,
                file_name=f"tasks_{selected_task_algorithm.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )

    # -----------------------------------------------------
    # Вкладка 4. Методика
    # -----------------------------------------------------

    with tab_method:
        st.subheader("Методика моделювання")

        st.markdown(
            """
            У симуляторі реалізовано три алгоритми балансування:

            **Round Robin** — почерговий розподіл завдань між
            доступними серверами.

            **Least Connections** — вибір сервера з найменшою
            кількістю активних завдань.

            **ACLB (Adaptive Composite Load Balancing)** —
            адаптивний вибір сервера на основі комплексної оцінки
            прогнозованого часу виконання, завантаження CPU
            та використання RAM.

            Для ACLB використовується інтегральна оцінка:

            `Score = 0.55 · W + 0.30 · C + 0.15 · R`

            Для вибору сервера алгоритм порівнює оцінки доступних
            вузлів і вибирає вузол із найменшим значенням Score.

            Усі алгоритми запускаються на однакових початкових
            параметрах серверів та однаковому наборі завдань.
            """
        )

        st.subheader("Параметри поточного експерименту")

        st.write(
            f"Кількість серверів: "
            f"{len(st.session_state['server_configs'])}"
        )

        st.write(
            f"Кількість завдань: "
            f"{len(st.session_state['task_configs'])}"
        )

        st.write(
            f"Seed: {seed}"
        )

        st.write(
            f"Інтервал надходження: {arrival_interval}"
        )

        st.info(
            "Отримані результати характеризують саме обрану "
            "конфігурацію симуляції. Для загальних висновків "
            "потрібно виконати серію експериментів із різними "
            "параметрами навантаження."
        )
