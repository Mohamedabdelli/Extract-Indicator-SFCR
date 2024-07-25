# Automated Extraction of Solvency Indicators from SFCR Reports

## Project Description

The Solvency and Financial Condition Reports (SFCR), written annually by insurance companies and intended for the public, are essential for assessing the financial strength of insurers.

In this project, using Streamlit, Lambda functions, Docker images on ECR, pipelines with Step Functions, and the Qdrant vector database, we extract the following indicators:

- Eligible own funds to cover MCR
- Eligible own funds to cover SCR
- MCR coverage ratio
- SCR coverage ratio
- SCR for market risk
- SCR for default risk
- SCR for health underwriting risk
- SCR for life underwriting risk
- SCR for non-life underwriting risk

## Prerequisites

- AWS account
- Qdrant
- OpenAI API Key

## Automated Process

1. **Download and Trigger**: An AWS Step Functions pipeline is triggered upon uploading a PDF file.
2. **Image Extraction and Analysis**: Images are extracted and analyzed.
3. **Text Extraction and Segmentation**: Text is extracted and divided into segments (chunks).
4. **Summarization and Q&A Generation**: Each segment is summarized and Q&A is generated.
5. **Table Extraction and Summarization**: Tables are extracted and summarized.
6. **Vectorization and Storage**: Summaries are vectorized and stored in a vector database (Qdrant).
7. **Result Retrieval**: The application connects to Qdrant to retrieve and display results in a table format.

## Installation and Deployment Steps

### 1. Creating Docker Images for Lambda Functions

#### `aggregate` function

```bash
cd functions_lambda/aggregate
docker build -t aggregate-function .
aws ecr create-repository --repository-name aggregate-function
docker tag aggregate-function:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/aggregate-function:latest
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/aggregate-function:latest
```

Repeat these steps for each lambda function:

- Extract-images
- extract-text-tables
- summarize-image
- summarize-table
- summarize-texts
### 2. Creating Lambda Functions in AWS
For each lambda function, create a new function in AWS Lambda and configure it to use the corresponding Docker image from ECR.

### 3. Creating the Step Function
Modify the MyStateMachine.json file to use the ARNs of the created Lambda functions.

### 4. Configuring the Streamlit Application
Create an S3 bucket and note its ARN. Update the environment variables in streamlit/env.

```
KEY_API_QDRANT=<your_qdrant_api_key>
URL_QDRANT=<your_qdrant_url>
OPENAI_KEY=<your_openai_key>
STEP_FUNCTION_ARN=<your_step_function_arn>
S3_BUCKET=<your_s3_bucket_name>
```
### 5. Running the Streamlit Application
Build and run the Docker container for the Streamlit application.
```
cd streamlit
docker build -t streamlit-app .
docker run -p 8501:8501 --env-file env streamlit-app
```
Access the application at http://localhost:8501.

### Project Structure
```
├── functions_lambda
│   ├── aggregate
│   │   ├── Dockerfile
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   ├── Extract-images
│   │   ├── Dockerfile
│   │   └── lambda_function.py
│   ├── extract-text-tables
│   │   ├── Dockerfile
│   │   └── lambda_function.py
│   ├── summarize-image
│   │   ├── Dockerfile
│   │   └── lambda_function.py
│   ├── summarize-table
│   │   ├── Dockerfile
│   │   └── lambda_function.py
│   └── summarize-texts
│       ├── Dockerfile
│       └── lambda_function.py
├── MyStateMachine.json
└── streamlit
    ├── app.py
    ├── Dockerfile
    ├── env
    ├── functions_helpers.py
    └── requirements.txt

```



