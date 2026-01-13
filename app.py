import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults

# --- CONFIGURATION ---
st.set_page_config(page_title="Mon Agent Actu", page_icon="🗞️")
st.title("🗞️ Mon Expert Actualité")

# --- CONNEXION ---
try:
    api_key_google = st.secrets["GOOGLE_API_KEY"]
    api_key_tavily = st.secrets["TAVILY_API_KEY"]
    
    # On configure Google
    genai.configure(api_key=api_key_google)
except Exception as e:
    st.error(f"Erreur de clés : {e}")
    st.stop()

# --- CERVEAU DE L'AGENT ---
def ask_agent(user_input):
    # 1. Recherche Web (Les Yeux)
    context_web = ""
    # On déclenche la recherche si on détecte une intention d'actu
    mots_cles = ["actu", "news", "récent", "aujourd'hui", "hier", "passé", "recherche"]
    if any(mot in user_input.lower() for mot in mots_cles):
        status = st.status("🔍 Lecture du web en cours...", expanded=True)
        try:
            search = TavilySearchResults(tavily_api_key=api_key_tavily, k=3)
            results = search.invoke(user_input)
            context_web = f"\n\n[SOURCES WEB RÉCENTES] :\n{results}\n"
            status.update(label="✅ Infos trouvées !", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Recherche web échouée", state="error")
    
    # 2. Réflexion (Le Cerveau)
    try:
        # ICI ON UTILISE LE MODÈLE QUE TU AS DÉCOUVERT
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt_complet = f"""
        Tu es un assistant expert en synthèse d'actualité.
        Utilise les informations web ci-dessous pour répondre.
        Si tu n'as pas d'infos web, utilise tes connaissances générales.
        Cite tes sources si possible.
        
        {context_web}
        
        QUESTION : {user_input}
        """
        
        response = model.generate_content(prompt_complet)
        return response.text
    except Exception as e:
        return f"Erreur du modèle : {e}"

# --- INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Zone de saisie
if prompt := st.chat_input("Quelles sont les nouvelles ?"):
    # Message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse assistant
    with st.chat_message("assistant"):
        reponse = ask_agent(prompt)
        st.markdown(reponse)
    
    st.session_state.messages.append({"role": "assistant", "content": reponse})
