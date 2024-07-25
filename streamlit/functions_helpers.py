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
from dotenv import load_dotenv

load_dotenv()

bucket_name =   os.getenv('BUCKET_NAME')
state_machine_arn = os.getenv('state_machine_arn') 
api_key =os.getenv('API_KEY')
url = os.getenv('URL')
OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
# Initialisation des clients AWS
s3_client = boto3.client('s3')
stepfunctions_client = boto3.client('stepfunctions')


# Input pour Step Function
def input_data(current):
    return {
        'COLLECTION_NAME': current,
        'BUCKET_NAME': bucket_name,
        'KEY_FILE': f'{current}/document.pdf',
        'OUTPUT_EXTRACT_TABLES': f'{current}/Tables',
        'OUTPUT_EXTRACT_TEXTES': f'{current}/TEXTES',
        'OUTPUT_EXTRACT_IMAGES': f'{current}/IMAGES',
        'OUTPUT_SUMMARIZES': f'{current}/SUMMARIZES',
        'KEY_TEXT': f'{current}/TEXTES/document.txt'
    }

# Configuration de LangChain
def chain_Q(collection_name):
    embeddings = OpenAIEmbeddings()
    vect = Qdrant.from_existing_collection(embeddings, url=url, prefer_grpc=True, api_key=api_key,
                                            collection_name=collection_name)
    retriever = vect.as_retriever()
    model = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

    template = """
    En utilisant le contexte fourni, donnez une réponse concise à la question posée.
    Si vous ne connaissez pas la réponse, indiquez simplement "je ne sais pas" et n'essayez pas d'inventer une réponse.
    La réponse doit être exprimée uniquement en valeur numérique avec une unité, suivie d'une explication. Si vous ne savez pas, répondez uniquement "je ne sais pas".
    La réponse doit être en format JSON avec deux clés : "reponse" et "explication".
    Format de la réponse :
    {{ "reponse": (ici votre réponse), "explication": (ici votre explication) }}

    Contexte: {context}
    Question: {question}
    Réponse:
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    return chain

# Fonction pour télécharger le fichier sur S3
def upload_to_s3(file_content, bucket, key):
    try:
        s3_client.upload_fileobj(io.BytesIO(file_content), bucket, key)
        st.success("Fichier téléchargé avec succès sur S3.")
        return True
    except Exception as e:
        st.error(f"Erreur lors du téléchargement vers S3 : {e}")
        return False

# Fonction pour démarrer la Step Function
def start_step_function(input_data):
    try:
        response = stepfunctions_client.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(input_data)
        )
        return response['executionArn']
    except Exception as e:
        st.error(f"Erreur lors du démarrage de la Step Function : {e}")
        return None

# Fonction pour vérifier l'état de la Step Function
def check_step_function_status(execution_arn):
    try:
        response = stepfunctions_client.describe_execution(executionArn=execution_arn)
        return response['status']
    except Exception as e:
        st.error(f"Erreur lors de la vérification de l'état de la Step Function : {e}")
        return None