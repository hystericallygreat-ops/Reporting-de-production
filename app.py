import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Production", layout="wide")

st.title("📊 Dashboard de Production")

uploaded_file = st.file_uploader("📂 Upload fichier DATA", type=["xlsx"])

if uploaded_file:

    # 📥 Lire les feuilles
    df = pd.read_excel(uploaded_file, sheet_name="data")
    mapping = pd.read_excel(uploaded_file, sheet_name=1)

    # 🧹 Nettoyage colonnes
    def clean(df):
        df.columns = (
            df.columns
            .str.strip()
            .str.replace("\n", "", regex=True)
            .str.replace("\r", "", regex=True)
        )
        return df

    df = clean(df)
    mapping = clean(mapping)

    # 🔁 Rename data
    df = df.rename(columns={
        "Agent": "agent",
        "Log": "log",
        "Ventes nettes": "ventes",
        "Heures Attribution": "heures",
        "Clients nets": "clients",
        "Contacts uniques": "contacts",
        "Tickets reçus": "tickets",
        "Appels entrants": "appels"
    })

    # 🔁 Rename mapping
    mapping = mapping.rename(columns={
        "Agent": "agent_final",
        "Log1": "log1_name",
        "Log2": "log2_name"
    })

    # 🔥 CRÉER DICTIONNAIRE DE MAPPING
    map_dict = {}

    for _, row in mapping.iterrows():
        if pd.notna(row["log1_name"]):
            map_dict[row["log1_name"]] = row["agent_final"]
        if pd.notna(row["log2_name"]):
            map_dict[row["log2_name"]] = row["agent_final"]

    # 🎯 APPLIQUER MAPPING
    df["agent"] = df["agent"].map(map_dict).fillna(df["agent"])

    # 🔍 DEBUG
    st.write("Agents après mapping :", df["agent"].unique())

    df = df.fillna(0)

    def safe_div(a, b):
        return a / b if b != 0 else 0

    # 📊 Calculs
    df["% transfo"] = df.apply(lambda x: safe_div(x["clients"], x["contacts"]), axis=1)
    df["vph"] = df.apply(lambda x: safe_div(x["ventes"], x["heures"]), axis=1)
    df["rendement"] = df.apply(lambda x: safe_div(x["clients"], x["tickets"] + x["appels"]), axis=1)

    # 🎯 FILTRE LOG
    st.subheader("🎯 Filtre par Source")
    selected_log = st.selectbox("Choisir une source", df["log"].dropna().unique())
    df_filtered = df[df["log"] == selected_log]

    # 📊 KPI
    st.subheader("📊 KPI")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Ventes", int(df_filtered["ventes"].sum()))
    col2.metric("Total Clients", int(df_filtered["clients"].sum()))
    col3.metric("Rendement moyen", round(df_filtered["rendement"].mean(), 2))

    # 📈 Graph
    st.subheader("📈 Ventes par Agent")
    st.bar_chart(df_filtered.groupby("agent")["ventes"].sum())

    # 📋 Tableau
    st.subheader("📋 Données")
    st.dataframe(df_filtered)
