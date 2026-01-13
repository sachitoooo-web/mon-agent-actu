import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Mon Agent Actu", page_icon="🗞️")
st.title("🗞️ Mon Expert Actualité")

# 2. INSTRUCTIONS DE L'AGENT
SYSTEM_PROMPT = """
Tu es un assistant expert en actualité quotidienne.
Ta mission : Chercher les infos du jour sur le web et faire des synthèses.
Règles :
- Cite toujours tes sources.
- Sois neutre et factuel.
"""

# 3. GESTION DES CLÉS SECRÈTES
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
except:
    st.error("Les clés API manquent ! Il faut les ajouter dans les réglages de Streamlit.")
    st.stop()

# 4. INITIALISATION DE LA MÉMOIRE
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. FONCTION DU CERVEAU (LLM + RECHERCHE)
def ask_agent(user_message):
    
    # --- MODIFICATION ICI : ON DESACTIVE LES FILTRES DE SECURITE ---
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=GOOGLE_API_KEY,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    # ---------------------------------------------------------------

    search_tool = TavilySearchResults(tavily_api_key=TAVILY_API_KEY, k=3)
    
    context_web = ""
    mots_cles = ["actu", "news", "récent", "aujourd'hui", "hier", "chercher"]
    if any(mot in user_message.lower() for mot in mots_cles):
        with st.status("🔍 Je scanne le web...", expanded=True) as status:
            try:
                raw_results = search_tool.invoke(user_message)
                context_web = f"\n\n[INFOS DU WEB À UTILISER]: {raw_results}\n"
                status.update(label="✅ Infos trouvées !", state="complete", expanded=False)
            except:
                st.warning("Recherche web échouée.")

    conversation = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            conversation.append(HumanMessage(content=msg["content"]))
        else:
            conversation.append(SystemMessage(content=msg["content"]))
    
    conversation.append(HumanMessage(content=user_message + context_web))
    
    response = llm.invoke(conversation)
    return response.content

# 6. INTERFACE DE CHAT
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Quelle est l'actu aujourd'hui ?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ask_agent(prompt)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
