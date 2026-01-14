import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults
import time

# --- 1. CONFIGURATION DES PROFILS ---
PROFILS = {
    "👔 PRO (Finance/Tech)": """
        Tu es un analyste de marché concis et factuel.
        Concentre-toi UNIQUEMENT sur : Tech, Finance, Bourse, Crypto, IA.
        Format : Bullet points précis. Pas de blabla.
        Ignore le sport et les faits divers.
    """,
    
    "☕ PERSO (Détente)": """
        Tu es un ami sympa qui fait le tri dans l'info.
        Sujets : Cinéma, Culture, Sport, Faits insolites, Sciences.
        Ton ton est léger, tu utilises des emojis.
        Fais des résumés courts et faciles à lire.
    """
}

# --- 2. SETUP ---
st.set_page_config(page_title="Flash Actu", page_icon="⚡")

# --- 3. CONNEXION ---
try:
    api_key_google = st.secrets["GOOGLE_API_KEY"]
    api_key_tavily = st.secrets["TAVILY_API_KEY"]
    genai.configure(api_key=api_key_google)
except Exception as e:
    st.error(f"Erreur de clés : {e}")
    st.stop()

# --- 4. FONCTION CERVEAU ---
def ask_agent(user_input, instructions_profil, nom_profil):
    # Recherche Web
    context_web = ""
    status = st.status(f"⚡ Recherche des actus ({nom_profil})...", expanded=True)
    try:
        search = TavilySearchResults(tavily_api_key=api_key_tavily, k=5) # On cherche 5 articles
        results = search.invoke(user_input)
        context_web = f"\n[SOURCES WEB] :\n{results}\n"
        status.update(label="✅ Infos trouvées !", state="complete", expanded=False)
    except:
        status.update(label="❌ Pas d'infos web", state="error")
    
    # Génération
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        INSTRUCTIONS STRICTES : {instructions_profil}
        
        CONTEXTE WEB : {context_web}
        
        DEMANDE : {user_input}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur : {e}"

# --- 5. INITIALISATION VARIABLES ---
if "current_profile" not in st.session_state:
    st.session_state.current_profile = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auto_start" not in st.session_state:
    st.session_state.auto_start = False

# --- 6. ÉCRAN D'ACCUEIL (BOUTONS) ---
if st.session_state.current_profile is None:
    st.title("⚡ Flash Info Express")
    st.write("Clique sur un profil pour lancer ton résumé immédiat :")
    
    col1, col2 = st.columns(2)
    
    # Bouton Profil 1
    with col1:
        key_pro = "👔 PRO (Finance/Tech)"
        if st.button(key_pro, use_container_width=True):
            st.session_state.current_profile = key_pro
            st.session_state.auto_start = True # On active le démarrage auto
            st.rerun()

    # Bouton Profil 2
    with col2:
        key_perso = "☕ PERSO (Détente)"
        if st.button(key_perso, use_container_width=True):
            st.session_state.current_profile = key_perso
            st.session_state.auto_start = True # On active le démarrage auto
            st.rerun()
            
    st.stop()

# --- 7. INTERFACE CHAT ---
profil_nom = st.session_state.current_profile
profil_regles = PROFILS[profil_nom]

# Sidebar pour changer
with st.sidebar:
    st.title(f"Mode : {profil_nom}")
    if st.button("⬅️ Changer de profil"):
        st.session_state.current_profile = None
        st.session_state.messages = []
        st.session_state.auto_start = False
        st.rerun()

st.title(f"Actualité du jour")

# --- 8. DÉCLENCHEUR AUTOMATIQUE (MAGIE) ---
# C'est ici que ça se passe : si on vient d'arriver, on lance la recherche tout seul
if st.session_state.auto_start:
    prompt_auto = "Fais-moi un résumé complet des actualités importantes des dernières 24h selon mon profil."
    
    # On affiche la question de l'utilisateur (virtuel)
    st.session_state.messages.append({"role": "user", "content": prompt_auto})
    
    # On lance l'agent
    reponse = ask_agent(prompt_auto, profil_regles, profil_nom)
    st.session_state.messages.append({"role": "assistant", "content": reponse})
    
    # On désactive le démarrage auto pour ne pas que ça boucle
    st.session_state.auto_start = False
    st.rerun()

# --- 9. AFFICHAGE DES MESSAGES ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 10. ZONE DE CHAT (Pour continuer la discussion) ---
if prompt := st.chat_input("Approfondir un sujet..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        reponse = ask_agent(prompt, profil_regles, profil_nom)
        st.markdown(reponse)
    
    st.session_state.messages.append({"role": "assistant", "content": reponse})
