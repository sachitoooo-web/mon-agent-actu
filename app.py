import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults
from gtts import gTTS
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Mon Assistant Actu", page_icon="🎧")

# --- 2. DÉFINITION DES PROFILS ---
PROFILS = {
    "🕵️‍♀️ MERIEM (Investigation)": """
        CONTEXTE : Tu es l'assistant personnel d'intelligence économique de Meriem.
        TON AUDITRICE : Meriem cherche des infos alternatives, de l'investigation et du fond. Elle déteste le superficiel.
        TES SOURCES : Mediapart, The Intercept, Al Jazeera, ONG, Rapports indépendants.
        
        STRUCTURE DE TON BRIEFING AUDIO :
        1. SALUTATION : "Bonjour Meriem. Voici ta revue de presse investigation pour la zone [ZONE]."
        2. LE DOSSIER DU JOUR : Raconte-lui une info "hors radar" ou un scandale géopolitique/écologique important.
        3. LE POINT DE VUE : Synthétise un angle critique sur l'actu majeure.
        4. CONCLUSION : "Voilà pour l'essentiel, Meriem. Bonne journée."
        
        TON : Calme, posé, très intellectuel et précis. Tu t'adresses directement à elle.
    """,
    
    "🚀 SACHA (Business/VC)": """
        CONTEXTE : Tu es l'analyste junior de Sacha, un investisseur VC pressé.
        TON AUDITEUR : Sacha veut des signaux de marché, des chiffres, de la tech. Il veut savoir où investir.
        TES SOURCES : Bloomberg, TechCrunch, Y Combinator, Les Echos.
        
        STRUCTURE DE TON BRIEFING AUDIO :
        1. SALUTATION : "Bonjour Sacha. Prêt pour le market update de la zone [ZONE] ? C'est parti."
        2. LE MARKET MOVER : L'info qui fait bouger la bourse ou la tech aujourd'hui.
        3. LA STARTUP / TECH : Une innovation ou une levée de fonds à noter.
        4. CONCLUSION : "Fin du briefing Sacha. À plus tard."
        
        TON : Rapide, énergique, droit au but. Pas de phrases inutiles.
    """
}

# --- 3. DÉFINITION DES RÉGIONS ---
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

# --- 5. FONCTION INTELLIGENTE ---
def ask_agent_radio(region, instructions_profil, nom_profil):
    # A. Recherche Web
    status_container = st.empty()
    region_clean = region.split(" ")[1] if " " in region else region
    
    # Mots-clés contextuels
    if "MERIEM" in nom_profil:
        keywords = "investigation corruption human rights geopolitics independent news"
    else:
        keywords = "market trends venture capital startups tech finance news"

    with status_container.status(f"📡 Recherche pour {nom_profil.split(' ')[1]} ({region})...", expanded=True) as s:
        try:
            search = TavilySearchResults(tavily_api_key=api_key_tavily, k=5)
            query = f"top news {region_clean} {keywords} today latest details"
            results = search.invoke(query)
            context_web = f"\n[INFOS WEB] :\n{results}\n"
            s.update(label="✅ Infos trouvées !", state="complete", expanded=False)
        except:
            s.update(label="❌ Erreur web", state="error")

    # B. Rédaction Script
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        CONTEXTE : Tu es un assistant vocal qui parle à son utilisateur.
        ZONE : {region}
        
        TA MISSION ET TON UTILISATEUR : 
        {instructions_profil}
        
        LES INFOS DU JOUR : 
        {context_web}
        
        CONSIGNE TECHNIQUE : Rédige uniquement le texte parlé. Utilise la ponctuation pour rendre la lecture fluide.
        """
        response = model.generate_content(prompt)
        text_script = response.text
    except Exception as e:
        return f"Erreur IA : {e}", None

    # C. Audio
    try:
        tts = gTTS(text=text_script, lang='fr', slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return text_script, audio_bytes
    except Exception as e:
        return text_script, None

# --- 6. NAVIGATION ---
if "step" not in st.session_state:
    st.session_state.step = 1 
if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = None
if "selected_region" not in st.session_state:
    st.session_state.selected_region = None
if "result_text" not in st.session_state:
    st.session_state.result_text = None
if "result_audio" not in st.session_state:
    st.session_state.result_audio = None

# --- 7. INTERFACE ---
st.title("🎧 Mon Assistant Actu")

# BOUTON RETOUR (Toujours visible si étape > 1)
if st.session_state.step > 1:
    if st.button("⬅️ Retour au début", key="btn_retour"):
        st.session_state.step = 1
        st.session_state.result_text = None
        st.session_state.result_audio = None
        st.rerun()

# ÉTAPE 1 : IDENTIFICATION
if st.session_state.step == 1:
    st.subheader("Qui êtes-vous ?")
    
    keys = list(PROFILS.keys())
    # Colonnes dynamiques
    cols = st.columns(len(keys))
    
    for i, key in enumerate(keys):
        with cols[i]:
            # Clé unique indispensable pour éviter les bugs d'affichage
            if st.button(key, use_container_width=True, key=f"profil_{i}"):
                st.session_state.selected_profile = key
                st.session_state.step = 2
                st.rerun()

# ÉTAPE 2 : ZONE D'INTÉRÊT
elif st.session_state.step == 2:
    # Récupération sécurisée du prénom
    try:
        prenom_user = st.session_state.selected_profile.split(' ')[1]
    except:
        prenom_user = "Utilisateur"

    st.subheader(f"Bonjour {prenom_user}, quelle zone t'intéresse ?")
    
    # Affichage des régions
    cols_geo = st.columns(2)
    for i, region in enumerate(REGIONS):
        # On alterne les colonnes gauche/droite
        col_actuelle = cols_geo[i % 2]
        
        with col_actuelle:
            # Clé unique "geo_{i}" pour forcer l'affichage
            if st.button(region, use_container_width=True, key=f"geo_{i}"):
                st.session_state.selected_region = region
                st.session_state.step = 3
                st.rerun()

# ÉTAPE 3 : BRIEFING
elif st.session_state.step == 3:
    st.subheader("🎙️ Briefing en cours...")
    
    if st.session_state.result_text is None:
        with st.spinner("Je compile tes informations..."):
            profil_blob = PROFILS[st.session_state.selected_profile]
            region_blob = st.session_state.selected_region
            
            texte, audio = ask_agent_radio(region_blob, profil_blob, st.session_state.selected_profile)
            
            st.session_state.result_text = texte
            st.session_state.result_audio = audio
            st.rerun()
    
    if st.session_state.result_audio:
        st.audio(st.session_state.result_audio, format='audio/mp3', start_time=0)
        st.success("Briefing prêt.")
    
    with st.expander("📄 Lire le script"):
        st.write(st.session_state.result_text)
