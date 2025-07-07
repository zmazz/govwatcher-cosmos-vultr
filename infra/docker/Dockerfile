# Multi-stage Dockerfile for Cosmos Gov-Watcher SaaS
# Builds a single container image for all 4 uAgents deployed as separate Lambda functions

# Stage 1: Builder - Install dependencies and compile packages
FROM public.ecr.aws/lambda/python:3.11 AS builder

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install build dependencies
RUN yum update -y && \
    yum install -y gcc g++ make && \
    yum clean all

# Install Python dependencies to a temporary location
RUN pip install --no-cache-dir --target /app/dependencies -r requirements.txt

# Stage 2: Runtime - Create final lightweight image
FROM public.ecr.aws/lambda/python:3.11

# Set environment variables for Lambda
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Copy installed dependencies from builder stage
COPY --from=builder /app/dependencies ${LAMBDA_TASK_ROOT}

# Copy application source code
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Set proper permissions for Lambda execution
RUN chmod 755 ${LAMBDA_TASK_ROOT}/handler.py

# Add a health check script (optional, for local testing)
RUN echo '#!/bin/bash\npython3 -c "import src.agents.subscription_agent; print(\"Health check passed\")"' > /tmp/health_check.sh && \
    chmod +x /tmp/health_check.sh

# Metadata labels
LABEL maintainer="GovWatcher Team"
LABEL version="1.0.0"
LABEL description="Cosmos Governance Watcher SaaS - Multi-Agent System"
LABEL agents="SubscriptionAgent,WatcherAgent,AnalysisAgent,MailAgent"

# Lambda handler configuration
# This will be overridden by the specific Lambda function configuration
CMD ["handler.subscription_handler"] 