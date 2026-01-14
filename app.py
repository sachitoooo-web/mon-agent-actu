import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults
import edge_tts
import asyncio
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Assistant Actu Pro", page_icon="🎙️")

# --- 2. DÉFINITION DES PROFILS ---
PROFILS = {
    "🕵️‍♀️ MERIEM (Investigation)": """
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
    
    "🚀 SACHA (Business/VC)": """
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
    "🌍 Monde Entier",
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

# --- 5. FONCTION GÉNÉRATION AUDIO (VOIX HOMME UNIQUE) ---
async def generate_audio_edge(text, profil_nom):
    # VOIX D'HOMME POUR TOUT LE MONDE (Henri)
    voice = "fr-FR-HenriNeural" 
    
    # ON GARDE LA VITESSE COMME MARQUEUR DE PERSONNALITÉ
    if "SACHA" in profil_nom:
        rate = "+20%"  # Sacha = Très rapide
    else:
        rate = "+20%"  # Meriem = Rapide (mais moins que Sacha)

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    
    out = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            out.write(chunk["data"])
    
    out.seek(0)
    return out

# Wrapper pour exécuter l'async dans Streamlit
def get_audio(text, profil_nom):
    return asyncio.run(generate_audio_edge(text, profil_nom))

# --- 6. FONCTION CERVEAU ---
def ask_agent_radio(region, instructions_profil, nom_profil):
    # A. Recherche Web
    status_container = st.empty()
    region_clean = region.split(" ")[1] if " " in region else region
    
    if "MERIEM" in nom_profil:
        keywords = "investigation corruption human rights geopolitics analysis"
    else:
        keywords = "market trends venture capital startups tech finance data"

    with status_container.status(f"📡 Analyse pour {nom_profil.split(' ')[1]} ({region})...", expanded=True) as s:
        try:
            search = TavilySearchResults(tavily_api_key=api_key_tavily, k=7)
            query = f"top news {region_clean} {keywords} today detailed analysis"
            results = search.invoke(query)
            context_web = f"\n[DATA] :\n{results}\n"
            s.update(label="✅ Données récupérées !", state="complete", expanded=False)
        except:
            s.update(label="❌ Erreur web", state="error")

    # B. Rédaction Script
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        CONTEXTE : Tu es un assistant vocal masculin.
        ZONE : {region}
        PROFIL : {instructions_profil}
        DONNÉES : {context_web}
        
        CONSIGNE DE RÉDACTION :
        - Rédige un texte DENSE (environ 600-800 mots).
        - Style RADIO : Phrases courtes. Ponctuation forte.
        - Pas de titres, pas de gras. Juste le texte à lire.
        """
        response = model.generate_content(prompt)
        text_script = response.text
    except Exception as e:
        return f"Erreur IA : {e}", None

    # C. Audio via Edge TTS
    try:
        audio_bytes = get_audio(text_script, nom_profil)
        return text_script, audio_bytes
    except Exception as e:
        return text_script, None

# --- 7. INTERFACE ---
# Gestion état
if "step" not in st.session_state: st.session_state.step = 1 
if "selected_profile" not in st.session_state: st.session_state.selected_profile = None
if "selected_region" not in st.session_state: st.session_state.selected_region = None
if "result_text" not in st.session_state: st.session_state.result_text = None
if "result_audio" not in st.session_state: st.session_state.result_audio = None

st.title("🎧 Mon Assistant Actu")

# Retour
if st.session_state.step > 1:
    if st.button("⬅️ Retour", key="btn_ret"):
        st.session_state.step = 1
        st.session_state.result_text = None
        st.session_state.result_audio = None
        st.rerun()

# ÉTAPE 1
if st.session_state.step == 1:
    st.subheader("Qui êtes-vous ?")
    keys = list(PROFILS.keys())
    cols = st.columns(len(keys))
    for i, key in enumerate(keys):
        with cols[i]:
            if st.button(key, use_container_width=True, key=f"p_{i}"):
                st.session_state.selected_profile = key
                st.session_state.step = 2
                st.rerun()

# ÉTAPE 2
elif st.session_state.step == 2:
    try: prenom = st.session_state.selected_profile.split(' ')[1]
    except: prenom = "User"
    st.subheader(f"Bonjour {prenom}, quelle zone ?")
    cols = st.columns(2)
    for i, r in enumerate(REGIONS):
        with cols[i%2]:
            if st.button(r, use_container_width=True, key=f"r_{i}"):
                st.session_state.selected_region = r
                st.session_state.step = 3
                st.rerun()

# ÉTAPE 3
elif st.session_state.step == 3:
    st.subheader("🎙️ Production du rapport...")
    
    if st.session_state.result_text is None:
        with st.spinner("Analyse des sources et synthèse vocale..."):
            p_blob = PROFILS[st.session_state.selected_profile]
            r_blob = st.session_state.selected_region
            txt, aud = ask_agent_radio(r_blob, p_blob, st.session_state.selected_profile)
            st.session_state.result_text = txt
            st.session_state.result_audio = aud
            st.rerun()
            
    if st.session_state.result_audio:
        st.audio(st.session_state.result_audio, format='audio/mp3', start_time=0)
        st.success("Lecture prête.")
        
    with st.expander("📄 Script complet"):
        st.write(st.session_state.result_text)
