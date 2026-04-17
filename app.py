import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Production", layout="wide")

st.title("📊 Dashboard de Production")

uploaded_file = st.file_uploader("📂 Upload fichier DATA", type=["xlsx"])

if uploaded_file:

    # 📥 Charger fichier
    excel = pd.ExcelFile(uploaded_file)

    st.write("Feuilles :", excel.sheet_names)

    df = pd.read_excel(excel, sheet_name=excel.sheet_names[0])  # DATA
    mapping = pd.read_excel(excel, sheet_name="Code")  # FEUILLE CODE

    # 🧹 Nettoyage
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

    # 🔍 DEBUG
    st.write("DATA cols:", df.columns.tolist())
    st.write("MAPPING cols:", mapping.columns.tolist())

    # 🔁 Rename DATA
    df = df.rename(columns={
        "Agent": "agent",
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
        "Log1": "log1",
        "Log2": "log2"
    })

    # 🔥 CRÉER MAPPING NOM + LOG
    name_map = {}
    log_map = {}

    for _, row in mapping.iterrows():

        final = row["agent_final"]

        if pd.notna(row["log1"]):
            name_map[row["log1"]] = final
            log_map[row["log1"]] = "Log1"

        if pd.notna(row["log2"]):
            name_map[row["log2"]] = final
            log_map[row["log2"]] = "Log2"

    # 🎯 APPLIQUER MAPPING
    df["log"] = df["agent"].map(log_map)
    df["agent"] = df["agent"].map(name_map).fillna(df["agent"])

    # 🔍 Vérif
    st.write("Logs détectés :", df["log"].unique())

    df = df.fillna(0)

    # ⚠️ division safe
    def safe_div(a, b):
        return a / b if b != 0 else 0

    # 📊 Calculs
    df["% transfo"] = df.apply(lambda x: safe_div(x["clients"], x["contacts"]), axis=1)
    df["vph"] = df.apply(lambda x: safe_div(x["ventes"], x["heures"]), axis=1)
    df["rendement"] = df.apply(lambda x: safe_div(x["clients"], x["tickets"] + x["appels"]), axis=1)

    # 🎯 FILTRE LOG
    st.subheader("🎯 Filtre par Source")

    if "log" in df.columns:
        selected_log = st.selectbox("Choisir une source", df["log"].dropna().unique())
        df_filtered = df[df["log"] == selected_log]
    else:
        st.error("Colonne log non créée")
        df_filtered = df

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
