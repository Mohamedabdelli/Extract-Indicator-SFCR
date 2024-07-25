FROM public.ecr.aws/lambda/python:3.10

RUN pip install boto3 langchain langchain-openai openai

COPY lambda_function.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_function.lambda_handler"]