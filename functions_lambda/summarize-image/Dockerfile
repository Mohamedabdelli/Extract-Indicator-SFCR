FROM public.ecr.aws/lambda/python:3.10

RUN pip install boto3 openai Pillow

COPY lambda_function.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_function.lambda_handler"]
