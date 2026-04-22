import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
 
st.set_page_config(
    page_title="Pilotage Performance Agents",
    page_icon="📊",
    layout="wide"
)
 
st.title("📊 Pilotage de Performance Agents")
st.markdown("---")
 
 
def normalize(s):
    """Normalise une chaîne pour la comparaison : minuscules, espaces multiples supprimés."""
    return re.sub(r'\s+', ' ', str(s).strip().lower())
 
 
@st.cache_data
def load_data(file):
    xl = pd.ExcelFile(file)
    sheet_names_lower = {s.lower(): s for s in xl.sheet_names}
 
    # --- Feuille Code (mapping agents) ---
    code_sheet = sheet_names_lower.get('code')
    if not code_sheet:
        st.error("Feuille 'Code' introuvable dans le fichier.")
        st.stop()
    df_code = pd.read_excel(file, sheet_name=code_sheet, header=0)
    df_code.columns = ['Agent', 'Log2_name', 'Log1_id']
    df_code = df_code.dropna(subset=['Agent'])
    df_code['Log2_norm'] = df_code['Log2_name'].apply(normalize)
    df_code['Log1_norm'] = df_code['Log1_id'].apply(normalize)
    df_code['Agent'] = df_code['Agent'].astype(str).str.strip()
 
    # Dictionnaires de mapping
    map_log1 = dict(zip(df_code['Log1_norm'], df_code['Agent']))
    map_log2 = dict(zip(df_code['Log2_norm'], df_code['Agent']))
 
    # --- Feuille data ---
    data_sheet = sheet_names_lower.get('data')
    if not data_sheet:
        st.error("Feuille 'data' introuvable dans le fichier.")
        st.stop()
    df_raw = pd.read_excel(file, sheet_name=data_sheet, header=None)
 
    # == Sous-tableau 1 : Appels entrants (col 0 = nom agent, col 1 = appels) ==
    df_appels = df_raw.iloc[1:, [0, 1]].copy()
    df_appels.columns = ['Agent_appels', 'Appels_entrants']
    df_appels = df_appels.dropna(subset=['Agent_appels'])
    df_appels['Agent_appels'] = df_appels['Agent_appels'].astype(str).str.strip()
    df_appels['Appels_entrants'] = pd.to_numeric(df_appels['Appels_entrants'], errors='coerce')
    # Normaliser pour jointure
    df_appels['Agent_norm'] = df_appels['Agent_appels'].apply(normalize)
 
    # Créer mapping nom_appel -> Agent officiel
    # On cherche dans df_code si le nom correspond au Log2 ou au nom Agent
    agent_norm_map = dict(zip(df_code['Log2_norm'], df_code['Agent']))
    agent_norm_map.update(dict(zip(df_code['Agent'].apply(normalize), df_code['Agent'])))
    df_appels['Agent'] = df_appels['Agent_norm'].map(agent_norm_map)
    # Fallback : garder le nom original s'il n'est pas mappé
    df_appels['Agent'] = df_appels.apply(
        lambda r: r['Agent'] if pd.notna(r['Agent']) else r['Agent_appels'], axis=1
    )
 
    # == Sous-tableau 2 : Log1 (col 2 = log1_id, col 3 = clients, col 4 = ventes) ==
    df_log1 = df_raw.iloc[1:, [2, 3, 4]].copy()
    df_log1.columns = ['Log1_id', 'Clients', 'Ventes']
    df_log1 = df_log1.dropna(subset=['Log1_id'])
    df_log1['Log1_id'] = df_log1['Log1_id'].astype(str).str.strip()
    df_log1['Clients'] = pd.to_numeric(df_log1['Clients'], errors='coerce').fillna(0)
    df_log1['Ventes'] = pd.to_numeric(df_log1['Ventes'], errors='coerce').fillna(0)
    df_log1['Log1_norm'] = df_log1['Log1_id'].apply(normalize)
    df_log1['Agent'] = df_log1['Log1_norm'].map(map_log1)
    df_log1['Source'] = 'Log1'
 
    # == Sous-tableau 3 : Log2 (col 5 = log2_name, col 6 = tickets) ==
    df_log2 = df_raw.iloc[1:, [5, 6]].copy()
    df_log2.columns = ['Log2_name', 'Tickets']
    df_log2 = df_log2.dropna(subset=['Log2_name'])
    df_log2['Log2_name'] = df_log2['Log2_name'].astype(str).str.strip()
    df_log2['Tickets'] = pd.to_numeric(df_log2['Tickets'], errors='coerce').fillna(0)
    df_log2['Log2_norm'] = df_log2['Log2_name'].apply(normalize)
    df_log2['Agent'] = df_log2['Log2_norm'].map(map_log2)
    df_log2['Source'] = 'Log2'
 
    # == Sous-tableau 4 : Contacts + Heures (col 7 = log2_name, col 8 = contacts, col 9 = agent_h, col 10 = heures) ==
    df_contacts = df_raw.iloc[1:, [7, 8]].copy()
    df_contacts.columns = ['Log2_name_c', 'Contacts']
    df_contacts = df_contacts.dropna(subset=['Log2_name_c'])
    df_contacts['Log2_name_c'] = df_contacts['Log2_name_c'].astype(str).str.strip()
    df_contacts['Contacts'] = pd.to_numeric(df_contacts['Contacts'], errors='coerce').fillna(0)
    df_contacts['Log2_norm'] = df_contacts['Log2_name_c'].apply(normalize)
    df_contacts['Agent'] = df_contacts['Log2_norm'].map(map_log2)
 
    df_heures = df_raw.iloc[1:, [9, 10]].copy()
    df_heures.columns = ['Agent_h', 'Heures']
    df_heures = df_heures.dropna(subset=['Agent_h'])
    df_heures['Agent_h'] = df_heures['Agent_h'].astype(str).str.strip()
    df_heures['Heures'] = pd.to_numeric(df_heures['Heures'], errors='coerce').fillna(0)
    df_heures['Agent_h_norm'] = df_heures['Agent_h'].apply(normalize)
    df_heures['Agent'] = df_heures['Agent_h_norm'].map(agent_norm_map)
    df_heures['Agent'] = df_heures.apply(
        lambda r: r['Agent'] if pd.notna(r['Agent']) else r['Agent_h'], axis=1
    )
 
    return df_log1, df_log2, df_contacts, df_heures, df_appels, df_code
 
 
# --- Upload fichier ---
uploaded_file = st.sidebar.file_uploader(
    "📂 Charger le fichier Excel",
    type=["xlsx", "xls"],
    help="Fichier avec les feuilles 'data' et 'Code'"
)
 
if not uploaded_file:
    st.info("👈 Veuillez charger votre fichier Excel dans la barre latérale pour commencer.")
    st.stop()
 
df_log1, df_log2, df_contacts, df_heures, df_appels, df_code = load_data(uploaded_file)
 
# --- Filtre source dans sidebar ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtres")
source_options = ["Toutes les sources", "Log1", "Log2"]
source_filter = st.sidebar.selectbox("Source de données", source_options)
 
# --- Construction du tableau consolidé par agent ---
# Agréger Log1 par agent
log1_agg = df_log1.groupby('Agent', as_index=False).agg(
    Clients_Log1=('Clients', 'sum'),
    Ventes_Log1=('Ventes', 'sum')
)
 
# Agréger Log2 par agent
log2_agg = df_log2.groupby('Agent', as_index=False).agg(
    Tickets_Log2=('Tickets', 'sum')
)
 
# Contacts par agent (Log2)
contacts_agg = df_contacts.groupby('Agent', as_index=False).agg(
    Contacts=('Contacts', 'sum')
)
 
# Heures par agent
heures_agg = df_heures.groupby('Agent', as_index=False).agg(
    Heures=('Heures', 'sum')
)
 
# Appels entrants
appels_agg = df_appels.groupby('Agent', as_index=False).agg(
    Appels_entrants=('Appels_entrants', 'sum')
)
 
# Fusion sur Agent
df_final = df_code[['Agent']].copy()
df_final = df_final.merge(log1_agg, on='Agent', how='left')
df_final = df_final.merge(log2_agg, on='Agent', how='left')
df_final = df_final.merge(contacts_agg, on='Agent', how='left')
df_final = df_final.merge(heures_agg, on='Agent', how='left')
df_final = df_final.merge(appels_agg, on='Agent', how='left')
df_final = df_final.fillna(0)
 
# --- Indicateurs calculés ---
df_final['Taux_transfo_%'] = (
    df_final['Clients_Log1'] / df_final['Ventes_Log1'].replace(0, pd.NA) * 100
).round(1)
 
df_final['Ventes_par_heure'] = (
    df_final['Ventes_Log1'] / df_final['Heures'].replace(0, pd.NA)
).round(2)
 
df_final['Rendement_%'] = (
    df_final['Clients_Log1'] / df_final['Contacts'].replace(0, pd.NA) * 100
).round(1)
 
# --- Application du filtre source ---
if source_filter == "Log1":
    # Garder les agents ayant des données Log1
    df_display = df_final[df_final['Ventes_Log1'] > 0].copy()
elif source_filter == "Log2":
    # Garder les agents ayant des données Log2
    df_display = df_final[df_final['Tickets_Log2'] > 0].copy()
else:
    df_display = df_final.copy()
 
df_display = df_display.sort_values('Ventes_Log1', ascending=False)
 
# ============================================================
# AFFICHAGE
# ============================================================
 
# -- KPIs globaux --
st.subheader(f"📈 KPIs Globaux — {source_filter}")
col1, col2, col3, col4, col5 = st.columns(5)
 
total_ventes = int(df_display['Ventes_Log1'].sum())
total_clients = int(df_display['Clients_Log1'].sum())
total_tickets = int(df_display['Tickets_Log2'].sum())
total_heures = int(df_display['Heures'].sum())
nb_agents = len(df_display[df_display['Ventes_Log1'] > 0])
 
col1.metric("🏆 Ventes totales", f"{total_ventes:,}")
col2.metric("👥 Clients nets", f"{total_clients:,}")
col3.metric("🎫 Tickets Log2", f"{total_tickets:,}")
col4.metric("⏱️ Heures totales", f"{total_heures:,}")
col5.metric("👤 Agents actifs", nb_agents)
 
st.markdown("---")
 
# -- Graphiques --
col_g1, col_g2 = st.columns(2)
 
with col_g1:
    st.subheader("Ventes par agent (Log1)")
    df_chart = df_display[df_display['Ventes_Log1'] > 0].nlargest(20, 'Ventes_Log1')
    fig1 = px.bar(
        df_chart,
        x='Ventes_Log1',
        y='Agent',
        orientation='h',
        color='Ventes_Log1',
        color_continuous_scale='Blues',
        labels={'Ventes_Log1': 'Ventes', 'Agent': ''},
        text='Ventes_Log1'
    )
    fig1.update_layout(
        height=500,
        yaxis={'categoryorder': 'total ascending'},
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    fig1.update_traces(textposition='outside')
    st.plotly_chart(fig1, use_container_width=True)
 
with col_g2:
    st.subheader("Rendement par agent (%)")
    df_rend = df_display[
        (df_display['Rendement_%'].notna()) & (df_display['Rendement_%'] > 0)
    ].nlargest(20, 'Rendement_%')
    fig2 = px.bar(
        df_rend,
        x='Rendement_%',
        y='Agent',
        orientation='h',
        color='Rendement_%',
        color_continuous_scale='Greens',
        labels={'Rendement_%': 'Rendement (%)', 'Agent': ''},
        text='Rendement_%'
    )
    fig2.update_layout(
        height=500,
        yaxis={'categoryorder': 'total ascending'},
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    fig2.update_traces(textposition='outside', texttemplate='%{text:.1f}%')
    st.plotly_chart(fig2, use_container_width=True)
 
st.markdown("---")
 
# -- Tableau détaillé --
st.subheader("📋 Tableau détaillé par agent")
 
# Colonnes à afficher
cols_display = {
    'Agent': 'Agent',
    'Ventes_Log1': 'Ventes',
    'Clients_Log1': 'Clients nets',
    'Tickets_Log2': 'Tickets Log2',
    'Contacts': 'Contacts',
    'Heures': 'Heures',
    'Taux_transfo_%': 'Taux transfo (%)',
    'Ventes_par_heure': 'Ventes/heure',
    'Rendement_%': 'Rendement (%)',
    'Appels_entrants': 'Appels entrants',
}
 
df_table = df_display[list(cols_display.keys())].rename(columns=cols_display)
df_table = df_table[df_table['Ventes'] > 0].reset_index(drop=True)
 
# Mise en forme conditionnelle
st.dataframe(
    df_table.style
    .background_gradient(subset=['Ventes'], cmap='Blues')
    .background_gradient(subset=['Rendement (%)'], cmap='Greens')
    .format({
        'Taux transfo (%)': '{:.1f}%',
        'Ventes/heure': '{:.2f}',
        'Rendement (%)': '{:.1f}%',
        'Heures': '{:.0f}',
    }, na_rep='-'),
    use_container_width=True,
    height=500
)
 
st.markdown("---")
 
# -- Agents sans mapping --
unmapped_log1 = df_log1[df_log1['Agent'].isna()]['Log1_id'].unique().tolist()
unmapped_log2 = df_log2[df_log2['Agent'].isna()]['Log2_name'].unique().tolist()
 
if unmapped_log1 or unmapped_log2:
    with st.expander("⚠️ Agents non reconnus (non trouvés dans la feuille Code)"):
        if unmapped_log1:
            st.write("**Log1 IDs sans correspondance :**", unmapped_log1)
        if unmapped_log2:
            st.write("**Log2 noms sans correspondance :**", unmapped_log2)
 
st.caption("Dashboard généré automatiquement — Données issues du fichier Excel chargé")
