import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults
import edge_tts
import asyncio
import io

# --- 1. CONFIGURATION VISUELLE (MODE APP) ---
st.set_page_config(page_title="L'actu en bref", page_icon="📰", layout="centered")

# CSS POUR CACHER LES MENUS ET STYLER COMME UNE APP
st.markdown("""
    <style>
    /* Cache le menu hamburger en haut à droite */
    #MainMenu {visibility: hidden;}
    /* Cache le footer 'Made with Streamlit' */
    footer {visibility: hidden;}
    /* Cache la barre colorée en haut */
    header {visibility: hidden;}
    
    /* Style des boutons pour le mobile (Gros et ronds) */
    .stButton>button {
        height: 80px;
        width: 100%;
        border-radius: 15px;
        font-size: 24px;
        font-weight: bold;
        background-color: #f0f2f6;
        border: 1px solid #d0d4d8;
        color: #31333F;
        transition: 0.3s;
    }
    
    /* Effet au clic */
    .stButton>button:active {
        background-color: #ff4b4b;
        color: white;
        border: none;
    }

    /* Remonter le titre pour gagner de la place */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DÉFINITION DES PROFILS ---
PROFILS = {
    "🕵️‍♀️ MERIEM": """
        CONTEXTE : Tu es l'assistant personnel d'intelligence économique de Meriem.
        TON AUDITEUR : Meriem veut aller au fond des choses. Elle veut des détails, des noms, des contextes.
        TES SOURCES : Mediapart, The Intercept, Al Jazeera, ONG, Rapports indépendants.
        
        STRUCTURE (FORMAT LONG) :
        1. SALUTATION : "Bonjour Meriem. Analyse approfondie de la zone [ZONE]."
        2. LE GRAND DOSSIER (Détaillé) : Le sujet complexe du jour. Causes, conséquences.
        3. LE TOUR D'HORIZON : 3 autres actualités analysées critiquement.
        4. CONCLUSION : "C'était ton analyse Meriem. À demain."
        
        TON : Posé, intellectuel, mais fluide.
    """,
    
    "🚀 SACHA": """
        CONTEXTE : Tu es l'analyste senior de Sacha.
        TON AUDITEUR : Sacha veut un rapport de marché pour prendre des décisions.
        TES SOURCES : Bloomberg, TechCrunch, Y Combinator, Les Echos.
        
        STRUCTURE (FORMAT LONG) :
        1. SALUTATION : "Bonjour Sacha. Point marchés complet pour la zone [ZONE]."
        2. MACRO & BOURSE : Chiffres précis, taux, inflation.
        3. DEEP DIVE TECH : Une tendance (IA/Crypto) analysée en profondeur.
        4. OPPORTUNITÉS : Les signaux faibles.
        5. CONCLUSION : "Rapport terminé Sacha."
        
        TON : Très rapide, percutant, orienté data.
    """
}

# --- 3. RÉGIONS ---
REGIONS = [
    "🌍 Monde",
    "🇪🇺 Europe",
    "🇺🇸 Amériques",
    "🌍 Afrique",
    "🌏 Asie",
    "🕌 Moyen-Orient"
]

# --- 4. CONNEXION ---
try:
    api_key_google = st.secrets["GOOGLE_API_KEY"]
    api_key_tavily = st.secrets["TAVILY_API_KEY"]
    genai.configure(api_key=api_key_google)
except Exception as e:
    st.error(f"Erreur de clés : {e}")
    st.stop()

# --- 5. FONCTION AUDIO (Henri + Vitesse) ---
async def generate_audio_edge(text, profil_nom):
    voice = "fr-FR-HenriNeural" 
    if "SACHA" in profil_nom:
        rate = "+40%"
    else:
        rate = "+25%"

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    out = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            out.write(chunk["data"])
    out.seek(0)
    return out

def get_audio(text, profil_nom):
    return asyncio.run(generate_audio_edge(text, profil_nom))

# --- 6. CERVEAU ---
def ask_agent_radio(region, instructions_profil, nom_profil):
    status_container = st.empty()
    region_clean = region.split(" ")[1] if " " in region else region
    
    if "MERIEM" in nom_profil:
        keywords = "investigation corruption human rights geopolitics analysis"
    else:
        keywords = "market trends venture capital startups tech finance data"

    with status_container.status(f"📡 Analyse ({region})...", expanded=True) as s:
        try:
            search = TavilySearchResults(tavily_api_key=api_key_tavily, k=7)
            query = f"top news {region_clean} {keywords} today detailed analysis"
            results = search.invoke(query)
            context_web = f"\n[DATA] :\n{results}\n"
            s.update(label="✅ Données OK", state="complete", expanded=False)
        except:
            s.update(label="❌ Erreur web", state="error")

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        CONTEXTE : Tu es un assistant vocal masculin.
        ZONE : {region}
        PROFIL : {instructions_profil}
        DONNÉES : {context_web}
        
        CONSIGNE : Rédige un texte DENSE (600-800 mots). Style RADIO.
        """
        response = model.generate_content(prompt)
        text_script = response.text
    except Exception as e:
        return f"Erreur IA : {e}", None

    try:
        audio_bytes = get_audio(text_script, nom_profil)
        return text_script, audio_bytes
    except Exception as e:
        return text_script, None

# --- 7. INTERFACE APP ---
if "step" not in st.session_state: st.session_state.step = 1 
if "selected_profile" not in st.session_state: st.session_state.selected_profile = None
if "selected_region" not in st.session_state: st.session_state.selected_region = None
if "result_text" not in st.session_state: st.session_state.result_text = None
if "result_audio" not in st.session_state: st.session_state.result_audio = None

# Titre minimaliste
if st.session_state.step == 1:
    st.markdown("<h1 style='text-align: center;'>☀️ Morning Brief</h1>", unsafe_allow_html=True)
elif st.session_state.step == 2:
    st.markdown(f"<h1 style='text-align: center;'>Bonjour {st.session_state.selected_profile.split(' ')[1]}</h1>", unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align: center;'>🎙️ À l'écoute</h1>", unsafe_allow_html=True)

# BOUTON RETOUR (Petit et discret en haut)
if st.session_state.step > 1:
    if st.button("↩️ Menu", key="btn_ret"):
        st.session_state.step = 1
        st.session_state.result_text = None
        st.session_state.result_audio = None
        st.rerun()

# ÉTAPE 1 : PROFIL
if st.session_state.step == 1:
    keys = list(PROFILS.keys())
    # Affichage vertical pour mobile (plus ergonomique)
    for i, key in enumerate(keys):
        st.write("") # Espace
        if st.button(key, use_container_width=True, key=f"p_{i}"):
            st.session_state.selected_profile = key
            st.session_state.step = 2
            st.rerun()

# ÉTAPE 2 : RÉGION
elif st.session_state.step == 2:
    st.write("")
    cols = st.columns(2) # Grille de 2 colonnes
    for i, r in enumerate(REGIONS):
        with cols[i%2]:
            if st.button(r, use_container_width=True, key=f"r_{i}"):
                st.session_state.selected_region = r
                st.session_state.step = 3
                st.rerun()

# ÉTAPE 3 : LECTURE
elif st.session_state.step == 3:
    if st.session_state.result_text is None:
        with st.spinner("Analyse et synthèse..."):
            p_blob = PROFILS[st.session_state.selected_profile]
            r_blob = st.session_state.selected_region
            txt, aud = ask_agent_radio(r_blob, p_blob, st.session_state.selected_profile)
            st.session_state.result_text = txt
            st.session_state.result_audio = aud
            st.rerun()
            
    if st.session_state.result_audio:
        # Lecteur audio large
        st.audio(st.session_state.result_audio, format='audio/mp3', start_time=0)
        
    with st.expander("Lire le texte"):
        st.write(st.session_state.result_text)
