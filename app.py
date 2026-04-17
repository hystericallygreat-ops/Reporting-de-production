import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Production", layout="wide")

st.title("📊 Dashboard de Production")

# Upload fichier
uploaded_file = st.file_uploader("📂 Upload fichier DATA", type=["xlsx"])

if uploaded_file:
    # Lire fichier
    df = pd.read_excel(uploaded_file, sheet_name=0)

    # 🔍 DEBUG (tu peux supprimer après)
    st.write("Colonnes détectées :", df.columns.tolist())

    # 🧹 Nettoyage colonnes (CRUCIAL)
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\n", "", regex=True)
        .str.replace("\r", "", regex=True)
        .str.replace("  ", " ", regex=True)
    )

    # 🔁 Renommer colonnes (adapté à ton fichier)
    df = df.rename(columns={
        "Ventes nettes": "ventes",
        "Heures Attribution": "heures",
        "Clients nets": "clients",
        "Contacts uniques": "contacts",
        "Tickets reçus": "tickets",
        "Appels entrants": "appels",
        "Agent": "agent"
    })

    # Remplacer NaN
    df = df.fillna(0)

    # ⚠️ éviter division par 0
    def safe_div(a, b):
        return a / b if b != 0 else 0

    # 📊 Calculs (version robuste)
    df["% transfo"] = df.apply(lambda x: safe_div(x["clients"], x["contacts"]), axis=1)
    df["vph"] = df.apply(lambda x: safe_div(x["ventes"], x["heures"]), axis=1)
    df["entrants/h"] = df.apply(lambda x: safe_div(x["appels"], x["heures"]), axis=1)
    df["tickets/h"] = df.apply(lambda x: safe_div(x["tickets"], x["heures"]), axis=1)
    df["attrib/h"] = df.apply(lambda x: safe_div(x["tickets"] + x["appels"], x["heures"]), axis=1)
    df["rendement"] = df.apply(lambda x: safe_div(x["clients"], x["tickets"] + x["appels"]), axis=1)

    # 📊 KPI
    st.subheader("📊 KPI")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Ventes", int(df["ventes"].sum()))
    col2.metric("Total Clients", int(df["clients"].sum()))
    col3.metric("Rendement moyen", round(df["rendement"].mean(), 2))

    # 📈 Graphique
    st.subheader("📈 Ventes par Agent")

    if "agent" in df.columns:
        st.bar_chart(df.set_index("agent")["ventes"])
    else:
        st.warning("Colonne 'Agent' non trouvée")

    # 📋 Tableau final
    st.subheader("📋 Données calculées")
    st.dataframe(df)
