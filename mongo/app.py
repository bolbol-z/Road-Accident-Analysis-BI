import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from collections import Counter

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# --- CONFIGURATION MongoDB Atlas ---
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    st.error("❌ La variable d'environnement MONGODB_URI est manquante. Vérifiez votre fichier .env")
    st.stop()

# Mappages pour traduire les codes en libellés lisibles
LUM_MAP = {1: 'Plein jour', 2: 'Crépuscule', 3: 'Nuit (éclairée)', 4: 'Nuit (non éclairée)', 5: 'Nuit (mauvaise visibilité)'}
SEXE_MAP = {1: 'Homme', 2: 'Femme'}
SECU_MAP = {0: 'Sans ceinture', 1: 'Non déterminé', 2: 'Avec ceinture'}
GRAV_MAP = {1: 'Indemne', 2: 'Blessé léger', 3: 'Blessé hospitalisé', 4: 'Tué'}
CATR_MAP = {
    1: 'Autoroute / Route nationale',
    2: 'Route départementale',
    3: 'Route communale',
    4: 'Rue en agglomération',
    5: 'Hors réseau (chemin, piste, sentier…)',
    6: 'Voie ferrée',
    7: 'Parking / aire de stationnement',
    8: 'Autre / non renseigné',
    9: 'Voie privée'
}
SURF_MAP = {   -1: "Non renseigné",
     0: "Sec",
     1: "Humide",
     2: "Mouillé par pluie",
     3: "Verglas",
     4: "Neige",
     5: "Boue / terre",
     6: "Feuilles / végétation",
     7: "Gravier / sable",
     8: "Huiles / hydrocarbures",
     9: "Autre état"}
INFRA_MAP = { -1: "Non renseigné",
     0: "Sans infrastructure spécifique",
     1: "Route normale / chaussée ordinaire",
     2: "Intersection à niveau",
     3: "Rond-point / giratoire",
     4: "Passage pour piétons",
     5: "Passage à niveau ferroviaire",
     6: "Tunnel",
     7: "Pont / Viaduc",
     8: "Sortie de route / accotement",
     9: "Parking / aire de stationnement",
    10: "Autre infrastructure"}
SITU_MAP = {0: 'Aucune', 1: 'Accotement', 2: 'Bordereau', 3: 'Chaussée', 4: 'Trottoir', 5: 'Îlot/refuge', 6: 'Giratoire', 7: 'Parc stationnement'}
CIRC_MAP = {-1:'Inconue',1: 'Franchissement', 2: 'Débordement/Collision latérale', 3: 'Renversement', 4: 'Collision frontale', 5: 'Collision arrière', 9: 'Autre'}
MANV_MAP = {1: 'Tournant à gauche', 2: 'Tournant à droite', 15: 'Autre', 16: 'Autre (2)'}
# Catégories véhicules - Nomenclature complète
CATV_MAP = {
    1:  "Bicyclette",
2:  "Cyclomoteur (< 50 cm³)",
3:  "Motocyclette (> 50 cm³)",
4:  "Motocyclette avec side-car",
5:  "Tricycle à moteur",
6:  "Quadricycle à moteur",
7:  "Voiture particulière",
8:  "Véhicule utilitaire léger (≤ 3,5 t)",
9:  "Camion",
10: "Tracteur routier (semi-remorque)",
11: "Autobus",
12: "Autocar",
13: "Tramway",
14: "Engin spécial",
15: "Tracteur agricole",
16: "Remorque",
17: "Engin de déplacement personnel motorisé (EDPm)",
18: "Engin de déplacement personnel non motorisé (EDPnm)",
19: "Autre véhicule",
20: "Non renseigné / Indéterminé"

}
TRAJET_MAP = {
    0: 'Non renseigné',
    1: 'Domicile → Travail / Études',
    2: 'Travail / Études → Domicile',
    3: 'Trajet professionnel',
    4: 'Trajet scolaire',
    5: 'Trajet courses / achats',
    6: 'Trajet loisirs / sport',
    7: 'Trajet vacances / voyage',
    8: 'Trajet utilitaire / mission',
    9: 'Autre trajet'
}

# Mapping des codes département vers noms réels (France)
DEP_MAP = {
    1: 'Ain', 2: 'Aisne', 3: 'Allier', 4: 'Alpes-de-Haute-Provence', 5: 'Alpes (Hautes-)',
    6: 'Alpes-Maritimes', 7: 'Ardèche', 8: 'Ardennes', 9: 'Ariège', 10: 'Aube',
    11: 'Aude', 12: 'Aveyron', 13: 'Bouches-du-Rhône', 14: 'Calvados', 15: 'Cantal',
    16: 'Charente', 17: 'Charente-Maritime', 18: 'Cher', 19: 'Corrèze', 21: 'Côte-d\'Or',
    22: 'Côtes-d\'Armor', 23: 'Creuse', 24: 'Dordogne', 25: 'Doubs', 26: 'Drôme',
    27: 'Eure', 28: 'Eure-et-Loir', 29: 'Finistère', 2: 'Corse-du-Sud', 2: 'Haute-Corse',
    31: 'Garonne (Haute-)', 32: 'Gers', 33: 'Gironde', 34: 'Hérault', 35: 'Ille-et-Vilaine',
    36: 'Indre', 37: 'Indre-et-Loire', 38: 'Isère', 39: 'Jura', 40: 'Landes',
    41: 'Loir-et-Cher', 42: 'Loire', 43: 'Loire (Haute-)', 44: 'Loire-Atlantique', 45: 'Loiret',
    46: 'Lot', 47: 'Lot-et-Garonne', 48: 'Lozère', 49: 'Maine-et-Loire', 50: 'Manche',
    51: 'Marne', 52: 'Marne (Haute-)', 53: 'Mayenne', 54: 'Meurthe-et-Moselle', 55: 'Meuse',
    56: 'Morbihan', 57: 'Moselle', 58: 'Nièvre', 59: 'Nord', 60: 'Oise',
    61: 'Orne', 62: 'Pas-de-Calais', 63: 'Puy-de-Dôme', 64: 'Pyrénées-Atlantiques', 65: 'Pyrénées (Hautes-)',
    66: 'Pyrénées-Orientales', 67: 'Rhin (Bas-)', 68: 'Rhin (Haut-)', 69: 'Rhône', 70: 'Saône (Haute-)',
    71: 'Saône-et-Loire', 72: 'Sarthe', 73: 'Savoie', 74: 'Savoie (Haute-)', 75: 'Seine',
    76: 'Seine-Maritime', 77: 'Seine-et-Marne', 78: 'Yvelines', 79: 'Sèvres (Deux-)',
    80: 'Somme', 81: 'Tarn', 82: 'Tarn-et-Garonne', 83: 'Var', 84: 'Vaucluse',
    85: 'Vendée', 86: 'Vienne', 87: 'Vienne (Haute-)', 88: 'Vosges', 89: 'Yonne',
    90: 'Territoire-de-Belfort', 91: 'Essonne', 92: 'Hauts-de-Seine', 93: 'Seine-Saint-Denis',
    94: 'Val-de-Marne', 95: 'Val-d\'Oise',
    971: 'Guadeloupe', 972: 'Martinique', 973: 'Guyane', 974: 'Réunion', 976: 'Mayotte'
}

# Configuration Streamlit
st.set_page_config(
    page_title="Dashboard Accidents Corporels",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling CSS personnalisé
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #FF6B6B;
    }
    .header-title {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURATION MongoDB ---
@st.cache_resource
def get_mongo_connection():
    """Établit la connexion à MongoDB Atlas"""
    try:
        client = MongoClient(
            MONGODB_URI,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=10000
        )
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"❌ Erreur de connexion MongoDB: {e}")
        return None

@st.cache_data(ttl=300)
def load_data_from_mongo():
    """Charge les données depuis MongoDB Atlas"""
    try:
        client = MongoClient(
            MONGODB_URI,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=10000
        )
        client.admin.command('ping')
        
        db = client["db_accidents_corporels"]
        collection = db["accidents"]
        
        # Récupérer tous les documents
        documents = list(collection.find())
        
        return documents
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {e}")
        return None
    finally:
        try:
            client.close()
        except:
            pass

# --- FONCTIONS DE TRAITEMENT DES DONNÉES ---
def process_documents(documents):
    """Traite les documents MongoDB pour créer des DataFrames utiles"""
    
    # Données principales des accidents
    accidents_data = []
    for doc in documents:
        accident = {
            '_id': doc.get('_id'),
            'jour': doc.get('jour'),
            'mois': doc.get('mois'),
            'an': doc.get('an'),
            'hrmn': doc.get('hrmn'),
            'lat': doc.get('lat'),
            'long': doc.get('long'),
            'lum': doc.get('lum'),
            'dep': doc.get('dep'),
            'agg': doc.get('agg'),
            'atm': doc.get('atm'),
            'col': doc.get('col'),
        }
        accidents_data.append(accident)
    
    df_accidents = pd.DataFrame(accidents_data)
    
    # Extraction données véhicules
    vehicules_data = []
    for doc in documents:
        vehicules_list = doc.get('vehicules', [])
        if isinstance(vehicules_list, list):
            for veh in vehicules_list:
                v = {
                    '_id': doc.get('_id'),
                    'id_vehicule': veh.get('id_vehicule'),
                    'catv': veh.get('catv'),
                    'senc': veh.get('senc'),
                    'motor': veh.get('motor'),
                    'manv': veh.get('manv'),
                }
                vehicules_data.append(v)
    
    df_vehicules = pd.DataFrame(vehicules_data) if vehicules_data else pd.DataFrame()
    
    # Extraction données usagers
    usagers_data = []
    for doc in documents:
        vehicules_list = doc.get('vehicules', [])
        if isinstance(vehicules_list, list):
            for veh in vehicules_list:
                usagers_list = veh.get('usagers', [])
                if isinstance(usagers_list, list):
                    for usager in usagers_list:
                        u = {
                            '_id': doc.get('_id'),
                            'id_usager': usager.get('id_usager'),
                            'id_vehicule': veh.get('id_vehicule'),
                            'sexe': usager.get('sexe'),
                            'trajet': usager.get('trajet'),
                            'secu1': usager.get('secu1'),
                            'age': usager.get('age'),
                            'grav': usager.get('grav'),
                            'catu': usager.get('catu'),
                        }
                        usagers_data.append(u)
    
    df_usagers = pd.DataFrame(usagers_data) if usagers_data else pd.DataFrame()
    
    # Extraction données lieux
    lieux_data = []
    for doc in documents:
        lieux_list = doc.get('lieux', [])
        if isinstance(lieux_list, list):
            for lieu in lieux_list:
                l = {
                    '_id': doc.get('_id'),
                    'catr': lieu.get('catr'),
                    'circ': lieu.get('circ'),
                    'surf': lieu.get('surf'),
                    'infra': lieu.get('infra'),
                    'voie': lieu.get('voie'),
                    'nbv': lieu.get('nbv'),
                    'plan': lieu.get('plan'),
                }
                lieux_data.append(l)
    
    df_lieux = pd.DataFrame(lieux_data) if lieux_data else pd.DataFrame()
    
    return df_accidents, df_vehicules, df_usagers, df_lieux

# --- CHARGEMENT DES DONNÉES ---
documents = load_data_from_mongo()

if documents:
    df_accidents, df_vehicules, df_usagers, df_lieux = process_documents(documents)
    # --- Traduction des codes en libellés lisibles ---
    # Accidents
    if not df_accidents.empty:
        if 'lum' in df_accidents.columns:
            df_accidents['lum_label'] = pd.to_numeric(df_accidents['lum'], errors='coerce').map(LUM_MAP)
            df_accidents['lum_label'] = df_accidents['lum_label'].fillna(df_accidents['lum'].astype(str))
        # type de collision
        if 'col' in df_accidents.columns:
            COL_MAP = {1: 'Deux véhicules', 2: 'Plusieurs véhicules', 3: 'Mono', 4: 'Moto', 5: 'Autres', 6: 'Piéton', 7: 'Animal', 8: 'Objet'}
            df_accidents['col_label'] = pd.to_numeric(df_accidents['col'], errors='coerce').map(COL_MAP).fillna(df_accidents['col'].astype(str))
        
        # Département avec nom réel
        if 'dep' in df_accidents.columns:
            def format_dep(x):
                if pd.isna(x):
                    return ''
                try:
                    dep_int = int(float(x)) if isinstance(x, (float, str)) else int(x)
                    dep_name = DEP_MAP.get(dep_int, str(dep_int))
                    return f"{dep_int}: {dep_name}"
                except (ValueError, TypeError):
                    return str(x)
            df_accidents['dep_label'] = df_accidents['dep'].apply(format_dep)

    # Véhicules
    if not df_vehicules.empty:
        if 'catv' in df_vehicules.columns:
            df_vehicules['catv_label'] = pd.to_numeric(df_vehicules['catv'], errors='coerce').map(CATV_MAP).fillna(df_vehicules['catv'].astype(str))
        if 'manv' in df_vehicules.columns:
            df_vehicules['manv_label'] = pd.to_numeric(df_vehicules['manv'], errors='coerce').map(MANV_MAP).fillna(df_vehicules['manv'].astype(str))

    # Usagers
    if not df_usagers.empty:
        if 'sexe' in df_usagers.columns:
            df_usagers['sexe_label'] = pd.to_numeric(df_usagers['sexe'], errors='coerce').map(SEXE_MAP).fillna(df_usagers['sexe'].astype(str))
        if 'secu1' in df_usagers.columns:
            df_usagers['secu_label'] = pd.to_numeric(df_usagers['secu1'], errors='coerce').map(SECU_MAP).fillna(df_usagers['secu1'].astype(str))
        if 'trajet' in df_usagers.columns:
            df_usagers['trajet_label'] = pd.to_numeric(df_usagers['trajet'], errors='coerce').map(TRAJET_MAP).fillna(df_usagers['trajet'].astype(str))
        if 'grav' in df_usagers.columns:
            df_usagers['grav_label'] = pd.to_numeric(df_usagers['grav'], errors='coerce').map(GRAV_MAP).fillna(df_usagers['grav'].astype(str))

    # Lieux
    if not df_lieux.empty:
        if 'circ' in df_lieux.columns:
            df_lieux['circ_label'] = pd.to_numeric(df_lieux['circ'], errors='coerce').map(CIRC_MAP).fillna(df_lieux['circ'].astype(str))
        if 'surf' in df_lieux.columns:
            df_lieux['surf_label'] = pd.to_numeric(df_lieux['surf'], errors='coerce').map(SURF_MAP).fillna(df_lieux['surf'].astype(str))
        if 'infra' in df_lieux.columns:
            df_lieux['infra_label'] = pd.to_numeric(df_lieux['infra'], errors='coerce').map(INFRA_MAP).fillna(df_lieux['infra'].astype(str))
        if 'situ' in df_lieux.columns:
            df_lieux['situ_label'] = pd.to_numeric(df_lieux['situ'], errors='coerce').map(SITU_MAP).fillna(df_lieux['situ'].astype(str))
        if 'catr' in df_lieux.columns:
            df_lieux['catr_label'] = pd.to_numeric(df_lieux['catr'], errors='coerce').map(CATR_MAP).fillna(df_lieux['catr'].astype(str))
    
    # Création de la navigation multi-page
    pages = {
        "📊 Vue d'Ensemble": "overview",
        "🗺️ Analyse Géographique": "geographic",
        "📈 Analyse Détaillée": "detailed"
    }
    
    selected_page = st.sidebar.radio("Navigation", pages.keys())
    
    # --- PAGE 1: VUE D'ENSEMBLE ---
    if pages[selected_page] == "overview":
        st.markdown("<h1 class='header-title'>📊 Dashboard Accidents Corporels - Vue d'Ensemble</h1>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📍 Total Accidents", len(df_accidents), delta=None)
        
        with col2:
            total_usagers = len(df_usagers)
            st.metric("👥 Usagers Impliqués", int(total_usagers), delta=None)
        
        with col3:
            total_vehicules = len(df_vehicules)
            st.metric("🚗 Véhicules Impliqués", int(total_vehicules), delta=None)
        
        with col4:
            if 'grav' in df_usagers.columns:
                nb_grave_usagers = (df_usagers['grav'] == 1).sum()
            else:
                nb_grave_usagers = len(df_accidents[df_accidents['col'] > 0])
            st.metric("⚠️ Cas Graves", int(nb_grave_usagers), delta=None)
        
        st.divider()
        
        # Répartition par type de collision
        col1, col2 = st.columns(2)
        
        with col1:
            if 'col' in df_accidents.columns:
                col_map = {
    1: "Collision frontale (2 véhicules)",
    2: "Collision par l’arrière (2 véhicules)",
    3: "Collision par le côté – même sens (2 véhicules)",
    4: "Collision par le côté – sens opposé (2 véhicules)",
    5: "Collision impliquant plus de deux véhicules",
    6: "Autre collision",
    7: "Sans collision",
    8: "Collision avec piéton"
}
                df_accidents['col_label'] = df_accidents['col'].map(col_map)
                col_counts = df_accidents['col_label'].value_counts()
                fig_col = px.pie(
                    values=col_counts.values,
                    names=col_counts.index,
                    title="Type de Collision",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_col, use_container_width=True)
        
        with col2:
            # Accidents par mois
            if 'jour' in df_accidents.columns and 'mois' in df_accidents.columns and 'an' in df_accidents.columns:
                df_accidents_copy = df_accidents.copy()
                try:
                    df_accidents_copy['date'] = pd.to_datetime(
                        df_accidents_copy[['an', 'mois', 'jour']].rename(
                            columns={'an': 'year', 'mois': 'month', 'jour': 'day'}
                        ), errors='coerce'
                    )
                    accidents_par_mois = df_accidents_copy.groupby(df_accidents_copy['date'].dt.to_period('M')).size()
                    
                    df_mois = pd.DataFrame({
                        'Mois': accidents_par_mois.index.astype(str),
                        'Nombre': accidents_par_mois.values
                    })
                    
                    fig_mois = px.bar(
                        df_mois,
                        x='Mois',
                        y='Nombre',
                        title="Accidents par Mois",
                        color_discrete_sequence=['#636EFA']
                    )
                    fig_mois.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_mois, use_container_width=True)
                except:
                    st.info("Pas assez de données pour les accidents par mois")
        
        st.divider()
        
        # Distribution par luminosité
        if 'lum' in df_accidents.columns:
            lum_map = {1: 'Plein jour', 2: 'Crépuscule', 3: 'Nuit', 4: 'Nuit', 5: 'Nuit'}
            df_accidents['lum_label'] = df_accidents['lum'].map(lum_map)
            lum_counts = df_accidents['lum_label'].value_counts()
            
            df_lum = pd.DataFrame({'Luminosité': lum_counts.index, 'Nombre': lum_counts.values})
            fig_lum = px.bar(
                df_lum,
                x='Luminosité',
                y='Nombre',
                title="Distribution des Accidents par Luminosité",
                color_discrete_sequence=['#EF553B']
            )
            st.plotly_chart(fig_lum, use_container_width=True)
        
        st.divider()
        
        # Catégories de véhicules et sexe usagers
        if not df_vehicules.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                if 'catv' in df_vehicules.columns:
                    catv_col = 'catv_label' if 'catv_label' in df_vehicules.columns else 'catv'
                    catv_counts = df_vehicules[catv_col].value_counts().head(10)
                    df_catv = pd.DataFrame({'Catégorie': catv_counts.index, 'Nombre': catv_counts.values})
                    fig_catv = px.treemap(
                        df_catv,
                        path=['Catégorie'],
                        values='Nombre',
                        title="Top 10 Catégories de Véhicules",
                        color='Nombre',
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig_catv, use_container_width=True)
            
            with col2:
                if 'sexe' in df_usagers.columns and not df_usagers.empty:
                    if 'sexe_label' not in df_usagers.columns:
                        df_usagers['sexe_label'] = pd.to_numeric(df_usagers['sexe'], errors='coerce').map(SEXE_MAP).fillna(df_usagers['sexe'].astype(str))
                    sexe_counts = df_usagers['sexe_label'].value_counts()
                    fig_sexe = px.pie(
                        values=sexe_counts.values,
                        names=sexe_counts.index,
                        title="Répartition par Sexe des Usagers",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_sexe, use_container_width=True)
    
    # --- PAGE 2: ANALYSE GÉOGRAPHIQUE ---
    elif pages[selected_page] == "geographic":
        st.markdown("<h1 class='header-title'>🗺️ Analyse Géographique</h1>", unsafe_allow_html=True)
        
        # Filtre par département
        col_filter1, col_filter2 = st.columns([3, 1])
        with col_filter1:
            if 'dep_label' in df_accidents.columns:
                dep_options = ['Tous'] + sorted(df_accidents['dep_label'].dropna().unique().tolist())
                selected_dep_label = st.selectbox("🏘️ Choisir Département", dep_options, key='dept_filter')
                
                # Filtrer les données par département si sélectionné
                if selected_dep_label != 'Tous':
                    df_accidents_filtered = df_accidents[df_accidents['dep_label'] == selected_dep_label].copy()
                    df_lieux_filtered = df_lieux[df_lieux.index.isin(df_accidents_filtered.index)].copy() if not df_accidents_filtered.empty else df_lieux.iloc[0:0]
                else:
                    df_accidents_filtered = df_accidents.copy()
                    df_lieux_filtered = df_lieux.copy()
            else:
                df_accidents_filtered = df_accidents.copy()
                df_lieux_filtered = df_lieux.copy()
        
        # Carte interactive
        if 'lat' in df_accidents_filtered.columns and 'long' in df_accidents_filtered.columns:
            df_map = df_accidents_filtered.dropna(subset=['lat', 'long'])
            if not df_map.empty:
                df_map['col_label'] = df_map['col'].apply(lambda x: 'Collision' if x >= 1 else 'Pas collision')
                fig_map = px.scatter_mapbox(
                    df_map,
                    lat='lat',
                    lon='long',
                    color='col_label',
                    hover_name='_id',
                    hover_data={'lat': ':.4f', 'long': ':.4f'},
                    title="Localisation Géographique des Accidents",
                    zoom=5,
                    color_discrete_map={'Collision': '#FF0000', 'Pas collision': '#00CC96'},
                    mapbox_style="open-street-map"
                )
                st.plotly_chart(fig_map, use_container_width=True)
        
        st.divider()
        
        # Statistiques par circonstances
        col1, col2 = st.columns(2)
        
        with col1:
            if not df_lieux_filtered.empty and 'circ' in df_lieux_filtered.columns:
                circ_col = 'circ_label' if 'circ_label' in df_lieux_filtered.columns else 'circ'
                circ_counts = df_lieux_filtered[circ_col].value_counts().head(10)
                df_circ = pd.DataFrame({'Circonstance': circ_counts.index, 'Nombre': circ_counts.values})
                fig_circ = px.bar(
                    df_circ,
                    x='Nombre',
                    y='Circonstance',
                    title="Top 10 Circonstances",
                    color_discrete_sequence=['#AB63FA'],
                    orientation='h'
                )
                st.plotly_chart(fig_circ, use_container_width=True)
        
        st.divider()
        
        # Surface de la route
        col1, col2 = st.columns(2)
        
        with col1:
            if not df_lieux_filtered.empty and 'catr' in df_lieux_filtered.columns:
                catr_col = 'catr_label' if 'catr_label' in df_lieux_filtered.columns else 'catr'
                catr_counts = df_lieux_filtered[catr_col].value_counts()
                df_catr = pd.DataFrame({'Catégorie': catr_counts.index, 'Nombre': catr_counts.values})
                fig_catr = px.pie(
                    df_catr,
                    values='Nombre',
                    names='Catégorie',
                    title="Catégorie des Routes",
                    color_discrete_sequence=px.colors.qualitative.Light24,
                    labels={'Catégorie': 'Catégorie', 'Nombre': 'Nombre'}
                )
                st.plotly_chart(fig_catr, use_container_width=True)
        
        with col2:
            if not df_lieux_filtered.empty and 'infra' in df_lieux_filtered.columns:
                infra_col = 'infra_label' if 'infra_label' in df_lieux_filtered.columns else 'infra'
                # If situ exists, show combined sunburst, otherwise fallback to pie
                if 'situ' in df_lieux_filtered.columns:
                    situ_col = 'situ_label' if 'situ_label' in df_lieux_filtered.columns else 'situ'
                    # Créer combinaison infra + situ
                    df_infra_situ = df_lieux_filtered.groupby([infra_col, situ_col]).size().reset_index(name='Nombre')
                    df_infra_situ['Combined'] = df_infra_situ[infra_col].astype(str) + ' - ' + df_infra_situ[situ_col].astype(str)
                    fig_infra = px.sunburst(
                        df_infra_situ,
                        ids='Combined',
                        labels='Combined',
                        parents=df_infra_situ[infra_col],
                        values='Nombre',
                        title="Infrastructure et Situation",
                        color='Nombre',
                        color_continuous_scale='Viridis'
                    )
                else:
                    infra_counts = df_lieux_filtered[infra_col].value_counts()
                    df_infra = pd.DataFrame({'Type': infra_counts.index, 'Nombre': infra_counts.values})
                    fig_infra = px.pie(
                        df_infra,
                        values='Nombre',
                        names='Type',
                        title="Infrastructure",
                        color_discrete_sequence=px.colors.qualitative.Light24,
                        labels={'Type': 'Type d\'infrastructure', 'Nombre': 'Nombre'}
                    )
                st.plotly_chart(fig_infra, use_container_width=True)
    
    # --- PAGE 3: ANALYSE DÉTAILLÉE ---
    elif pages[selected_page] == "detailed":
        st.markdown("<h1 class='header-title'>📈 Analyse Détaillée</h1>", unsafe_allow_html=True)
        
        # Sélection du type d'analyse
        analyse_type = st.radio(
            "Sélectionnez le type d'analyse",
            ["Usagers", "Véhicules", "Lieux", "Données Brutes"],
            horizontal=True
        )
        
        if analyse_type == "Usagers":
            st.subheader("👥 Analyse des Usagers")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Usagers", len(df_usagers))
            
            with col2:
                if 'secu1' in df_usagers.columns:
                    secu_ok = (df_usagers['secu1'] == 2).sum()
                    st.metric("Avec Ceinture de Sécurité", secu_ok)
            
            with col3:
                if 'age' in df_usagers.columns:
                    age_mean = pd.to_numeric(df_usagers['age'], errors='coerce').mean()
                    if pd.isna(age_mean):
                        st.metric("Âge Moyen", "N/A")
                    else:
                        st.metric("Âge Moyen", f"{age_mean:.1f} ans")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'secu1' in df_usagers.columns and not df_usagers.empty:
                    secu_map = {0: 'Sans ceinture', 1: 'Non déterminé', 2: 'Avec ceinture'}
                    df_usagers['secu_label'] = df_usagers['secu1'].map(secu_map)
                    secu_counts = df_usagers['secu_label'].value_counts()
                    fig_secu = px.pie(
                        values=secu_counts.values,
                        names=secu_counts.index,
                        title="Ceinture de Sécurité",
                        color_discrete_sequence=['#FF6B6B', '#FFD700', '#00CC96']
                    )
                    st.plotly_chart(fig_secu, use_container_width=True)
            
            with col2:
                if 'trajet' in df_usagers.columns:
                    trajet_counts = df_usagers['trajet'].value_counts()
                    fig_trajet = px.bar(
                        x=trajet_counts.index,
                        y=trajet_counts.values,
                        title="Type de Trajet",
                        labels={'x': 'Type', 'y': 'Nombre'},
                        color_discrete_sequence=['#636EFA']
                    )
                    st.plotly_chart(fig_trajet, use_container_width=True)
            
            st.divider()
            
            # Distribution d'âge
            if 'age' in df_usagers.columns:
                age_numeric = pd.to_numeric(df_usagers['age'], errors='coerce')
                age_numeric = age_numeric.dropna()
                
                fig_age = px.histogram(
                    x=age_numeric,
                    nbins=30,
                    title="Distribution d'Âge des Usagers",
                    labels={'x': 'Âge (ans)', 'y': 'Nombre d\'usagers'},
                    color_discrete_sequence=['#AB63FA']
                )
                st.plotly_chart(fig_age, use_container_width=True)
        
        elif analyse_type == "Véhicules":
            st.subheader("🚗 Analyse des Véhicules")
            
            st.metric("Total Véhicules", len(df_vehicules))
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'catv' in df_vehicules.columns and not df_vehicules.empty:
                    catv_col = 'catv_label' if 'catv_label' in df_vehicules.columns else 'catv'
                    catv_counts = df_vehicules[catv_col].value_counts().head(15)
                    df_catv_detail = pd.DataFrame({'Catégorie': catv_counts.index, 'Nombre': catv_counts.values})
                    chart_type_detail = st.selectbox("Type d'affichage (Détail)", ['Barre horizontale', 'Camembert', 'Treemap'], key='catv_display_detail')
                    if chart_type_detail == 'Barre horizontale':
                        fig_catv = px.bar(
                            df_catv_detail,
                            x='Nombre',
                            y='Catégorie',
                            title="Top 15 Catégories de Véhicules",
                            color_discrete_sequence=['#FFA15A'],
                            orientation='h'
                        )
                    elif chart_type_detail == 'Camembert':
                        fig_catv = px.pie(
                            df_catv_detail,
                            values='Nombre',
                            names='Catégorie',
                            title="Top 15 Catégories de Véhicules",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                    else:
                        fig_catv = px.treemap(
                            df_catv_detail,
                            path=['Catégorie'],
                            values='Nombre',
                            title="Top 15 Catégories de Véhicules",
                            color='Nombre',
                            color_continuous_scale='Viridis'
                        )
                    st.plotly_chart(fig_catv, use_container_width=True)
            
            with col2:
                if 'type_veh' in df_vehicules.columns:
                    type_counts = df_vehicules['type_veh'].value_counts().head(10)
                    fig_type = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        title="Top 10 Types de Véhicules",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_type, use_container_width=True)
            
            st.divider()
            
            # Type de manœuvre
            if 'manv' in df_vehicules.columns and not df_vehicules.empty:
                manv_counts = df_vehicules['manv'].value_counts().head(15)
                df_manv = pd.DataFrame({'Manœuvre': manv_counts.index, 'Nombre': manv_counts.values})
                fig_manv = px.bar(
                    df_manv,
                    x='Manœuvre',
                    y='Nombre',
                    title="Top 15 Manœuvres des Véhicules",
                    color_discrete_sequence=['#00CC96']
                )
                fig_manv.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_manv, use_container_width=True)
        
        elif analyse_type == "Lieux":
            st.subheader("📍 Analyse des Lieux")
            
            st.metric("Total Lieux Enregistrés", len(df_lieux))
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'catr' in df_lieux.columns:
                    catr_col = 'catr_label' if 'catr_label' in df_lieux.columns else 'catr'
                    catr_counts = df_lieux[catr_col].value_counts()
                    df_catr_detail = pd.DataFrame({'Catégorie': catr_counts.index, 'Nombre': catr_counts.values})
                    fig_catr = px.bar(
                        df_catr_detail,
                        x='Catégorie',
                        y='Nombre',
                        title="Catégorie des Routes",
                        color_discrete_sequence=['#EF553B'],
                        labels={'Catégorie': 'Catégorie', 'Nombre': 'Nombre'}
                    )
                    st.plotly_chart(fig_catr, use_container_width=True)
            
            with col2:
                if 'circ' in df_lieux.columns:
                    circ_col = 'circ_label' if 'circ_label' in df_lieux.columns else 'circ'
                    circ_counts = df_lieux[circ_col].value_counts().head(10)
                    df_circ_detail = pd.DataFrame({'Circonstance': circ_counts.index, 'Nombre': circ_counts.values})
                    fig_circ = px.bar(
                        df_circ_detail,
                        x='Nombre',
                        y='Circonstance',
                        title="Top 10 Circonstances",
                        color_discrete_sequence=['#00CC96'],
                        orientation='h'
                    )
                    st.plotly_chart(fig_circ, use_container_width=True)
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'surf' in df_lieux.columns:
                    surf_col = 'surf_label' if 'surf_label' in df_lieux.columns else 'surf'
                    surf_counts = df_lieux[surf_col].value_counts()
                    df_surf_pie = pd.DataFrame({'État': surf_counts.index, 'Nombre': surf_counts.values})
                    fig_surf = px.pie(
                        df_surf_pie,
                        values='Nombre',
                        names='État',
                        title="État de la Surface",
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        labels={'État': 'État de la surface', 'Nombre': 'Nombre'}
                    )
                    st.plotly_chart(fig_surf, use_container_width=True)
            
            with col2:
                if 'infra' in df_lieux.columns:
                    infra_col = 'infra_label' if 'infra_label' in df_lieux.columns else 'infra'
                    infra_counts = df_lieux[infra_col].value_counts()
                    df_infra_pie = pd.DataFrame({'Type': infra_counts.index, 'Nombre': infra_counts.values})
                    fig_infra = px.pie(
                        df_infra_pie,
                        values='Nombre',
                        names='Type',
                        title="Infrastructure",
                        color_discrete_sequence=px.colors.qualitative.Light24,
                        labels={'Type': 'Type d\'infrastructure', 'Nombre': 'Nombre'}
                    )
                    st.plotly_chart(fig_infra, use_container_width=True)
        
        elif analyse_type == "Données Brutes":
            st.subheader("📋 Données Brutes")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Accidents", "Véhicules", "Usagers", "Lieux"])
            
            with tab1:
                st.write(f"Total: {len(df_accidents)} accidents")
                # Afficher avec les labels si disponibles
                df_accidents_display = df_accidents.copy()
                if 'lum_label' in df_accidents_display.columns:
                    df_accidents_display = df_accidents_display.drop(columns=['lum'], errors='ignore')
                    df_accidents_display = df_accidents_display.rename(columns={'lum_label': 'Lumière'})
                if 'col_label' in df_accidents_display.columns:
                    df_accidents_display = df_accidents_display.drop(columns=['col'], errors='ignore')
                    df_accidents_display = df_accidents_display.rename(columns={'col_label': 'Type Collision'})
                if 'dep_label' in df_accidents_display.columns:
                    df_accidents_display = df_accidents_display.drop(columns=['dep'], errors='ignore')
                    df_accidents_display = df_accidents_display.rename(columns={'dep_label': 'Département'})
                st.dataframe(df_accidents_display.head(100), use_container_width=True)
            
            with tab2:
                st.write(f"Total: {len(df_vehicules)} véhicules")
                # Afficher avec les labels de catégorie si disponibles
                df_vehicules_display = df_vehicules.copy()
                if 'catv_label' in df_vehicules_display.columns:
                    df_vehicules_display = df_vehicules_display.drop(columns=['catv'], errors='ignore')
                    df_vehicules_display = df_vehicules_display.rename(columns={'catv_label': 'Catégorie Véhicule'})
                if 'manv_label' in df_vehicules_display.columns:
                    df_vehicules_display = df_vehicules_display.drop(columns=['manv'], errors='ignore')
                    df_vehicules_display = df_vehicules_display.rename(columns={'manv_label': 'Manœuvre'})
                st.dataframe(df_vehicules_display.head(100), use_container_width=True)
            
            with tab3:
                st.write(f"Total: {len(df_usagers)} usagers")
                # Afficher avec les labels si disponibles
                df_usagers_display = df_usagers.copy()
                if 'sexe_label' in df_usagers_display.columns:
                    df_usagers_display = df_usagers_display.drop(columns=['sexe'], errors='ignore')
                    df_usagers_display = df_usagers_display.rename(columns={'sexe_label': 'Sexe'})
                if 'secu_label' in df_usagers_display.columns:
                    df_usagers_display = df_usagers_display.drop(columns=['secu1'], errors='ignore')
                    df_usagers_display = df_usagers_display.rename(columns={'secu_label': 'Sécurité'})
                if 'grav_label' in df_usagers_display.columns:
                    df_usagers_display = df_usagers_display.drop(columns=['grav'], errors='ignore')
                    df_usagers_display = df_usagers_display.rename(columns={'grav_label': 'Gravité'})
                if 'trajet_label' in df_usagers_display.columns:
                    df_usagers_display = df_usagers_display.drop(columns=['trajet'], errors='ignore')
                    df_usagers_display = df_usagers_display.rename(columns={'trajet_label': 'Trajet'})
                st.dataframe(df_usagers_display.head(100), use_container_width=True)
            
            with tab4:
                st.write(f"Total: {len(df_lieux)} lieux")
                # Afficher avec les labels si disponibles
                df_lieux_display = df_lieux.copy()
                if 'catr_label' in df_lieux_display.columns:
                    df_lieux_display = df_lieux_display.drop(columns=['catr'], errors='ignore')
                    df_lieux_display = df_lieux_display.rename(columns={'catr_label': 'Catégorie Route'})
                if 'circ_label' in df_lieux_display.columns:
                    df_lieux_display = df_lieux_display.drop(columns=['circ'], errors='ignore')
                    df_lieux_display = df_lieux_display.rename(columns={'circ_label': 'Circonstance'})
                if 'surf_label' in df_lieux_display.columns:
                    df_lieux_display = df_lieux_display.drop(columns=['surf'], errors='ignore')
                    df_lieux_display = df_lieux_display.rename(columns={'surf_label': 'Surface'})
                if 'infra_label' in df_lieux_display.columns:
                    df_lieux_display = df_lieux_display.drop(columns=['infra'], errors='ignore')
                    df_lieux_display = df_lieux_display.rename(columns={'infra_label': 'Infrastructure'})
                st.dataframe(df_lieux_display.head(100), use_container_width=True)

else:
    st.error("❌ Impossible de charger les données de MongoDB. Vérifiez que MongoDB est en cours d'exécution.")
