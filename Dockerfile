FROM public.ecr.aws/lambda/python:3.10

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip3 install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY companies_house_streaming_etl ${LAMBDA_TASK_ROOT}/companies_house_streaming_etl

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "companies_house_streaming_etl.streamer.stream.start_streaming" ]