"""Необязательный интерактивный дашборд по бюджету кластера.

Запуск: pip install -r requirements-optional.txt
       streamlit run web/dashboards/cluster_app.py
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "projects" / "04_cluster_budget" / "src"))

import budget


def load():
    jobs = budget.demo_jobs()
    return jobs, budget.summarize(jobs)


def reshape_frame(jobs):
    import pandas as pd

    frame = pd.DataFrame(jobs)
    frame["перерасход, ГБ"] = (frame["req_mem"] - frame["max_rss"]) / 1024
    return frame


def show_metrics(jobs, rows):
    before = sum(row["before"] for row in rows)
    after = sum(row["after"] for row in rows)
    columns = st.columns(4)
    columns[0].metric("Задач", len(jobs))
    columns[1].metric("Core-hours до", f"{before:.0f}")
    columns[2].metric("Core-hours после", f"{after:.0f}", f"−{budget.savings(before, after)}%")
    columns[3].metric("Средняя загрузка CPU", f"{budget.mean([budget.cpu_efficiency(job) for job in jobs]) * 100:.0f}%")


def show_charts(rows, jobs, steps, limit):
    chosen = [row for row in rows if row["step"] in steps]
    st.subheader("Core-hours по шагам")
    st.bar_chart({row["step"]: {"до": row["before"], "после": row["after"]} for row in chosen})
    st.subheader("Запрошено против использовано")
    frame = reshape_frame(jobs)
    st.scatter_chart(frame[frame["step"].isin(steps)], x="req_mem", y="max_rss", color="step")
    st.subheader("Худшие задачи")
    st.dataframe(frame.sort_values("перерасход, ГБ", ascending=False).head(limit))


def main():
    st.set_page_config(page_title="Бюджет кластера", layout="wide")
    st.title("Бюджет кластера: где сгорают core-hours")
    jobs, rows = load()
    show_metrics(jobs, rows)
    steps = st.multiselect("Шаги пайплайна", budget.STEPS, default=budget.STEPS)
    limit = st.slider("Показать худших задач", 3, len(jobs), 8)
    show_charts(rows, jobs, steps, limit)


main()
