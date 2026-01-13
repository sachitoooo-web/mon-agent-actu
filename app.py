import streamlit as st
import google.generativeai as genai
import os

st.title("🕵️ Détective de Modèles")

# 1. Vérification de la version installée
st.write(f"Version des outils Google installée : `{genai.__version__}`")

# 2. Configuration
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    st.success("✅ Clé API trouvée et configurée.")
except Exception as e:
    st.error(f"❌ Erreur de clé : {e}")
    st.stop()

# 3. Lister les modèles disponibles
st.subheader("Modèles disponibles pour ton compte :")

if st.button("Lancer le scan des modèles"):
    try:
        model_found = False
        # On demande à Google : "Qu'est-ce que tu as en rayon ?"
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                st.code(f"Nom exact : {m.name}")
                model_found = True
        
        if not model_found:
            st.warning("Aucun modèle de génération de texte trouvé. Vérifie ton compte Google AI Studio.")
            
    except Exception as e:
        st.error(f"Erreur lors du scan : {e}")
