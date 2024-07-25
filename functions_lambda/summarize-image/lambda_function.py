import json

import os
import base64
import boto3
import mimetypes
import openai
from openai import OpenAI
from PIL import Image
from io import BytesIO
import uuid
import json



def image_to_base64(image_bytes):
    # Convertir les bytes de l'image en base64
    encoded_string = base64.b64encode(image_bytes).decode('utf-8')
    mime_type = 'image/jpeg'  # Modifier en fonction du type d'image téléchargé

    image_base64 = f"data:{mime_type};base64,{encoded_string}"
    return image_base64

def describe_images(base64_string,client):
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Je voudrais que vous me fournissiez une description détaillée de cette image, en incluant toutes les informations visibles et pertinentes. Merci de fournir, avec un paragraphe, un résumé détaillé basé sur cette image. Veuillez également citer toutes les valeurs numériques présentes dans l'image et expliquer leur signification."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": base64_string ,
                        "detail": "low"
                    }
                },
            ],
          }
        ],
         max_tokens=1500,
       )
    return response.choices[0].message.content




def lambda_handler(event,context):

    # Récupérer les variables d'environnement
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


    INPUT_BUCKET = event['BUCKET_NAME']
    IMAGE_KEY = event['IMAGE_KEY']
    OUTPUT_SUMMARIZES = event['OUTPUT_SUMMARIZES']

 

    # Initialiser le client OpenAI et S3
    s3 = boto3.client('s3')
    openai.api_key = OPENAI_API_KEY
    client=OpenAI(api_key=OPENAI_API_KEY)




    # Télécharger l'image depuis S3
    response = s3.get_object(Bucket=INPUT_BUCKET, Key=IMAGE_KEY)
    image_bytes = response['Body'].read()

    # Convertir les bytes de l'image en base64
    base64_string = image_to_base64(image_bytes)

    # Obtenir la description de l'image
    description = describe_images(base64_string,client)

    doc_dict = {
            'page_content': description,
            'metadata': {'id':str(uuid.uuid4())}
        }
    data=json.dumps(doc_dict,ensure_ascii=False)
  
    OUTPUT_KEY=f'{OUTPUT_SUMMARIZES}/{IMAGE_KEY.split("/")[-1].split(".")[0]}.json'
    s3.put_object(Bucket=INPUT_BUCKET, Key=OUTPUT_KEY, Body=data)






    return {
        'status':200,
        "body":json.dumps('Hello')
    }