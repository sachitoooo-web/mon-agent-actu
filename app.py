import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults

# --- 1. CONFIGURATION DES PROFILS (C'est ici que tu définis tes règles !) ---
PROFILS = {
    "Profil Pro (Finance/Tech)": """
        Tu es un assistant exécutif très sérieux et concis.
        Tes sujets prioritaires : Bourse, IA, Startups, Crypto.
        Ton style : Listes à puces, chiffres précis, vouvoiement.
        Ignore les sujets "people" ou sport.
    """,
    
    "Profil Perso (Détente)": """
        Tu es un pote curieux et drôle.
        Tes sujets prioritaires : Cinéma, Jeux Vidéo, Sciences insolites, Sport.
        Ton style : Tutoiement, emojis, blagues légères.
        Explique les choses simplement comme à un enfant de 10 ans.
    """
}

# --- 2. SETUP DE LA PAGE ---
st.set_page_config(page_title="Mon Agent Multi-Profils", page_icon="👥")

# --- 3. CONNEXION AUX CLÉS ---
try:
    api_key_google = st.secrets["GOOGLE_API_KEY"]
    api_key_tavily = st.secrets["TAVILY_API_KEY"]
    genai.configure(api_key=api_key_google)
except Exception as e:
    st.error(f"Erreur de clés : {e}")
    st.stop()

# --- 4. GESTION DE LA SESSION (LOGIN) ---
if "current_profile" not in st.session_state:
    st.session_state.current_profile = None

# ÉCRAN DE CONNEXION (Si aucun profil n'est choisi)
if st.session_state.current_profile is None:
    st.title("👤 Qui utilise l'agent ?")
    st.write("Choisis ton mode pour que je m'adapte à tes besoins.")
    
    # Menu déroulant
    choix = st.selectbox("Sélectionne un profil :", list(PROFILS.keys()))
    
    if st.button("C'est parti ! 🚀"):
        st.session_state.current_profile = choix
        st.rerun() # On recharge la page pour lancer l'interface
    
    st.stop() # On arrête le code ici tant qu'on n'est pas connecté

# --- 5. INTERFACE PRINCIPALE (Une fois connecté) ---
profil_nom = st.session_state.current_profile
profil_regles = PROFILS[profil_nom]

# Barre latérale pour changer de profil
with st.sidebar:
    st.write(f"Connecté en tant que : **{profil_nom}**")
    if st.button("Changer de profil 🔄"):
        st.session_state.current_profile = None
        st.session_state.messages = [] # On vide la mémoire de chat
        st.rerun()

st.title(f"🤖 Agent Actu - Mode {profil_nom}")

# --- 6. CERVEAU DE L'AGENT ---
def ask_agent(user_input, instructions_profil):
    # Recherche Web
    context_web = ""
    mots_cles = ["actu", "news", "récent", "aujourd'hui", "hier", "chercher"]
    
    if any(mot in user_input.lower() for mot in mots_cles):
        status = st.status(f"🔍 Recherche en cours pour {profil_nom}...", expanded=True)
        try:
            search = TavilySearchResults(tavily_api_key=api_key_tavily, k=3)
            results = search.invoke(user_input)
            context_web = f"\n\n[SOURCES WEB] :\n{results}\n"
            status.update(label="✅ Infos trouvées !", state="complete", expanded=False)
        except:
            status.update(label="❌ Pas d'infos web", state="error")
    
    # Génération
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # LE SECRET EST ICI : On injecte les règles du profil dans le prompt
        prompt_complet = f"""
        INSTRUCTIONS DE PERSONNALITÉ (RESPECTE IMPÉRATIVEMENT) :
        {instructions_profil}
        
        CONTEXTE WEB :
        {context_web}
        
        QUESTION UTILISATEUR : {user_input}
        """
        
        response = model.generate_content(prompt_complet)
        return response.text
    except Exception as e:
        return f"Erreur : {e}"

# --- 7. CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Pose ta question ({profil_nom})..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # On passe les règles du profil à la fonction
        reponse = ask_agent(prompt, profil_regles)
        st.markdown(reponse)
    
    st.session_state.messages.append({"role": "assistant", "content": reponse})
