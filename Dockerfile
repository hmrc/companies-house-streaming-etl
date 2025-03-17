FROM public.ecr.aws/lambda/python:3.10

RUN curl -O https://lambda-insights-extension.s3-eu-west-2.amazonaws.com/amazon_linux/lambda-insights-extension.rpm && \
    rpm -U lambda-insights-extension.rpm && \
    rm -f lambda-insights-extension.rpm

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY companies_house_streaming_etl ${LAMBDA_TASK_ROOT}/companies_house_streaming_etl

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "companies_house_streaming_etl.streamer.stream.start_streaming" ]
