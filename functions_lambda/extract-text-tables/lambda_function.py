import os
import boto3
import pdfplumber
from io import BytesIO
import json


# Initialiser le client S3
s3 = boto3.client('s3')

def extract_and_store(bucket_name, pdf_key,output_extract_text,output_extract_tables):
    # Télécharger le fichier PDF depuis S3
    response = s3.get_object(Bucket=bucket_name, Key=pdf_key)
    pdf_bytes = response['Body'].read()

    # Utiliser pdfplumber pour extraire les tables et les textes
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        content_tables = []
        content_texts = []
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            texts = page.extract_text()
            if texts:
                content_texts.append(texts)
            for j, table in enumerate(tables):
                if not all(all(cell == '' for cell in row) for row in table):
                    table_key = f"{output_extract_tables}/{i}-{j}.json"
                    s3.put_object(Bucket=bucket_name, Key=table_key, Body=str({'table': table}).encode())
                    content_tables.append(table)

    # Enregistrer les textes dans S3
    texts_key = f"{output_extract_text}/document.txt"
    s3.put_object(Bucket=bucket_name, Key=texts_key, Body="\n".join(content_texts).encode())

    # Renvoyer les clés des résultats stockés dans S3
    return {
        'Tables_key': output_extract_tables,
        'Texts_key': texts_key
    }


def lambda_handler(event,context):

    # Récupérer les variables d'environnement
    bucket_name = event['BUCKET_NAME']
    pdf_key = event['KEY_FILE']
    output_extract_text=event['OUTPUT_EXTRACT_TEXTES']
    output_extract_tables=event['OUTPUT_EXTRACT_TABLES']


    results = extract_and_store(bucket_name, pdf_key,output_extract_text,output_extract_tables)

    return {
            'statusCode': 200,
            'Body': json.dumps(boto3.__version__)
        }

