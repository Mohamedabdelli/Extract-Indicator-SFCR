import io
import os
import boto3
import fitz  # PyMuPDF
from PIL import Image
import json

# Initialiser le client S3
s3 = boto3.client('s3')

# Fonction pour extraire les images du PDF
def extract_images_from_pdf(bucket_name, pdf_key, output_key_prefix):
    # Télécharger le fichier PDF depuis S3
    response = s3.get_object(Bucket=bucket_name, Key=pdf_key)
    pdf_bytes = response['Body'].read()

    document = fitz.open(stream=pdf_bytes, filetype="pdf")  # Utiliser le paramètre stream pour ouvrir depuis les bytes
    images = []
    
    # Parcourir toutes les pages
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        image_list = page.get_images(full=True)
        
        # Parcourir toutes les images de la page
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Utiliser PIL pour ouvrir l'image
            image = Image.open(io.BytesIO(image_bytes))
            image_name = f"{output_key_prefix}/page_{page_num+1}_image_{img_index+1}.{image_ext}"
            
            # Sauvegarder l'image dans S3 si elle est supérieure à 10 ko
            if len(image_bytes) > 10240:  # 10 ko = 10240 octets
                image_buffer = io.BytesIO()
                image.save(image_buffer, format=image_ext.upper())
                image_buffer.seek(0)
                s3.put_object(Bucket=bucket_name, Key=image_name, Body=image_buffer, ContentType=f'image/{image_ext}')
                images.append(image_name)
    
    return images

def lambda_handler(event, context):
    # Lire les variables d'environnement
    bucket_name = event['BUCKET_NAME']
    pdf_key = event['KEY_FILE']
    output_key_prefix = event['OUTPUT_EXTRACT_IMAGES']

    # Appeler la fonction pour extraire les images
    results = extract_images_from_pdf(bucket_name, pdf_key, output_key_prefix)
    print("Extraction et stockage terminés.")

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }

