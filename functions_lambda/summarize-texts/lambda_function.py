import os
import boto3
import uuid
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import json
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from io import BytesIO
import time
import openai
from tenacity import retry, wait_exponential, stop_after_attempt

s3 = boto3.client('s3')

# Initialiser le client S3

def summarize_text(bucket_name, key_text, openai_api_key):
    # Vérifier que bucket_name et key_text sont des chaînes de caractères
    if not isinstance(bucket_name, str):
        raise TypeError(f"bucket_name should be a string, but got {type(bucket_name)}")
    if not isinstance(key_text, str):
        raise TypeError(f"key_text should be a string, but got {type(key_text)}")
    
    print('bucket_name ',bucket_name)
    print('key_text',key_text)
    # Télécharger le fichier texte depuis S3

    response = s3.get_object(Bucket=bucket_name, Key=key_text)
    content = response['Body'].read().decode('utf-8')
    # Diviser le texte en documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000)
    docs = [Document(page_content=content, metadata={'id_key': str(uuid.uuid4())})]
    docs = text_splitter.split_documents(docs)

    # Diviser en plus petits chunks
    id_key = 'doc_id'
    doc_ids = [str(uuid.uuid4()) for _ in docs]
    time.sleep(1.5)


    child_text_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
    sub_docs = []

    for i, doc in enumerate(docs):
        _id = doc_ids[i]
        _sub_docs = child_text_splitter.split_documents([doc])
        for _doc in _sub_docs:
            _doc.metadata[id_key] = _id
        sub_docs.extend(_sub_docs)

    # Générer les résumés
    chain = (
        {"doc": lambda x: x.page_content}
        | ChatPromptTemplate.from_template("fournir un résumé du document en mettant en évidence les éléments les plus importants :\n\n{doc}")
        | ChatOpenAI(max_retries=0, openai_api_key=openai_api_key)
        | StrOutputParser()
    )

    #summaries = chain.batch(docs, {"max_concurrency": 5})
    @retry(wait=wait_exponential(multiplier=1, min=15, max=60), stop=stop_after_attempt(10))
    def get_summaries():
        return chain.batch(docs, {"max_concurrency": 5})

    summaries = get_summaries()


    doc_ids = [str(uuid.uuid4()) for _ in summaries]

    summary_docs = [
        Document(page_content=s, metadata={id_key: doc_ids[i]})
        for i, s in enumerate(summaries)
    ]

    return docs + summary_docs + sub_docs


def lambda_handler(event,context):

    # Récupérer les variables d'environnement

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    BUCKET_NAME = str(event['BUCKET_NAME'])
    KEY_TEXT = str(event['KEY_TEXT'])
    OUTPUT_EXTRACT_TEXTES = str(event['OUTPUT_EXTRACT_TEXTES'])
    OUTPUT_SUMMARIZES = str(event['OUTPUT_SUMMARIZES'])

    documents_to_qdrant=summarize_text(BUCKET_NAME, KEY_TEXT, OPENAI_API_KEY)
    for i, doc in enumerate(documents_to_qdrant):
        doc_dict = {
            'page_content': doc.page_content,
            'metadata': doc.metadata
        }
        data=json.dumps(doc_dict,ensure_ascii=False)
        summaries_key= f"{OUTPUT_SUMMARIZES}/{str(uuid.uuid4()).split('-')[-1]}.json"

        s3.put_object(Bucket=BUCKET_NAME, Key=summaries_key, Body=data)

    print("Résumé généré et enregistré.")
    return {
        "Status":200
    }