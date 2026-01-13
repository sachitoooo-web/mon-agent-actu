import streamlit as st
import os
# On importe la librairie officielle en secours pour valider la clé si besoin
import google.generativeai as genai 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage

# CONFIGURATION PAGE
st.set_page_config(page_title="Mon Agent Actu", page_icon="🗞️")
st.title("🗞️ Mon Expert Actualité")

# RECUPERATION CLES
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except:
    st.error("Clés introuvables. Vérifie les secrets.")
    st.stop()

# --- DIAGNOSTIC AUTOMATIQUE ---
# Ce petit bout de code va vérifier silencieusement si la clé fonctionne
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    # On teste juste si on arrive à lister les modèles
    list(genai.list_models())
except Exception as e:
    st.error(f"❌ Problème critique avec la clé Google : {e}")
    st.stop()
# -----------------------------

# FONCTION PRINCIPALE
def ask_agent(user_message):
    # On utilise le modèle Flash qui est rapide et gratuit
    # Si ça plante encore, on essaiera "gemini-1.0-pro"
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True # Astuce pour éviter certains bugs
    )
    
    search_tool = TavilySearchResults(tavily_api_key=TAVILY_API_KEY, k=3)
    
    context_web = ""
    if "actu" in user_message.lower() or "news" in user_message.lower():
        with st.status("🔍 Recherche en cours...", expanded=True) as status:
            try:
                raw_results = search_tool.invoke(user_message)
                context_web = f"\nINFOS WEB : {raw_results}"
                status.update(label="Trouvé !", state="complete", expanded=False)
            except:
                st.warning("Recherche web impossible.")

    messages = [
        SystemMessage(content="Tu es un expert en actualité. Synthétise les infos."),
        HumanMessage(content=user_message + context_web)
    ]
    
    # Historique simplifié pour le test
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            messages.insert(1, HumanMessage(content=msg["content"]))
        else:
            messages.insert(2, SystemMessage(content=msg["content"]))

    response = llm.invoke(messages)
    return response.content

# INTERFACE
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Quelle est l'actu ?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = ask_agent(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Erreur : {e}")
