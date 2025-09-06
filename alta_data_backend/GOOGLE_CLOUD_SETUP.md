# Google Cloud Platform Setup Guide

This guide will walk you through setting up Google Cloud Storage, Document AI, and Speech-to-Text services for the Alta Data Backend.

## 🎯 Prerequisites

- Google Cloud Platform account
- Billing enabled on your GCP project
- `gcloud` CLI installed and configured
- Basic understanding of GCP services

## 📋 Step-by-Step Setup

### **1. Create a Google Cloud Project**

```bash
# Create a new project
gcloud projects create alta-data-backend --name="Alta Data Backend"

# Set the project as default
gcloud config set project alta-data-backend

# Enable billing (required for AI services)
# Note: You'll need to do this through the GCP Console
```

**Alternative: Use GCP Console**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `alta-data-backend`
4. Click "Create"

### **2. Enable Required APIs**

```bash
# Enable all required APIs
gcloud services enable storage.googleapis.com
gcloud services enable documentai.googleapis.com
gcloud services enable speech.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable iam.googleapis.com
```

**Alternative: Use GCP Console**
1. Go to "APIs & Services" → "Library"
2. Search and enable each service:
   - Cloud Storage API
   - Document AI API
   - Cloud Speech-to-Text API
   - Cloud Resource Manager API
   - Identity and Access Management (IAM) API

### **3. Create a Service Account**

```bash
# Create service account
"gcloud iam service-accounts create alta-data-service \
    --display-name="Alta Data Service Account" \
    --description="Service account for Alta Data Backend""

# Get the service account email
SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:Alta Data Service Account" \
    --format="value(email)")

echo "Service Account Email: $SERVICE_ACCOUNT_EMAIL"

Service Account Email: alta-data-service@alta-data-backend.iam.gserviceaccount.com
```

### **4. Assign Required Roles**

```bash
# Assign roles to the service account
gcloud projects add-iam-policy-binding alta-data-backend \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding alta-data-backend \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/documentai.apiUser"

gcloud projects add-iam-policy-binding alta-data-backend \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/speech.client"
```

**Alternative: Use GCP Console**
1. Go to "IAM & Admin" → "IAM"
2. Find your service account
3. Click "Edit" (pencil icon)
4. Add these roles:
   - Storage Admin
   - Document AI API User
   - Cloud Speech-to-Text Client

### **5. Create and Download Service Account Key**

```bash
# Create and download the key
gcloud iam service-accounts keys create ./service-account.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# Verify the key was created
ls -la service-account.json
```

**Alternative: Use GCP Console**
1. Go to "IAM & Admin" → "Service Accounts"
2. Click on your service account
3. Go to "Keys" tab
4. Click "Add Key" → "Create new key"
5. Choose "JSON" format
6. Download the key file

### **6. Create Google Cloud Storage Bucket**

```bash
# Create a bucket (bucket names must be globally unique)
BUCKET_NAME="alta-data-backend-$(date +%s)"
gsutil mb gs://$BUCKET_NAME

# Set bucket permissions
gsutil iam ch serviceAccount:$SERVICE_ACCOUNT_EMAIL:objectAdmin gs://$BUCKET_NAME

echo "Bucket created: gs://$BUCKET_NAME"
```

**Alternative: Use GCP Console**
1. Go to "Cloud Storage" → "Buckets"
2. Click "Create bucket"
3. Enter a unique bucket name
4. Choose location type and region
5. Click "Create"

### **7. Set Up Document AI Processor**

#### **Option A: Using gcloud CLI**

```bash
# Create a Document AI processor
gcloud documentai processors create \
    --location=us \
    --display-name="Alta Data OCR Processor" \
    --type=OCR_PROCESSOR

# List processors to get the processor ID
gcloud documentai processors list --location=us
```

#### **Option B: Using GCP Console**

1. Go to [Document AI Console](https://console.cloud.google.com/ai/document-ai)
2. Click "Create Processor"
3. Choose "Document OCR" processor type
4. Enter processor name: "Alta Data OCR Processor"
5. Select region: "us-central1" (or your preferred region)
6. Click "Create"
7. Copy the Processor ID from the processor details page

### **8. Configure Environment Variables**

Update your `.env` file with the following values:

```bash
# Google Cloud Configuration
GCS_PROJECT_ID=alta-data-backend
GCS_BUCKET_NAME=your-bucket-name-here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Document AI Configuration
DOCUMENT_AI_PROCESSOR_ID=your-processor-id-here
DOCUMENT_AI_LOCATION=us
```

### **9. Test the Setup**

Create a test script to verify everything is working:

```python
# test_gcp_setup.py
import os
from google.cloud import storage, documentai, speech

# Set the path to your service account key
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './service-account.json'

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
    else:
        print("⚠️  Some services need attention. Check the errors above.")
```

Run the test:
```bash
python test_gcp_setup.py
```

## 🔧 Configuration Details

### **Service Account Permissions**

The service account needs these specific permissions:

| Service | Required Role | Purpose |
|---------|---------------|---------|
| Cloud Storage | `roles/storage.admin` | Upload/download files, manage bucket permissions |
| Document AI | `roles/documentai.apiUser` | Process documents for OCR |
| Speech-to-Text | `roles/speech.client` | Transcribe audio files |

### **Bucket Configuration**

Recommended bucket settings:

```bash
# Set lifecycle policy for cost optimization
gsutil lifecycle set lifecycle.json gs://your-bucket-name

# lifecycle.json content:
{
  "rule": [
    {
      "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 30}
    },
    {
      "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
      "condition": {"age": 90}
    }
  ]
}
```

### **Document AI Processor Types**

Choose the right processor type for your use case:

| Processor Type | Use Case | Supported Formats |
|----------------|----------|-------------------|
| `OCR_PROCESSOR` | General text extraction | PDF, PNG, JPEG, TIFF |
| `FORM_PARSER_PROCESSOR` | Form data extraction | PDF forms |
| `INVOICE_PROCESSOR` | Invoice processing | PDF invoices |
| `RECEIPT_PROCESSOR` | Receipt processing | Receipt images |

### **Speech-to-Text Configuration**

Supported audio formats and configurations:

| Format | Encoding | Sample Rate | Max Duration |
|--------|----------|-------------|--------------|
| WAV | LINEAR16 | 8kHz-48kHz | 60 minutes |
| FLAC | FLAC | 8kHz-48kHz | 60 minutes |
| MP3 | MP3 | 8kHz-48kHz | 60 minutes |
| OGG | OGG_OPUS | 8kHz-48kHz | 60 minutes |

## 💰 Cost Optimization

### **Storage Costs**
- Use lifecycle policies to move old files to cheaper storage classes
- Consider using Cloud Storage Transfer Service for large migrations
- Monitor usage with Cloud Monitoring

### **AI Service Costs**
- Document AI: $1.50 per 1,000 pages
- Speech-to-Text: $0.006 per 15 seconds of audio
- Use batch processing to reduce API calls

### **Monitoring Setup**

```bash
# Enable monitoring
gcloud services enable monitoring.googleapis.com

# Create alerting policy for costs
gcloud alpha monitoring policies create --policy-from-file=alert-policy.yaml
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Authentication Errors**
   ```bash
   # Verify service account key
   gcloud auth activate-service-account --key-file=service-account.json
   gcloud auth list
   ```

2. **Permission Denied**
   ```bash
   # Check IAM roles
   gcloud projects get-iam-policy alta-data-backend
   ```

3. **API Not Enabled**
   ```bash
   # List enabled APIs
   gcloud services list --enabled
   
   # Enable specific API
   gcloud services enable documentai.googleapis.com
   ```

4. **Bucket Access Issues**
   ```bash
   # Test bucket access
   gsutil ls gs://your-bucket-name
   
   # Check bucket permissions
   gsutil iam get gs://your-bucket-name
   ```

### **Debug Mode**

Enable debug logging in your application:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Set environment variable for detailed logs
os.environ['GOOGLE_CLOUD_LOG_LEVEL'] = 'DEBUG'
```

## 📚 Additional Resources

- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Document AI Documentation](https://cloud.google.com/document-ai/docs)
- [Speech-to-Text Documentation](https://cloud.google.com/speech-to-text/docs)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/service-accounts)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator)

## 🔐 Security Best Practices

1. **Never commit service account keys to version control**
2. **Use least privilege principle for IAM roles**
3. **Enable audit logging for all services**
4. **Regularly rotate service account keys**
5. **Use VPC Service Controls for additional security**

---

**Your Google Cloud Platform setup is now complete!** 🎉

The Alta Data Backend can now:
- ✅ Store files in Google Cloud Storage
- ✅ Process documents with Document AI OCR
- ✅ Transcribe audio with Speech-to-Text
- ✅ Handle all operations securely with service accounts
