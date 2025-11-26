FROM public.ecr.aws/lambda/python:3.12

# Set working directory
WORKDIR /var/task

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code and tools
COPY agent.py .
COPY tools/ tools/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Lambda handler
CMD ["agent.lambda_handler"]
