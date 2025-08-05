#!/bin/bash

# Configuration
PROJECT_ID="mail-summary-468010"
SERVICE_NAME="email-summarizer"
REGION="asia-east1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment of Email Summarizer to Cloud Run...${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Build and push Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME}

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
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
    echo -e "${RED}Error: Cloud Run deployment failed${NC}"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')
echo -e "${GREEN}Service deployed successfully!${NC}"
echo -e "Service URL: ${SERVICE_URL}"

# Create Cloud Scheduler job
echo -e "${YELLOW}Creating Cloud Scheduler job...${NC}"
gcloud scheduler jobs create http email-summarizer-cron \
    --schedule="0 */6 * * *" \
    --uri="${SERVICE_URL}" \
    --http-method=POST \
    --time-zone="Asia/Taipei" \
    --location=${REGION} \
    --description="Run email summarizer every 6 hours"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Cloud Scheduler job created successfully!${NC}"
    echo -e "Schedule: Every 6 hours (0 */6 * * *)"
else
    echo -e "${YELLOW}Warning: Cloud Scheduler job creation failed or already exists${NC}"
fi

echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Create secrets in Secret Manager:"
echo -e "   - openrouter-api-key"
echo -e "   - discord-webhook"
echo -e "2. Update cloudrun.yaml with your project ID"
echo -e "3. Upload Gmail credentials to GCS bucket"
echo -e "4. Test the service manually before enabling the scheduler"