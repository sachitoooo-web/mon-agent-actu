import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage

# Titre
st.title("🛠️ Test de Connexion Agent")

# Récupération des clés
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
    st.success("✅ Clés détectées.")
except:
    st.error("❌ Clés introuvables.")
    st.stop()

# Test immédiat
if st.button("Tester la connexion Gemini"):
    try:
        # ON UTILISE GEMINI-PRO ICI (C'est la version la plus stable)
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)
        reponse = llm.invoke("Réponds juste par le mot : CONNECTÉ")
        st.success(f"Réponse de Google : {reponse.content}")
    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")

# Interface Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pose une question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # ON UTILISE GEMINI-PRO ICI AUSSI
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY)
        search = TavilySearchResults(tavily_api_key=TAVILY_API_KEY, k=1)
        
        context = ""
        if "actu" in prompt.lower():
            res = search.invoke(prompt)
            context = f"Infos Web : {res}"

        msg = [HumanMessage(content=prompt + context)]
        response = llm.invoke(msg)
        
        with st.chat_message("assistant"):
            st.markdown(response.content)
        st.session_state.messages.append({"role": "assistant", "content": response.content})
        
    except Exception as e:
        st.error(f"Erreur : {e}")
