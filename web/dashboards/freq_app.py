"""Необязательный интерактивный дашборд по базе популяционных частот.

Запуск: pip install -r requirements-optional.txt
       streamlit run web/dashboards/freq_app.py
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "projects" / "07_freqdb" / "src"))

import freqdb


def ensure_db():
    rows = freqdb.demo_rows()
    freqdb.write_demo(freqdb.DATA, rows)
    return rows


def frame_of(rows):
    import pandas as pd

    frame = pd.DataFrame(rows, columns=["key", "chrom", "pos", "ref", "alt", "af", "population"])
    return frame


def show_metrics(rows, selected):
    columns = st.columns(3)
    columns[0].metric("Вариантов в базе", len(rows))
    columns[1].metric("Прошли фильтр", len(selected))
    columns[2].metric("Средняя частота", f"{freqdb.average([row[5] for row in selected]) if selected else 0:.3f}")


def show_charts(connection, chosen, selected):
    stats = freqdb.district_rows(connection)
    st.subheader("Средняя частота по округам")
    st.bar_chart({row["name"]: row["af"] for row in stats if row["name"] in chosen})
    st.subheader("Распределение частот")
    st.bar_chart(freqdb.af_histogram([row[5] for row in selected]))


def choose_filters(districts):
    chosen = st.multiselect("Округа", districts, default=districts)
    min_af = st.slider("Минимальная частота AF", 0.0, 0.5, 0.05, 0.005)
    return chosen, min_af


def show_table(selected):
    st.subheader("Варианты")
    st.dataframe(frame_of(selected).head(200))


def show_lookup(connection):
    key = st.text_input("Поиск по ключу", "1:10000:A>G")
    st.json(freqdb.lookup_variant(connection, key))


def main():
    st.set_page_config(page_title="Частоты вариантов", layout="wide")
    st.title("База популяционных частот (синтетика)")
    rows = ensure_db()
    connection = freqdb.open_db(freqdb.DB_PATH)
    districts = [district["name"] for district in freqdb.DISTRICTS]
    chosen, min_af = choose_filters(districts)
    selected = [row for row in rows if row[6] in chosen and row[5] >= min_af]
    show_metrics(rows, selected)
    show_charts(connection, chosen, selected)
    show_table(selected)
    show_lookup(connection)


main()
