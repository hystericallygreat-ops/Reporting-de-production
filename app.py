import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.set_page_config(
    page_title="Pilotage Performance Agents",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Pilotage de Performance Agents")
st.markdown("---")


# ==============================
# 🔧 UTILS
# ==============================
def normalize(s):
    return re.sub(r'\s+', ' ', str(s).strip().lower())


@st.cache_data
def load_data(file):

    xl = pd.ExcelFile(file)
    sheet_names_lower = {s.lower(): s for s in xl.sheet_names}

    # ==============================
    # 📌 FEUILLE CODE
    # ==============================
    code_sheet = sheet_names_lower.get('code')
    if not code_sheet:
        st.error("Feuille 'Code' introuvable")
        st.stop()

    df_code = pd.read_excel(file, sheet_name=code_sheet)
    df_code.columns = ['Agent', 'Log2_name', 'Log1_id']
    df_code = df_code.dropna(subset=['Agent'])

    df_code['Agent'] = df_code['Agent'].astype(str).str.strip()
    df_code['Agent_norm'] = df_code['Agent'].apply(normalize)
    df_code['Log1_norm'] = df_code['Log1_id'].apply(normalize)
    df_code['Log2_norm'] = df_code['Log2_name'].apply(normalize)

    # ==============================
    # 🔥 MAPPING GLOBAL UNIQUE
    # ==============================
    global_map = {}

    for _, row in df_code.iterrows():
        agent = row['Agent']

        if pd.notna(row['Log1_norm']):
            global_map[row['Log1_norm']] = agent

        if pd.notna(row['Log2_norm']):
            global_map[row['Log2_norm']] = agent

        global_map[row['Agent_norm']] = agent

    # ==============================
    # 📌 FEUILLE DATA
    # ==============================
    data_sheet = sheet_names_lower.get('data')
    if not data_sheet:
        st.error("Feuille 'data' introuvable")
        st.stop()

    df_raw = pd.read_excel(file, sheet_name=data_sheet, header=None)

    # ==============================
    # 📞 APPELS
    # ==============================
    df_appels = df_raw.iloc[1:, [0, 1]].copy()
    df_appels.columns = ['Agent_appels', 'Appels']
    df_appels = df_appels.dropna(subset=['Agent_appels'])

    df_appels['Agent_norm'] = df_appels['Agent_appels'].apply(normalize)
    df_appels['Agent'] = df_appels['Agent_norm'].map(global_map).fillna(df_appels['Agent_appels'])
    df_appels['Appels'] = pd.to_numeric(df_appels['Appels'], errors='coerce').fillna(0)

    # ==============================
    # 📊 LOG1
    # ==============================
    df_log1 = df_raw.iloc[1:, [2, 3, 4]].copy()
    df_log1.columns = ['Log1_id', 'Clients', 'Ventes']
    df_log1 = df_log1.dropna(subset=['Log1_id'])

    df_log1['Log1_norm'] = df_log1['Log1_id'].apply(normalize)
    df_log1['Agent'] = df_log1['Log1_norm'].map(global_map).fillna(df_log1['Log1_id'])

    df_log1['Clients'] = pd.to_numeric(df_log1['Clients'], errors='coerce').fillna(0)
    df_log1['Ventes'] = pd.to_numeric(df_log1['Ventes'], errors='coerce').fillna(0)

    # ==============================
    # 🎫 LOG2
    # ==============================
    df_log2 = df_raw.iloc[1:, [5, 6]].copy()
    df_log2.columns = ['Log2_name', 'Tickets']
    df_log2 = df_log2.dropna(subset=['Log2_name'])

    df_log2['Log2_norm'] = df_log2['Log2_name'].apply(normalize)
    df_log2['Agent'] = df_log2['Log2_norm'].map(global_map).fillna(df_log2['Log2_name'])

    df_log2['Tickets'] = pd.to_numeric(df_log2['Tickets'], errors='coerce').fillna(0)

    # ==============================
    # 📞 CONTACTS
    # ==============================
    df_contacts = df_raw.iloc[1:, [7, 8]].copy()
    df_contacts.columns = ['Log2_name', 'Contacts']
    df_contacts = df_contacts.dropna(subset=['Log2_name'])

    df_contacts['Log2_norm'] = df_contacts['Log2_name'].apply(normalize)
    df_contacts['Agent'] = df_contacts['Log2_norm'].map(global_map).fillna(df_contacts['Log2_name'])

    df_contacts['Contacts'] = pd.to_numeric(df_contacts['Contacts'], errors='coerce').fillna(0)

    # ==============================
    # ⏱️ HEURES
    # ==============================
    df_heures = df_raw.iloc[1:, [9, 10]].copy()
    df_heures.columns = ['Agent_h', 'Heures']
    df_heures = df_heures.dropna(subset=['Agent_h'])

    df_heures['Agent_norm'] = df_heures['Agent_h'].apply(normalize)
    df_heures['Agent'] = df_heures['Agent_norm'].map(global_map).fillna(df_heures['Agent_h'])

    df_heures['Heures'] = pd.to_numeric(df_heures['Heures'], errors='coerce').fillna(0)

    return df_log1, df_log2, df_contacts, df_heures, df_appels


# ==============================
# 📂 UPLOAD
# ==============================
uploaded_file = st.sidebar.file_uploader("📂 Charger fichier", type=["xlsx"])

if not uploaded_file:
    st.stop()

df_log1, df_log2, df_contacts, df_heures, df_appels = load_data(uploaded_file)


# ==============================
# 🔗 AGRÉGATION
# ==============================
df_final = pd.DataFrame({'Agent': pd.concat([
    df_log1['Agent'],
    df_log2['Agent'],
    df_contacts['Agent'],
    df_heures['Agent'],
    df_appels['Agent']
]).dropna().unique()})

df_final = df_final.merge(df_log1.groupby('Agent')[['Clients', 'Ventes']].sum(), on='Agent', how='left')
df_final = df_final.merge(df_log2.groupby('Agent')[['Tickets']].sum(), on='Agent', how='left')
df_final = df_final.merge(df_contacts.groupby('Agent')[['Contacts']].sum(), on='Agent', how='left')
df_final = df_final.merge(df_heures.groupby('Agent')[['Heures']].sum(), on='Agent', how='left')
df_final = df_final.merge(df_appels.groupby('Agent')[['Appels']].sum(), on='Agent', how='left')

df_final = df_final.fillna(0)


# ==============================
# 📊 KPI (corrigé)
# ==============================
df_final['Taux_transfo_%'] = (
    (df_final['Clients'] / df_final['Contacts'].replace(0, pd.NA)) * 100
)

df_final['Ventes_par_heure'] = (
    df_final['Ventes'] / df_final['Heures'].replace(0, pd.NA)
)

df_final['Rendement_%'] = (
    df_final['Clients'] / (df_final['Tickets'] + df_final['Appels']).replace(0, pd.NA) * 100
)

# 🔒 sécurisation round
for col in ['Taux_transfo_%', 'Ventes_par_heure', 'Rendement_%']:
    df_final[col] = pd.to_numeric(df_final[col], errors='coerce').round(1)


# ==============================
# 🚫 FILTRE SOURCE (désactivé volontairement)
# ==============================
# st.sidebar.subheader("🔍 Filtres")
# source_options = ["Toutes les sources", "Log1", "Log2"]
# source_filter = st.sidebar.selectbox("Source de données", source_options)

df_display = df_final.copy()


# ==============================
# 📈 UI
# ==============================
st.subheader("📈 KPIs")

col1, col2, col3 = st.columns(3)

col1.metric("Ventes", int(df_display['Ventes'].sum()))
col2.metric("Clients", int(df_display['Clients'].sum()))
col3.metric("Agents", df_display['Agent'].nunique())

st.markdown("---")

st.subheader("📊 Ventes par agent")

chart_data = df_display.sort_values("Ventes", ascending=False).head(20)

fig = px.bar(chart_data, x="Ventes", y="Agent", orientation="h")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📋 Tableau")
st.dataframe(df_display, use_container_width=True)
