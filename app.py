import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults
from gtts import gTTS
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Podcast IA Actu", page_icon="🎙️")

# --- 2. DÉFINITION DES PROFILS (Mode Script Radio) ---
PROFILS = {
    "🕵️‍♀️ MERIEM (Investigation)": """
        Tu es Meriem, une journaliste d'investigation indépendante.
        Ta tâche : Rédiger un SCRIPT DE PODCAST RADIO de 3 minutes (environ 500 mots).
        Ton ton : Engagé, sérieux mais accessible, direct.
        Structure du script :
        1. Intro : "Bonjour, ici Meriem pour votre revue de presse indépendante..."
        2. Le gros dossier (Investigation/Géopolitique).
        3. Le tour du monde rapide.
        4. Outro : Une phrase de conclusion percutante.
        
        Sources : Mediapart, The Intercept, Al Jazeera, etc.
        Important : Ne lis pas les URL, cite juste les noms des journaux.
    """,
    
    "🚀 SACHA (Business/VC)": """
        Tu es Sacha, analyste VC à la Silicon Valley.
        Ta tâche : Rédiger un SCRIPT DE PODCAST RADIO de 3 minutes (environ 500 mots).
        Ton ton : Dynamique, rapide, "Business Class", professionnel.
        Structure du script :
        1. Intro : "Hello les makers, c'est Sacha pour le Market Update..."
        2. Le signal fort (Tech/Bourse).
        3. Les opportunités (Startups/Innovation).
        4. Outro : "Stay hungry, à demain."
        
        Sources : Bloomberg, TechCrunch, Financial Times.
        Important : Ne lis pas les URL, cite juste les noms des journaux.
    """
}

# --- 3. DÉFINITION DES RÉGIONS ---
REGIONS = [
    "🌍 Monde Entier (Global)",
    "🇪🇺 Europe",
    "🇺🇸 Amériques (Nord/Sud)",
    "🌍 Afrique",
    "🌏 Asie & Océanie",
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

# --- 5. FONCTION INTELLIGENTE (Texte + Audio) ---
def ask_agent_podcast(region, instructions_profil, nom_profil):
    # A. Recherche Web
    status_container = st.empty()
    context_web = ""
    
    # On nettoie le nom de la région pour la recherche (enlève les emojis)
    region_clean = region.split(" ")[1] 
    
    with status_container.status(f"🎧 Préparation du podcast ({region})...", expanded=True) as s:
        try:
            search = TavilySearchResults(tavily_api_key=api_key_tavily, k=6) # Plus de sources pour 3 min
            # Requête optimisée avec la région
            query = f"latest news {region_clean} investigation business technology today significant events"
            results = search.invoke(query)
            context_web = f"\n[SOURCES] :\n{results}\n"
            s.update(label="✅ Infos collectées !", state="complete", expanded=False)
        except:
            s.update(label="❌ Recherche web difficile", state="error")

    # B. Génération du Script (Texte)
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        CONTEXTE : Tu es un présentateur de podcast.
        ZONE GÉOGRAPHIQUE : {region}
        
        INSTRUCTIONS DE PERSONNALITÉ : 
        {instructions_profil}
        
        INFOS DU WEB À TRAITER : 
        {context_web}
        
        Rédige le script complet du podcast maintenant. Écris-le pour qu'il soit lu à l'oral (style fluide).
        """
        response = model.generate_content(prompt)
        text_script = response.text
    except Exception as e:
        return f"Erreur IA : {e}", None

    # C. Génération de l'Audio (TTS)
    try:
        # On utilise gTTS (Google Text-to-Speech)
        tts = gTTS(text=text_script, lang='fr', slow=False)
        # On sauvegarde en mémoire (pas de fichier sur le disque)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return text_script, audio_bytes
    except Exception as e:
        return text_script, None

# --- 6. GESTION D'ÉTAT ---
if "step" not in st.session_state:
    st.session_state.step = 1 # Etape 1: Profil, 2: Région, 3: Résultat
if "selected_profile" not in st.session_state:
    st.session_state.selected_profile = None
if "selected_region" not in st.session_state:
    st.session_state.selected_region = None
if "result_text" not in st.session_state:
    st.session_state.result_text = None
if "result_audio" not in st.session_state:
    st.session_state.result_audio = None

# --- 7. INTERFACE ---

# BOUTON RETOUR (Si on n'est pas à l'étape 1)
if st.session_state.step > 1:
    if st.button("⬅️ Recommencer"):
        st.session_state.step = 1
        st.session_state.result_text = None
        st.session_state.result_audio = None
        st.rerun()

# ÉTAPE 1 : CHOIX DU PROFIL
if st.session_state.step == 1:
    st.title("🎙️ Choisissez votre Narrateur")
    col1, col2 = st.columns(2)
    keys = list(PROFILS.keys())
    
    with col1:
        if st.button(keys[0], use_container_width=True):
            st.session_state.selected_profile = keys[0]
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button(keys[1], use_container_width=True):
            st.session_state.selected_profile = keys[1]
            st.session_state.step = 2
            st.rerun()

# ÉTAPE 2 : CHOIX DE LA RÉGION
elif st.session_state.step == 2:
    nom_perso = st.session_state.selected_profile.split(' ')[1]
    st.title(f"🌍 Quelle zone pour {nom_perso} ?")
    
    # Affichage des régions en grille de boutons
    cols = st.columns(2)
    for i, region in enumerate(REGIONS):
        if cols[i % 2].button(region, use_container_width=True):
            st.session_state.selected_region = region
            st.session_state.step = 3
            st.rerun()

# ÉTAPE 3 : GÉNÉRATION ET LECTURE
elif st.session_state.step == 3:
    st.title("🎧 Votre Podcast est prêt")
    
    # Si on n'a pas encore généré, on le fait maintenant
    if st.session_state.result_text is None:
        with st.spinner("Fabrication du podcast (Rédaction + Enregistrement audio)..."):
            profil_blob = PROFILS[st.session_state.selected_profile]
            region_blob = st.session_state.selected_region
            
            texte, audio = ask_agent_podcast(region_blob, profil_blob, st.session_state.selected_profile)
            
            st.session_state.result_text = texte
            st.session_state.result_audio = audio
            st.rerun()
    
    # Affichage du lecteur audio
    if st.session_state.result_audio:
        st.success("Lecture disponible !")
        st.audio(st.session_state.result_audio, format='audio/mp3', start_time=0)
    
    # Affichage du script (Optionnel, dans un accordéon pour pas gêner)
    with st.expander("📖 Lire le script"):
        st.markdown(st.session_state.result_text)

    # Note de bas de page
    st.info("💡 Note : La voix est générée synthétiquement par Google TTS (Gratuit).")
