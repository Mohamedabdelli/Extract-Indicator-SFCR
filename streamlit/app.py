import streamlit as st
import time
import pandas as pd
import boto3
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from datetime import datetime
import os
import json
import io
from functions_helpers import input_data,chain_Q,upload_to_s3,start_step_function,check_step_function_status
from dotenv import load_dotenv

load_dotenv()

# Configuration AWS et API keys
bucket_name =   os.getenv('BUCKET_NAME')
state_machine_arn = os.getenv('state_machine_arn') 
api_key =os.getenv('API_KEY_qdrant')
url = os.getenv('URL_qdrant')
OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')

# Initialisation des clients AWS
s3_client = boto3.client('s3')
stepfunctions_client = boto3.client('stepfunctions')

# Utilisation de la barre latérale (sidebar) pour la sélection des indicateurs
indicators = {
    'Fonds propres éligibles à la couverture MCR': 'Fonds propres éligibles à la couverture MCR en 31/12/2023?',
    'Fonds propres éligibles à la couverture SCR': 'Fonds propres éligibles à la couverture SCR en 31/12/2023?',
    'taux de couverture du MCR': 'Taux (ratio) de couverture du MCR en  31/12/2023?',
    'SCR pour risque de marché': 'SCR pour risque de marché en décembre 2023?',
    'taux de couverture du SCR': 'Taux (ratio) de couverture du SCR (not MCR) en 31/12/2023?',

    'SCR pour risque de défaut': 'SCR pour risque de défaut en décembre 2023?',
    'SCR pour risque de souscription santé': 'SCR pour risque de souscription santé en décembre 2023?',
    'SCR pour risque de souscription vie': 'SCR pour risque de souscription vie en décembre 2023?',
    "SCR pour Souscription Non Vie": "SCR Souscription Non Vie en décembre 2023?"
}

st.set_page_config(layout="wide")

# Initialize session state variables
if 'current_time' not in st.session_state:
    st.session_state.current_time = None
if 'execution_arn' not in st.session_state:
    st.session_state.execution_arn = None
if 'status' not in st.session_state:
    st.session_state.status = None
# Interface utilisateur Streamlit
st.title("Extraction des Indicateurs de Solvabilité à partir de PDF SFCR")

# Layout en deux colonnes
left_column, right_column = st.columns([2, 3])

# Colonne de gauche : Upload du fichier PDF
with left_column:
    uploaded_file = st.file_uploader("Uploader un fichier PDF", type="pdf")
    if uploaded_file:
        file_content = uploaded_file.read()
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        file_key = f"{current_time}/document.pdf"

        if upload_to_s3(file_content, bucket_name, file_key):
            st.success("Fichier téléchargé avec succès sur S3.")
            st.session_state.current_time = current_time

# Colonne de droite : Affichage du tableau des résultats
with right_column:
    if st.session_state.current_time:
        current_time = st.session_state.current_time

        # Vérifier si l'exécution est terminée avant d'afficher les résultats
        execution_arn = start_step_function(input_data(current_time))
        if execution_arn:
            st.write("Exécution de la Step Function en cours...")

            while True:
                status = check_step_function_status(execution_arn)
                if status == 'SUCCEEDED':
                    st.success("Extraction des indicateurs terminée avec succès.")
                    break
                elif status == 'FAILED':
                    st.error("Échec de l'extraction des indicateurs.")
                    break
                time.sleep(5)

            # Afficher les résultats des indicateurs
            results = []
            collection_name = current_time
            for indicator, question in indicators.items():
                response = chain_Q(collection_name).invoke(question)
                response_json = json.loads(response)
                results.append({
                    "Indicateur": indicator,
                    "Réponse": str(response_json['reponse']),
                    "Explication": response_json['explication']
                })

            # Affichage du tableau des résultats
            st.write("### Résultats des Indicateurs de Solvabilité")
            if results:
                st.table(pd.DataFrame(results))
            else:
                st.write("Aucun résultat trouvé pour les indicateurs.")
        else:
            st.warning("Uploadez d'abord un fichier PDF pour démarrer le processus.")
    else:
        st.warning("Uploadez un fichier PDF à gauche pour démarrer.")
