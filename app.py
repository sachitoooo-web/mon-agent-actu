import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Mon Agent Actu", page_icon="🗞️")
st.title("🗞️ Mon Expert Actualité (Mode Direct)")

# Récupération sécurisée des clés
try:
    api_key_google = st.secrets["GOOGLE_API_KEY"]
    api_key_tavily = st.secrets["TAVILY_API_KEY"]
    
    # Configuration DIRECTE de Google (plus fiable)
    genai.configure(api_key=api_key_google)
except Exception as e:
    st.error(f"Erreur de clés : {e}")
    st.stop()

# --- 2. FONCTION INTELLIGENTE ---
def ask_agent_direct(user_input):
    # Etape A : Recherche Web
    context_web = ""
    if "actu" in user_input.lower() or "news" in user_input.lower() or "récent" in user_input.lower():
        status_box = st.status("🔍 Recherche web en cours...", expanded=True)
        try:
            search = TavilySearchResults(tavily_api_key=api_key_tavily, k=3)
            # On force la recherche
            results = search.invoke(user_input)
            context_web = f"\n\nSOURCES WEB RÉCENTES (A UTILISER POUR RÉPONDRE) :\n{results}\n"
            status_box.update(label="✅ Infos trouvées !", state="complete", expanded=False)
        except Exception as e:
            status_box.update(label="❌ Recherche impossible", state="error")
            st.error(f"Erreur Tavily: {e}")

    # Etape B : Génération de réponse (Mode Direct)
    try:
        # On essaie le modèle le plus standard
        model = genai.GenerativeModel('gemini-pro')
        
        # Construction du prompt
        full_prompt = f"""
        Tu es un assistant expert en actualité. 
        Utilise les informations suivantes pour répondre à la question de l'utilisateur.
        Si tu n'as pas d'infos web, utilise tes connaissances.
        
        {context_web}
        
        QUESTION UTILISATEUR : {user_input}
        """
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Erreur Gemini : {e}"

# --- 3. INTERFACE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Zone de saisie
if prompt := st.chat_input("Pose ta question d'actu..."):
    # Affichage user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Réponse assistant
    with st.chat_message("assistant"):
        reponse_text = ask_agent_direct(prompt)
        st.markdown(reponse_text)
    
    st.session_state.messages.append({"role": "assistant", "content": reponse_text})
