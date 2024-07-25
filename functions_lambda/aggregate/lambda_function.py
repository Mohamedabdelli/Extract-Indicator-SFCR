import json
import boto3
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient, models
import os
# Définir la classe Document
class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

    def __repr__(self):
        return f"Document(page_content={self.page_content}, metadata={self.metadata})"

s3_client = boto3.client('s3')

# Lire et transformer les fichiers JSON en objets Document
def read_json_from_s3(bucket, key):
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
    return Document(page_content=data['page_content'], metadata=data['metadata'])

def traitement(liste):
    return [item.replace("\\", "") for item in liste]

def lambda_handler(event, context):
    # Déboguer l'événement reçu
    print('Received event:', event)

    try:
        OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
        URL=os.getenv('URL')
        KEY_QDRANT=os.getenv('KEY_QDRANT')
        file_keys = event['FILES_KEYS']
        bucket_name = event['BUCKET_NAME']
        collection_name = event['COLLECTION_NAME']
    except KeyError as e:
        print(f"KeyError: {e}")
        raise

    print('file_keys:', file_keys)
    print('bucket_name:', bucket_name)
    print('collection_name:', collection_name)

    # Créer une liste de documents
    documents = []

    # Lire chaque fichier JSON et créer des objets Document
    for key in traitement(file_keys):
        try:
            print('key:', key)
            document = read_json_from_s3(bucket_name, key)
            documents.append(document)
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier {key}: {str(e)}")

    # Vérifier si des documents ont été extraits
    if not documents:
        print("Aucun document n'a été extrait.")
        return {
            'statusCode': 500,
            'body': json.dumps("Aucun document n'a été extrait.")
        }

    print("Documents extraits:", documents)


    url = URL
    api_key = KEY_QDRANT
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    client = QdrantClient(url=url, api_key=api_key)

    # Vérifiez si la collection existe déjà
    collection_exists = False
    try:
        client.get_collection(collection_name)
        collection_exists = True
        print(f"La collection {collection_name} existe déjà. Ajout des documents à la collection.")
    except Exception as e:
        print(f"La collection {collection_name} n'existe pas encore. Création en cours.")

    if collection_exists:
        # Ajouter des documents à la collection existante
        try:
            qdrant_instance = Qdrant(client=client, collection_name=collection_name, embeddings=embeddings)
            qdrant_instance.add_documents(documents)
        except Exception as e:
            print(f"Erreur lors de l'ajout des documents à la collection: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Erreur lors de l'ajout des documents à la collection: {e}")
            }
    else:
        # Créer une nouvelle collection et y ajouter des documents
        try:
            Qdrant.from_documents(
                documents,
                embeddings,
                url=url,
                prefer_grpc=True,
                api_key=api_key,
                collection_name=collection_name
            )
        except Exception as e:
            print(f"Erreur lors de la création de la collection: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Erreur lors de la création de la collection: {e}")
            }

    return {
        'statusCode': 200,
        'body': json.dumps(collection_name)
    }
