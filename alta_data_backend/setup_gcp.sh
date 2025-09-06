#!/bin/bash

# Google Cloud Platform Setup Script for Alta Data Backend
# This script automates the GCP setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="alta-data-backend"
SERVICE_ACCOUNT_NAME="alta-data-service"
BUCKET_NAME="alta-data-backend-$(date +%s)"
LOCATION="us-central1"

echo -e "${BLUE}🚀 Setting up Google Cloud Platform for Alta Data Backend${NC}"
echo "=================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first:${NC}"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  You need to authenticate with gcloud first:${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

echo -e "${GREEN}✅ gcloud CLI is installed and authenticated${NC}"

# Create project (if it doesn't exist)
echo -e "${BLUE}📁 Creating GCP project...${NC}"
if gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo -e "${YELLOW}⚠️  Project $PROJECT_ID already exists${NC}"
else
    gcloud projects create $PROJECT_ID --name="Alta Data Backend"
    echo -e "${GREEN}✅ Project $PROJECT_ID created${NC}"
fi

# Set the project as default
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Project set as default${NC}"

# Enable required APIs
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
APIS=(
    "storage.googleapis.com"
    "documentai.googleapis.com"
    "speech.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "iam.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "Enabling $api..."
    gcloud services enable $api
done
echo -e "${GREEN}✅ All APIs enabled${NC}"

# Create service account
echo -e "${BLUE}👤 Creating service account...${NC}"
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com &> /dev/null; then
    echo -e "${YELLOW}⚠️  Service account already exists${NC}"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Alta Data Service Account" \
        --description="Service account for Alta Data Backend"
    echo -e "${GREEN}✅ Service account created${NC}"
fi

SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Assign roles to service account
echo -e "${BLUE}🔐 Assigning roles to service account...${NC}"
ROLES=(
    "roles/storage.admin"
    "roles/documentai.apiUser"
    "roles/speech.client"
)

for role in "${ROLES[@]}"; do
    echo "Assigning $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role" \
        --quiet
done
echo -e "${GREEN}✅ Roles assigned${NC}"

# Create and download service account key
echo -e "${BLUE}🔑 Creating service account key...${NC}"
if [ -f "service-account.json" ]; then
    echo -e "${YELLOW}⚠️  service-account.json already exists. Backing up...${NC}"
    mv service-account.json service-account.json.backup
fi

gcloud iam service-accounts keys create ./service-account.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

echo -e "${GREEN}✅ Service account key created${NC}"

# Create GCS bucket
echo -e "${BLUE}🪣 Creating GCS bucket...${NC}"
gsutil mb -l $LOCATION gs://$BUCKET_NAME
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:objectAdmin gs://$BUCKET_NAME
echo -e "${GREEN}✅ Bucket created: gs://$BUCKET_NAME${NC}"

# Create Document AI processor
echo -e "${BLUE}📄 Creating Document AI processor...${NC}"
PROCESSOR_ID=$(gcloud documentai processors create \
    --location=$LOCATION \
    --display-name="Alta Data OCR Processor" \
    --type=OCR_PROCESSOR \
    --format="value(name)" | sed 's/.*\///')

echo -e "${GREEN}✅ Document AI processor created: $PROCESSOR_ID${NC}"

# Create .env file with configuration
echo -e "${BLUE}📝 Creating .env file...${NC}"
cat > .env << EOF
# Application Configuration
APP_ENV=development
APP_NAME=alta_data
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALG=HS256

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=alta_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# RabbitMQ Configuration
RABBITMQ_URL=amqp://guest:guest@localhost:5672//
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# Outbox Pattern Configuration
OUTBOX_BATCH_SIZE=100
OUTBOX_PROCESSING_INTERVAL=5
OUTBOX_MAX_RETRIES=3
OUTBOX_RETRY_DELAY=60

# Email Configuration
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=no-reply@altadata.local

# Google Cloud Configuration
GCS_PROJECT_ID=$PROJECT_ID
GCS_BUCKET_NAME=$BUCKET_NAME
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Document AI Configuration
DOCUMENT_AI_PROCESSOR_ID=$PROCESSOR_ID
DOCUMENT_AI_LOCATION=$LOCATION

# WebAuthn Configuration
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=Alta Data

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Rate Limiting Configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_URL=redis://localhost:6379/1

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

echo -e "${GREEN}✅ .env file created${NC}"

# Create test script
echo -e "${BLUE}🧪 Creating test script...${NC}"
cat > test_gcp_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test script to verify GCP setup"""

import os
import sys
from google.cloud import storage, documentai, speech

def test_storage():
    """Test GCS connection"""
    try:
        client = storage.Client()
        buckets = list(client.list_buckets())
        print(f"✅ GCS: Found {len(buckets)} buckets")
        return True
    except Exception as e:
        print(f"❌ GCS Error: {e}")
        return False

def test_document_ai():
    """Test Document AI connection"""
    try:
        client = documentai.DocumentProcessorServiceClient()
        print("✅ Document AI: Client created successfully")
        return True
    except Exception as e:
        print(f"❌ Document AI Error: {e}")
        return False

def test_speech_to_text():
    """Test Speech-to-Text connection"""
    try:
        client = speech.SpeechClient()
        print("✅ Speech-to-Text: Client created successfully")
        return True
    except Exception as e:
        print(f"❌ Speech-to-Text Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Google Cloud Platform setup...")
    print("-" * 40)
    
    storage_ok = test_storage()
    doc_ai_ok = test_document_ai()
    speech_ok = test_speech_to_text()
    
    print("-" * 40)
    if all([storage_ok, doc_ai_ok, speech_ok]):
        print("🎉 All services are configured correctly!")
        sys.exit(0)
    else:
        print("⚠️  Some services need attention. Check the errors above.")
        sys.exit(1)
EOF

chmod +x test_gcp_setup.py
echo -e "${GREEN}✅ Test script created${NC}"

# Summary
echo ""
echo -e "${GREEN}🎉 Google Cloud Platform setup completed successfully!${NC}"
echo "=================================================="
echo -e "${BLUE}📋 Summary:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "  Bucket: gs://$BUCKET_NAME"
echo "  Document AI Processor: $PROCESSOR_ID"
echo "  Location: $LOCATION"
echo ""
echo -e "${BLUE}📁 Files created:${NC}"
echo "  - service-account.json (service account key)"
echo "  - .env (environment configuration)"
echo "  - test_gcp_setup.py (test script)"
echo ""
echo -e "${BLUE}🧪 Next steps:${NC}"
echo "  1. Install Python dependencies: pip install -r requirements.txt"
echo "  2. Test the setup: python test_gcp_setup.py"
echo "  3. Start the application: ./start.sh"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "  - Never commit service-account.json to version control"
echo "  - Add service-account.json to .gitignore"
echo "  - Keep your service account key secure"
echo ""
echo -e "${GREEN}✅ Setup complete! Your Alta Data Backend is ready to use Google Cloud services.${NC}"
