import json
import os
import boto3
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import uuid
import time


def summarize_table(key_file, OPENAI_API_KEY, bucket_name, OUTPUT_SUMMARIZES):
    # Initialize S3 client
    s3 = boto3.client('s3')

    try:
        # Download the JSON file from S3 directly into memory
        response = s3.get_object(Bucket=bucket_name, Key=key_file)
        file_content = response['Body'].read().decode('utf-8')

        # Attempt to load the JSON data
        try:
            data = json.loads(file_content)
        except json.JSONDecodeError:
            # If JSON loading fails, attempt to evaluate as a Python literal
            import ast
            data = ast.literal_eval(file_content)
    except Exception as e:
        print(f"An error occurred: {e}")
        return

     # Prompt
    prompt_text = """Voici un tableau contenant diverses données sur les réservoirs d'eau dans plusieurs communes. Je voudrais que vous me fournissiez un résumé descriptif de ce tableau, en incluant toutes les informations et les chiffres numériques mentionnés. Assurez-vous de citer chaque valeur pour chaque commune et chaque catégorie.: {element} Merci de fournir, avec un paragraphe, un résumé détaillé basé sur ce tableau."""
    prompt = ChatPromptTemplate.from_template(prompt_text)

    # Initialize OpenAI model
    model = ChatOpenAI(temperature=0.1, model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)
 
    summarize_chain = {"element": lambda x: x} | prompt | model | StrOutputParser()



    # Add summary to the data
    summary= summarize_chain.invoke(data['table']) 
    
    doc_dict = {
        'page_content': summary,
        'metadata': {'id': str(uuid.uuid4())}
    }

    # Convert data to JSON string with non-ASCII characters
    output_data = json.dumps(doc_dict, ensure_ascii=False)

    OUTPUT_KEY = f'{OUTPUT_SUMMARIZES}/{key_file.split("/")[-1].split(".")[0]}.json'
    # Upload the updated file back to S3
    try:
        s3.put_object(Bucket=bucket_name, Key=OUTPUT_KEY, Body=output_data)
        print(f"File successfully uploaded to {OUTPUT_KEY}")
    except Exception as e:
        print(f"An error occurred while uploading: {e}")

def lambda_handler(event, context):
    # Load environment variables
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    bucket_name = event['BUCKET_NAME']
    key_file = event['KEY_FILE']
    OUTPUT_SUMMARIZES = event['OUTPUT_SUMMARIZES']

    summarize_table(key_file, OPENAI_API_KEY, bucket_name, OUTPUT_SUMMARIZES)

    return {
        'Status': 200
    }
