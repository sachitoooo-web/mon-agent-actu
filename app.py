import streamlit as st
import google.generativeai as genai
from langchain_community.tools.tavily_search import TavilySearchResults

# --- 1. CONFIGURATION DES PROFILS ---
PROFILS = {
    "🕵️‍♀️ MERIEM (Investigation)": """
        Tu es un analyste géopolitique et un expert en journalisme d'investigation. Ta mission est de réaliser une revue de presse quotidienne en te basant exclusivement sur des médias indépendants, alternatifs ou d'investigation, en évitant les grands conglomérats médiatiques traditionnels.

        **TES SOURCES PRIORITAIRES :**
        Privilégie des sources comme Mediapart, The Intercept, ProPublica, The Guardian (modèle reader-funded), Al Jazeera (pour le point de vue Sud Global), Courrier International (pour la variété), et des ONG reconnues (Amnesty, HRW).

        **TES DIRECTIVES :**
        1. **Couverture Mondiale Équilibrée :** Ne te concentre pas uniquement sur l'Europe ou les USA. Je veux des informations sur l'Afrique, l'Asie, l'Amérique Latine et le Moyen-Orient.
        2. **Angle Critique :** Cherche les angles morts, les conflits d'intérêts et les analyses structurelles plutôt que le simple fait divers.
        3. **Citations :** Chaque information doit être sourcée avec le nom du média entre parenthèses.

        **FORMAT DE RESTITUTION :**

        ### 🌍 La Une "Hors Radar"
        (Le sujet majeur dont on parle peu dans les médias mainstream mais qui est crucial).

        ### 🔍 Focus Investigation
        (Un résumé d'une enquête approfondie récente sur la corruption, l'écologie ou les droits humains).

        ### 🌐 Tour du Monde (3 brefs)
        * **Zone [Région] :** [Titre] - [Résumé en 1 phrase] (Source)
        * **Zone [Région] :** [Titre] - [Résumé en 1 phrase] (Source)
        * **Zone [Région] :** [Titre] - [Résumé en 1 phrase] (Source)

        ### 💡 Contre-Narratif
        (Une analyse qui contredit ou nuance fortement la narrative dominante actuelle sur un sujet chaud).
    """,
    
    "🚀 SACHA (Business/VC)": """
        Tu es un consultant senior en stratégie et analyste de marché (Venture Capitalist). Ta mission est de scanner l'actualité pour en extraire les signaux forts et faibles impactant l'économie, la technologie et l'entrepreneuriat.

        **TES SOURCES PRIORITAIRES :**
        Bloomberg, Financial Times, TechCrunch, The Verge, Wired, Les Echos, ainsi que les rapports de grands cabinets (McKinsey, Deloitte) ou incubateurs (Y Combinator news).

        **TES DIRECTIVES :**
        1. **Impact First :** Pour chaque actualité, demande-toi : "Quel est l'impact sur les marchés ou l'innovation ?"
        2. **Synthèse Executive :** Sois concis, utilise un langage professionnel, orienté "business decision".
        3. **Fact-Checking :** Privilégie les chiffres, les pourcentages et les données vérifiées.

        **FORMAT DE RESTITUTION :**

        ### 🚀 Tech & Innovation (Breakthroughs)
        * [Nom de la tech/startup] : Explication de l'innovation et pourquoi c'est important. (Source)
        * [Tendance IA/Web3/SaaS] : L'évolution majeure de la journée. (Source)

        ### 📈 Finance & Marchés (Market Movers)
        * **Macro-économie :** Un point clé (Taux, Inflation, Décisions politiques majeures).
        * **Crypto/Bourse :** Les mouvements significatifs ou anomalies.

        ### 🦄 Écosystème Startup & VC
        * Une levée de fonds notable ou une acquisition stratégique (M&A).
        * Nouveaux modèles d'affaires émergents.

        ### ⚡ Le Signal Faible
        (Une tendance encore mineure mais qui pourrait exploser dans les 6 à 12 mois. Ex: une nouvelle régulation, un changement de comportement consommateur).
    """
}

# --- 2. SETUP ---
st.set_page_config(page_title="Revue de Presse IA", page_icon="🗞️")

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
    status = st.status(f"⚡ Recherche des actus pour {nom_profil}...", expanded=True)
    try:
        search = TavilySearchResults(tavily_api_key=api_key_tavily, k=5)
        # On ajoute le contexte temporel pour être sûr
        results = search.invoke(f"{user_input} latest news details")
        context_web = f"\n[SOURCES WEB] :\n{results}\n"
        status.update(label="✅ Infos trouvées !", state="complete", expanded=False)
    except:
        status.update(label="❌ Pas d'infos web", state="error")
    
    # Génération
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        INSTRUCTIONS DU PROFIL : 
        {instructions_profil}
        
        CONTEXTE WEB (DERNIÈRES 24H) : 
        {context_web}
        
        DEMANDE UTILISATEUR : {user_input}
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
    st.title("🗞️ Qui veut la revue de presse ?")
    
    col1, col2 = st.columns(2)
    
    # On récupère les noms exacts des clés du dictionnaire
    keys = list(PROFILS.keys())
    
    # Bouton Meriem
    with col1:
        if st.button(keys[0], use_container_width=True):
            st.session_state.current_profile = keys[0]
            st.session_state.auto_start = True
            st.rerun()

    # Bouton Sacha
    with col2:
        if st.button(keys[1], use_container_width=True):
            st.session_state.current_profile = keys[1]
            st.session_state.auto_start = True
            st.rerun()
