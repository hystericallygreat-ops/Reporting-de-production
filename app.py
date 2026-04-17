import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Production", layout="wide")

st.title("📊 Dashboard de Production")

uploaded_file = st.file_uploader("📂 Upload fichier DATA", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Data")
    df.columns = df.columns.str.strip()
    df = df.fillna(0)

    def safe_div(a, b):
        return a / b if b != 0 else 0

    df["% transfo"] = df.apply(lambda x: safe_div(x["Clients nets"], x["Contacts uniques"]), axis=1)
    df["Vph"] = df.apply(lambda x: safe_div(x["Ventes nettes \n"], x["Heures Attribution  "]), axis=1)
    df["Entrants reçus/h"] = df.apply(lambda x: safe_div(x["Appels entrants"], x["Heures Attribution  "]), axis=1)
    df["Tickets reçus/h"] = df.apply(lambda x: safe_div(x["Tickets reçus"], x["Heures Attribution  "]), axis=1)
    df["Attrib reçus/h"] = df.apply(lambda x: safe_div(x["Tickets reçus"] + x["Appels entrants"], x["Heures Attribution  "]), axis=1)
    df["Taux de rendement"] = df.apply(lambda x: safe_div(x["Clients nets"], x["Tickets reçus"] + x["Appels entrants"]), axis=1)

    st.subheader("📊 KPI")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Ventes", int(df["Ventes nettes \n"].sum()))
    col2.metric("Total Clients", int(df["Clients nets"].sum()))
    col3.metric("Rendement moyen", round(df["Taux de rendement"].mean(), 2))

    st.subheader("📈 Graphiques")
    st.bar_chart(df.set_index("Agent")["Ventes nettes \n"])

    st.subheader("📋 Données")
    st.dataframe(df)
