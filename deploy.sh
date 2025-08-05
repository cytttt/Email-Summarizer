#!/bin/bash

# Configuration
PROJECT_ID="mail-summary-468010"
SERVICE_NAME="email-summarizer"
REGION="asia-east1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"


# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "Error: gcloud CLI is not installed"
    exit 1
fi

# Set project
gcloud config set project ${PROJECT_ID}

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com

# Build and push Docker image
gcloud builds submit --tag ${IMAGE_NAME}

if [ $? -ne 0 ]; then
    echo -e "$Error: Docker build failed"
    exit 1
fi

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 1 \
    --min-instances 0 \
    --concurrency 1 \
    --set-env-vars MODEL_NAME=z-ai/glm-4.5-air:free,MAX_EMAILS=10,GCS_BUCKET_NAME=${PROJECT_ID}-email-agent,GOOGLE_TOKEN_PATH=token.json \
    --set-secrets OPENROUTER_API_KEY=openrouter-api-key:latest,DISCORD_WEBHOOK_URL=discord-webhook:latest

if [ $? -ne 0 ]; then
    echo -e "Error: Cloud Run deployment failed"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')
echo -e "Service URL: ${SERVICE_URL}"

# Create Cloud Scheduler job
gcloud scheduler jobs create http email-summarizer-cron \
    --schedule="0 */6 * * *" \
    --uri="${SERVICE_URL}" \
    --http-method=POST \
    --time-zone="Asia/Taipei" \
    --location=${REGION} \
    --description="Run email summarizer every 6 hours"

if [ $? -ne 0 ]; then
    echo -e "Warning: Cloud Scheduler job creation failed or already exists"
fi